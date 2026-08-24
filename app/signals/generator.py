from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.data.historical import candle_buffer
from app.data.chart_info import build_chart_info, ActiveChartInfo
from app.strategy.engine import StrategyEngine
from app.strategy.schemas import StrategyDefinition
from app.risk.manager import RiskManager
from app.signals.models import SignalPayload, SignalStatus
from app.signals.deduplicator import deduplicator
from app.ai.explanation import generate_signal_explanation
from app.config import settings

from app.strategy.active_store import active_strategy_store
from app.data.provider import log_execution_event
from app.risk.limits import get_utc_trading_session, is_blackout_active
from app.indicators.trend import evaluate_adx_gate
from app.ai.omni_engine import omni_engine
from app.ai.preferences import omni_preferences_store
import uuid
import json

async def _persist_signal_log(
    alert_id: str,
    symbol: str,
    direction: str,
    entry_price: float,
    sl: float,
    tp1: float,
    tp2: float,
    rr: float,
    lots: float,
    confidence_score: int,
    status: str,
    session: str,
    confirmations: list
):
    try:
        from app.database.connection import AsyncSessionLocal
        from app.database.models import DBSignalLog
        async with AsyncSessionLocal() as session_db:
            db_log = DBSignalLog(
                alert_id=alert_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=sl,
                take_profit_1=tp1,
                take_profit_2=tp2,
                risk_reward_ratio=rr,
                position_size_lots=lots,
                confidence_score=confidence_score,
                status=status,
                session=session,
                confirmations_json=json.dumps(confirmations)
            )
            session_db.add(db_log)
            await session_db.commit()
    except Exception:
        pass

