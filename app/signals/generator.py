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
    """Core Signal Generation and Alert Pipeline."""

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
        Executes end-to-end signal analysis pipeline using current active strategy.
        """
        current_strategy = active_strategy_store.get_strategy()
        strategy_engine = StrategyEngine(current_strategy)

        timeframes = current_strategy.timeframes
        entry_tf = timeframes.get("entry", "5m")
        session_name = get_utc_trading_session()

        # Fetch Data
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, timeframes)
        entry_df = tf_dfs.get(entry_tf)

        if entry_df is None or entry_df.empty:
            return None

        # 1. HARD-BLOCK GUARD: Check for synthetic data source in active evaluation window
        has_synthetic = False
        for tf, df in tf_dfs.items():
            if "source" in df.columns and any(df["source"].astype(str).str.lower().isin(["synthetic", "mock"])):
                has_synthetic = True
                break

        if has_synthetic and not force_generate:
            await log_execution_event("DATA_GUARD_BLOCK", f"Signal generation blocked: synthetic data present in {symbol} candles", {"symbol": symbol})
            await _persist_signal_log(
                alert_id=f"guard_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
                direction="NONE",
                entry_price=float(entry_df["close"].iloc[-1]),
                sl=0.0, tp1=0.0, tp2=0.0, rr=0.0, lots=0.0,
                confidence_score=0,
                status="SUPPRESSED_SYNTHETIC",
                session=session_name,
                confirmations=["insufficient live data — signal suppressed"]
            )
            return None

        # 2. Blackout window filter
        is_blackout, blackout_reason = is_blackout_active()
        if is_blackout and not force_generate:
            await log_execution_event("BLACKOUT_SUPPRESSED", f"Signal suppressed due to blackout: {blackout_reason}", {"symbol": symbol})
            return None

        # Build Active Chart Context Metadata with ADX & Regime
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

        # Evaluate Strategy
        eval_result = strategy_engine.evaluate(tf_dfs)
        direction = eval_result.direction
        confidence_score = eval_result.confidence_score

        # Calculate Risk Plan
        risk_plan = self.risk_manager.calculate_trade_plan(
            symbol=symbol,
            direction=direction,
            current_df=entry_df,
            target_rr=current_strategy.risk_reward_ratio,
            sl_method=current_strategy.sl_method
        )

        # Log evaluation cycle (including Near Misses and No Trade)
        eval_status = "CONFIRMED" if eval_result.is_valid_setup else ("NEAR_MISS" if confidence_score >= 60 else "NO_TRADE")
        confirmations = [f"✓ {r.description}" for r in eval_result.rule_results if r.passed]

        eval_alert_id = deduplicator.generate_alert_id(symbol, entry_tf, direction, last_ts)
        await _persist_signal_log(
            alert_id=eval_alert_id,
            symbol=symbol,
            direction=direction,
            entry_price=risk_plan.entry_price,
            sl=risk_plan.stop_loss,
            tp1=risk_plan.take_profit_1,
            tp2=risk_plan.take_profit_2,
            rr=risk_plan.risk_reward_ratio,
            lots=risk_plan.position_size_lots,
            confidence_score=confidence_score,
            status=eval_status,
            session=session_name,
            confirmations=confirmations
        )

        if not eval_result.is_valid_setup and not force_generate:
            return None

        # Check Deduplication
        alert_id = eval_alert_id
        if deduplicator.is_duplicate(alert_id) and not force_generate:
            return None

        # Generate AI Summary Explanation
        explanation = generate_signal_explanation(
            symbol=symbol,
            direction=direction,
            entry=risk_plan.entry_price,
            sl=risk_plan.stop_loss,
            tp=risk_plan.take_profit_2,
            confidence=eval_result.confidence_score,
            trend=eval_result.higher_tf_trend,
            confirmations=confirmations
        )

        payload = SignalPayload(
            alert_id=alert_id,
            symbol=symbol,
            direction=direction,
            entry_price=risk_plan.entry_price,
            stop_loss=risk_plan.stop_loss,
            take_profit_1=risk_plan.take_profit_1,
            take_profit_2=risk_plan.take_profit_2,
            risk_reward_ratio=risk_plan.risk_reward_ratio,
            position_size_lots=risk_plan.position_size_lots,
            confidence_score=confidence_score,
            timeframe=entry_tf,
            higher_tf_trend=eval_result.higher_tf_trend,
            status=SignalStatus.CONFIRMED,
            confirmations=confirmations,
            created_at=datetime.now(timezone.utc).isoformat(),
            chart_info=chart_info.model_dump(),
            ai_explanation=explanation
        )

        deduplicator.register_alert(alert_id)

        # Final Stage Pipeline Execution & State Machine Transition
        try:
            from app.signals.state_machine import state_machine
            from app.execution.manager import execution_manager
            state_machine.register_signal(payload)
            await execution_manager.execute_signal(payload)
        except Exception:
            pass

        return payload