class SignalGenerator:
    """Core Signal Generation and Alert Pipeline powered by Omni AI Engine."""

    def __init__(
        self,
        strategy: Optional[StrategyDefinition] = None,
        account_balance: float = 10000.0,
        risk_percent: float = 1.0
    ):
        self.risk_manager = RiskManager(account_balance=account_balance, risk_percent=risk_percent)

    async def analyze_and_generate_signal(
        self,
        symbol: str = "XAU/USD",
        force_generate: bool = False
    ) -> Optional[SignalPayload]:
        """
        Executes end-to-end signal analysis pipeline using Omni AI Engine and user preferences.
        """
        current_strategy = active_strategy_store.get_strategy()
        timeframes = current_strategy.timeframes
        entry_tf = timeframes.get("entry", "5m")
        session_name = get_utc_trading_session()

        # Fetch Data
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, timeframes)
        entry_df = tf_dfs.get(entry_tf)

        if entry_df is None or entry_df.empty:
            return None

        # 1. HARD-BLOCK GUARD: Check for synthetic data source
        has_synthetic = False
        for tf, df in tf_dfs.items():
            if "source" in df.columns and any(df["source"].astype(str).str.lower().isin(["synthetic", "mock"])):
                has_synthetic = True
                break

        if has_synthetic and not force_generate:
            await log_execution_event("DATA_GUARD_BLOCK", f"Signal generation blocked: synthetic data present in {symbol} candles", {"symbol": symbol})
            return None

        # 2. Blackout window filter
        is_blackout, blackout_reason = is_blackout_active()
        if is_blackout and not force_generate:
            await log_execution_event("BLACKOUT_SUPPRESSED", f"Signal suppressed due to blackout: {blackout_reason}", {"symbol": symbol})
            return None

        # Build Active Chart Context Metadata
        trend_1h_df = tf_dfs.get("1h", entry_df)
        adx_val, regime, _ = evaluate_adx_gate(trend_1h_df)
        last_price = float(entry_df["close"].iloc[-1])
        last_ts = str(entry_df["timestamp"].iloc[-1])

        chart_info = build_chart_info(
            symbol=symbol,
            provider=settings.default_data_provider,
            timeframes=timeframes,
            last_price=last_price,
            candle_count=len(entry_df),
            adx_1h=adx_val,
            regime=regime
        )

        # 3. Generate Multi-Timeframe Forecast via Omni AI Engine
        omni_forecast = await omni_engine.generate_future_trade_forecast(symbol, entry_tf, tf_dfs)
        user_prefs = omni_preferences_store.get_preferences()

        direction = omni_forecast.primary_direction
        if direction not in ["BUY", "SELL"]:
            if force_generate:
                # Default to trend direction on forced manual scan if ranging
                direction = "BUY" if last_price >= omni_forecast.entry_market_price else "SELL"
            else:
                return None

        confidence_score = omni_forecast.win_probability_percent

        # Confirmations
        confirmations = [f"✓ {d}" for d in omni_forecast.institutional_drivers]
        if omni_forecast.session_sweep_bias != "neutral":
            confirmations.append(f"✓ Session Liquidity Sweep ({omni_forecast.session_sweep_bias.replace('_', ' ').title()})")

        eval_status = "CONFIRMED" if confidence_score >= user_prefs.min_confidence_score else "NEAR_MISS"
        eval_alert_id = deduplicator.generate_alert_id(symbol, entry_tf, direction, last_ts)

        await _persist_signal_log(
            alert_id=eval_alert_id,
            symbol=symbol,
            direction=direction,
            entry_price=omni_forecast.entry_zone["ideal"],
            sl=omni_forecast.stop_loss,
            tp1=omni_forecast.take_profit_1,
            tp2=omni_forecast.take_profit_2,
            rr=omni_forecast.risk_reward_ratio,
            lots=user_prefs.preferred_lot_size,
            confidence_score=confidence_score,
            status=eval_status,
            session=session_name,
            confirmations=confirmations
        )

        if confidence_score < user_prefs.min_confidence_score and not force_generate:
            return None

        alert_id = eval_alert_id
        if deduplicator.is_duplicate(alert_id) and not force_generate:
            return None

        # AI Summary Explanation
        explanation = generate_signal_explanation(
            symbol=symbol,
            direction=direction,
            entry=omni_forecast.entry_zone["ideal"],
            sl=omni_forecast.stop_loss,
            tp=omni_forecast.take_profit_2,
            confidence=confidence_score,
            trend=omni_forecast.market_regime,
            confirmations=confirmations
        )

        payload = SignalPayload(
            alert_id=alert_id,
            symbol=symbol,
            direction=direction,
            entry_price=omni_forecast.entry_zone["ideal"],
            entry_market_price=omni_forecast.entry_market_price,
            entry_limit_price=omni_forecast.entry_limit_price,
            entry_reachability_percent=omni_forecast.entry_reachability_percent,
            entry_reachability_state=omni_forecast.entry_reachability_state,
            entry_distance_pips=omni_forecast.entry_distance_pips,
            stop_loss=omni_forecast.stop_loss,
            take_profit_1=omni_forecast.take_profit_1,
            take_profit_2=omni_forecast.take_profit_2,
            take_profit_3=omni_forecast.take_profit_3,
            risk_reward_ratio=omni_forecast.risk_reward_ratio,
            min_profit_pips=user_prefs.min_profit_pips,
            expected_profit_pips=omni_forecast.expected_profit_pips,
            expected_profit_usd=omni_forecast.expected_profit_usd,
            position_size_lots=user_prefs.preferred_lot_size,
            confidence_score=confidence_score,
            timeframe=entry_tf,
            higher_tf_trend=omni_forecast.market_regime,
            status=SignalStatus.CONFIRMED,
            confirmations=confirmations,
            created_at=datetime.now(timezone.utc).isoformat(),
            chart_info=chart_info.model_dump(),
            ai_explanation=explanation
        )

        deduplicator.register_alert(alert_id)

        # Execution & state machine trigger
        try:
            from app.signals.state_machine import state_machine
            from app.execution.manager import execution_manager
            state_machine.register_signal(payload)
            await execution_manager.execute_signal(payload)
        except Exception:
            pass

        return payload

signal_generator = SignalGenerator()
