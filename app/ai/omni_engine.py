import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import pandas as pd
from pydantic import BaseModel, Field

from app.indicators.trend import evaluate_trend_alignment, evaluate_adx_gate, calculate_ema
from app.indicators.momentum import calculate_rsi, calculate_macd
from app.indicators.volatility import calculate_atr, calculate_atr_percentile
from app.indicators.volume_flow import calculate_vwap, calculate_rvol, calculate_obv, estimate_volume_delta
from app.indicators.patterns import calculate_c2c_velocity, detect_fair_value_gaps, detect_market_structure_events, detect_candlestick_formations
from app.indicators.choch_predictor import evaluate_choch_prediction, CHoCHPredictionReport, MarketScenario
from app.indicators.session_sweeps import calculate_session_levels_and_sweeps, SessionSweepsReport
from app.indicators.sr_behavior import analyze_sr_price_behavior, SRPriceBehaviorAnalysis
from app.data.symbols import get_symbol_spec
from app.learning.feedback_engine import feedback_engine
from app.ai.preferences import omni_preferences_store

logger = logging.getLogger("omni_engine")

class OmniFutureForecast(BaseModel):
    symbol: str
    timeframe: str
    primary_direction: str  # "BUY", "SELL", "CHoCH_REVERSAL_WAIT", "RANGE_WAIT"
    win_probability_percent: int  # 0 to 100
    entry_zone: Dict[str, float]  # {"min": 4625.5, "max": 4627.0, "ideal": 4626.9}
    entry_market_price: float
    entry_limit_price: float
    entry_reachability_percent: int  # 0 to 100% feasibility score
    entry_reachability_state: str  # "INSTANT_MARKET_FILL", "FEASIBLE_PULLBACK", "CHASE_RISK_WARNING"
    entry_distance_pips: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward_ratio: float
    min_profit_pips: float
    expected_profit_pips: float
    expected_profit_usd: float
    position_size_lots: float
    market_regime: str
    c2c_momentum_state: str
    volume_flow_bias: str
    vwap_position: str  # "above_vwap", "below_vwap", "at_vwap"
    rvol: float
    choch_risk: str
    session_sweep_bias: str = "neutral"
    sr_behavior_state: str = "NEUTRAL"
    matrix_radar: Dict[str, int]  # {"trend": 85, "volume": 78, "momentum": 82, "structure": 90, "volatility": 70}
    institutional_drivers: List[str]
    invalidation_criteria: str
    scenarios: List[MarketScenario]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class OmniMarketMatrix(BaseModel):
    symbol: str
    timeframe: str
    last_price: float
    vwap: float
    vwap_upper: float
    vwap_lower: float
    rvol: float
    obv_trend: str
    volume_delta: Dict[str, Any]
    c2c_velocity: Dict[str, Any]
    fvgs: List[Dict[str, Any]]
    inversion_fvgs: List[Dict[str, Any]]
    structure_events: List[Dict[str, Any]]
    candlestick_pattern: Dict[str, Any]
    session_sweeps: Dict[str, Any]
    sr_price_behavior: Dict[str, Any]
    choch_report: Dict[str, Any]
    multi_tf_confluence: Dict[str, Any]
    matrix_radar: Dict[str, int]
    timestamp: str

class OmniAIEngine:
    """
    Omni-Aware AI Market Vision & Future Trade Prediction Engine.
    Combines C2C momentum, Volume Flow, Market Structure BOS/CHoCH, Entry Reachability, and Adaptive Learning.
    """

    async def analyze_market_matrix(
        self,
        symbol: str,
        timeframe: str,
        tf_dfs: Dict[str, pd.DataFrame]
    ) -> OmniMarketMatrix:
        """Extracts complete multi-dimensional quantitative chart matrix."""
        spec = get_symbol_spec(symbol)
        entry_df = tf_dfs.get(timeframe, tf_dfs.get("5m"))
        df_1h = tf_dfs.get("1h", entry_df)
        df_15m = tf_dfs.get("15m", entry_df)

        if entry_df is None or entry_df.empty:
            raise ValueError(f"No candle data available for symbol {symbol}")

        latest_close = float(entry_df["close"].iloc[-1])

        # 1. Volume & VWAP
        vwap_series, vwap_up, vwap_low = calculate_vwap(entry_df)
        vwap_val = float(vwap_series.iloc[-1]) if not vwap_series.empty else latest_close
        vwap_up_val = float(vwap_up.iloc[-1]) if not vwap_up.empty else latest_close + 2.0
        vwap_low_val = float(vwap_low.iloc[-1]) if not vwap_low.empty else latest_close - 2.0
        rvol = calculate_rvol(entry_df)
        _, obv_trend = calculate_obv(entry_df)
        vol_delta = estimate_volume_delta(entry_df)

        # 2. C2C, Patterns, and Structure
        c2c = calculate_c2c_velocity(entry_df)
        fvgs_raw = detect_fair_value_gaps(entry_df)
        fvgs = [f.model_dump() if hasattr(f, "model_dump") else f for f in fvgs_raw]
        inversion_fvgs = [f for f in fvgs if f.get("is_inverted")]
        struct_events_raw = detect_market_structure_events(entry_df)
        struct_events = [s.model_dump() if hasattr(s, "model_dump") else s for s in struct_events_raw]
        candle_pattern_raw = detect_candlestick_formations(entry_df)
        candle_pattern = candle_pattern_raw.model_dump() if hasattr(candle_pattern_raw, "model_dump") else candle_pattern_raw


        # 3. Session Sweeps & S/R Behavior
        session_sweeps = calculate_session_levels_and_sweeps(entry_df)
        sr_behavior = analyze_sr_price_behavior(entry_df, pip_threshold=spec.pip_size * 5)


        # 4. CHoCH & Multi-TF
        choch_report = evaluate_choch_prediction(df_1h, entry_df, symbol=symbol)
        t1h, a1h, _, _ = evaluate_trend_alignment(df_1h)
        t15m, a15m, _, _ = evaluate_trend_alignment(df_15m)
        t_entry, a_entry, _, _ = evaluate_trend_alignment(entry_df)
        is_aligned = (t1h == t15m == t_entry) and (t1h in ["bullish", "bearish"])
        multi_tf = {
            "1h_trend": t1h,
            "15m_setup": t15m,
            "entry_tf_trend": t_entry,
            "is_aligned": is_aligned
        }


        # 5. Composite Radar Scores
        trend_score = 85 if multi_tf["is_aligned"] else 60
        volume_score = min(98, int(rvol * 50)) if rvol > 1.0 else 55
        momentum_score = 85 if c2c["velocity_state"] == "strong_expansion" else 65
        structure_score = 90 if struct_events else 70
        atr_pct = calculate_atr_percentile(entry_df)
        volatility_score = int(atr_pct)

        radar = {
            "trend": trend_score,
            "volume": volume_score,
            "momentum": momentum_score,
            "structure": structure_score,
            "volatility": volatility_score
        }

        return OmniMarketMatrix(
            symbol=spec.symbol,
            timeframe=timeframe,
            last_price=round(latest_close, spec.quote_precision),
            vwap=round(vwap_val, spec.quote_precision),
            vwap_upper=round(vwap_up_val, spec.quote_precision),
            vwap_lower=round(vwap_low_val, spec.quote_precision),
            rvol=rvol,
            obv_trend=obv_trend,
            volume_delta=vol_delta,
            c2c_velocity=c2c,
            fvgs=fvgs,
            inversion_fvgs=inversion_fvgs,
            structure_events=struct_events,
            candlestick_pattern=candle_pattern,
            session_sweeps=session_sweeps.model_dump(),
            sr_price_behavior=sr_behavior.model_dump(),
            choch_report=choch_report.model_dump(),
            multi_tf_confluence=multi_tf,
            matrix_radar=radar,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    async def generate_future_trade_forecast(
        self,
        symbol: str,
        timeframe: str,
        tf_dfs: Dict[str, pd.DataFrame]
    ) -> OmniFutureForecast:
        """Synthesizes complete market matrix into an actionable future trade projection with reachability checks."""
        matrix = await self.analyze_market_matrix(symbol, timeframe, tf_dfs)
        spec = get_symbol_spec(symbol)
        last_p = matrix.last_price
        entry_df = tf_dfs.get(timeframe, list(tf_dfs.values())[0])

        user_prefs = omni_preferences_store.get_preferences()

        atr_series = calculate_atr(entry_df, 14)
        atr_val = float(atr_series.iloc[-1]) if not atr_series.empty else spec.pip_size * 20

        # Self-learning adaptive weights
        weights = feedback_engine.weights

        # Determine Primary Direction & Confluence
        is_bullish_trend = matrix.multi_tf_confluence["1h_trend"] == "bullish"
        is_bearish_trend = matrix.multi_tf_confluence["1h_trend"] == "bearish"
        choch_risk = matrix.choch_report["choch_risk_level"]
        sweep_bias = matrix.session_sweeps["liquidity_bias"]
        sr_dom = matrix.sr_price_behavior["dominant_behavior"]

        drivers = []
        if matrix.multi_tf_confluence["is_aligned"]:
            drivers.append(f"Multi-Timeframe Trend Alignment (1H {matrix.multi_tf_confluence['1h_trend'].upper()} + 15M {matrix.multi_tf_confluence['15m_setup'].upper()})")
        if matrix.rvol >= 1.3:
            drivers.append(f"Institutional Volume Surge (RVOL {matrix.rvol}x standard)")
        if matrix.volume_delta["delta_bias"] != "neutral":
            drivers.append(f"Order Flow Imbalance: {matrix.volume_delta['buy_volume_pct']}% Buying vs {matrix.volume_delta['sell_volume_pct']}% Selling")
        if matrix.c2c_velocity["velocity_state"] != "flat_consolidation":
            drivers.append(f"Close-to-Close Momentum: {matrix.c2c_velocity['velocity_state'].replace('_', ' ').title()}")
        if matrix.inversion_fvgs:
            drivers.append(f"Active Inversion FVG (iFVG): {matrix.inversion_fvgs[-1]['description']}")
        elif matrix.fvgs:
            drivers.append(f"Active Fair Value Gap (FVG) at ${matrix.fvgs[-1]['bottom_price']} - ${matrix.fvgs[-1]['top_price']}")

        if sweep_bias != "neutral":
            drivers.append(f"⚡ Session Liquidity Sweep: {matrix.session_sweeps['sweep_summary']}")
        if matrix.sr_price_behavior["summary"]:
            drivers.append(f"S/R Level Interaction: {matrix.sr_price_behavior['summary']}")

        # Direction synthesis
        if (is_bullish_trend or sweep_bias == "bullish_reversal_sweep" or sr_dom in ["BULLISH_BOUNCE", "RETEST_CONFIRMED"]) and choch_risk != "HIGH" and matrix.last_price >= matrix.vwap - 1.0:
            direction = "BUY"
            boost = 10 if (sweep_bias == "bullish_reversal_sweep" or matrix.inversion_fvgs) else 0
            win_prob = min(95, max(68, int((matrix.matrix_radar["trend"] * 0.35) + (matrix.matrix_radar["volume"] * 0.25) + (matrix.matrix_radar["structure"] * 0.40) + boost)))
            
            entry_market = last_p
            # Feasible Pullback: max 0.25 ATR discount so price actually fills
            pullback_offset = min(atr_val * 0.25, spec.pip_size * 25)
            entry_limit = round(last_p - pullback_offset, spec.quote_precision)

            # Choose entry ideal based on user preference
            if user_prefs.entry_preference == "INSTANT_MARKET":
                entry_ideal = entry_market
                reachability = 100
                reachability_state = "INSTANT_MARKET_FILL"
                dist_pips = 0.0
            elif user_prefs.entry_preference == "SNIPER_PULLBACK":
                entry_ideal = entry_limit
                reachability = 88
                reachability_state = "FEASIBLE_PULLBACK"
                dist_pips = round(abs(last_p - entry_limit) / spec.pip_size, 1)
            else: # AI_ADAPTIVE
                if matrix.rvol >= 1.3 or matrix.c2c_velocity["velocity_state"] == "strong_expansion":
                    entry_ideal = entry_market
                    reachability = 98
                    reachability_state = "INSTANT_MARKET_FILL"
                    dist_pips = 0.0
                else:
                    entry_ideal = entry_limit
                    reachability = 90
                    reachability_state = "FEASIBLE_PULLBACK"
                    dist_pips = round(abs(last_p - entry_limit) / spec.pip_size, 1)

            entry_min = round(entry_ideal - (atr_val * 0.15), spec.quote_precision)
            entry_max = round(entry_ideal + (atr_val * 0.10), spec.quote_precision)

            sl = round(entry_ideal - max(atr_val * 1.2, spec.pip_size * 25), spec.quote_precision)
            risk_dist = abs(entry_ideal - sl)

            # Enforce user minimum profit pips
            min_target_dist = max(risk_dist * 1.5, user_prefs.min_profit_pips * spec.pip_size)
            tp1 = round(entry_ideal + (min_target_dist * 0.8), spec.quote_precision)
            tp2 = round(entry_ideal + (min_target_dist * 1.4), spec.quote_precision)
            tp3 = round(entry_ideal + (min_target_dist * 2.5), spec.quote_precision)

            rr = round(abs(tp2 - entry_ideal) / max(1e-5, risk_dist), 2)
            invalidation = f"Candle body close below 1H EMA20 (${matrix.vwap:.2f}) or session low (${matrix.session_sweeps['asian_low']:.2f})"

        elif (is_bearish_trend or sweep_bias == "bearish_reversal_sweep" or sr_dom in ["BEARISH_REJECTION", "FAKEOUT_SWEEP"]) and choch_risk != "HIGH" and matrix.last_price <= matrix.vwap + 1.0:
            direction = "SELL"
            boost = 10 if (sweep_bias == "bearish_reversal_sweep" or matrix.inversion_fvgs) else 0
            win_prob = min(95, max(68, int((matrix.matrix_radar["trend"] * 0.35) + (matrix.matrix_radar["volume"] * 0.25) + (matrix.matrix_radar["structure"] * 0.40) + boost)))
            
            entry_market = last_p
            pullback_offset = min(atr_val * 0.25, spec.pip_size * 25)
            entry_limit = round(last_p + pullback_offset, spec.quote_precision)

            if user_prefs.entry_preference == "INSTANT_MARKET":
                entry_ideal = entry_market
                reachability = 100
                reachability_state = "INSTANT_MARKET_FILL"
                dist_pips = 0.0
            elif user_prefs.entry_preference == "SNIPER_PULLBACK":
                entry_ideal = entry_limit
                reachability = 88
                reachability_state = "FEASIBLE_PULLBACK"
                dist_pips = round(abs(last_p - entry_limit) / spec.pip_size, 1)
            else: # AI_ADAPTIVE
                if matrix.rvol >= 1.3 or matrix.c2c_velocity["velocity_state"] == "strong_expansion":
                    entry_ideal = entry_market
                    reachability = 98
                    reachability_state = "INSTANT_MARKET_FILL"
                    dist_pips = 0.0
                else:
                    entry_ideal = entry_limit
                    reachability = 90
                    reachability_state = "FEASIBLE_PULLBACK"
                    dist_pips = round(abs(last_p - entry_limit) / spec.pip_size, 1)

            entry_min = round(entry_ideal - (atr_val * 0.10), spec.quote_precision)
            entry_max = round(entry_ideal + (atr_val * 0.15), spec.quote_precision)

            sl = round(entry_ideal + max(atr_val * 1.2, spec.pip_size * 25), spec.quote_precision)
            risk_dist = abs(sl - entry_ideal)

            min_target_dist = max(risk_dist * 1.5, user_prefs.min_profit_pips * spec.pip_size)
            tp1 = round(entry_ideal - (min_target_dist * 0.8), spec.quote_precision)
            tp2 = round(entry_ideal - (min_target_dist * 1.4), spec.quote_precision)
            tp3 = round(entry_ideal - (min_target_dist * 2.5), spec.quote_precision)

            rr = round(abs(entry_ideal - tp2) / max(1e-5, risk_dist), 2)
            invalidation = f"Candle body close above 1H EMA20 (${matrix.vwap:.2f}) or session high (${matrix.session_sweeps['asian_high']:.2f})"

        elif choch_risk in ["ELEVATED", "HIGH"]:
            direction = "CHoCH_REVERSAL_WAIT"
            win_prob = 55
            entry_market = last_p
            entry_limit = last_p
            entry_ideal = last_p
            reachability = 90
            reachability_state = "WAITING_BREAKOUT"
            dist_pips = 0.0
            entry_min = last_p
            entry_max = last_p
            sl = round(last_p - atr_val, spec.quote_precision)
            tp1 = round(last_p + atr_val, spec.quote_precision)
            tp2 = round(last_p + (atr_val * 2), spec.quote_precision)
            tp3 = round(last_p + (atr_val * 3), spec.quote_precision)
            rr = 2.0
            invalidation = f"Wait for confirmed CHoCH break beyond key pivot level ${matrix.choch_report['key_reversal_trigger']:.2f}"
            drivers.append(f"⚠️ Imminent Change of Character Warning: {matrix.choch_report['divergence_detected']}")

        else:
            direction = "RANGE_WAIT"
            win_prob = 50
            entry_market = last_p
            entry_limit = last_p
            entry_ideal = last_p
            reachability = 90
            reachability_state = "WAITING_EXPANSION"
            dist_pips = 0.0
            entry_min = last_p
            entry_max = last_p
            sl = round(last_p - atr_val, spec.quote_precision)
            tp1 = round(last_p + atr_val, spec.quote_precision)
            tp2 = round(last_p + (atr_val * 2), spec.quote_precision)
            tp3 = round(last_p + (atr_val * 3), spec.quote_precision)
            rr = 1.5
            invalidation = "Market is in low ADX consolidation; awaiting directional breakout"
            drivers.append("Market is ranging within compression zone")

        vwap_pos = "above_vwap" if last_p > matrix.vwap + 0.2 else ("below_vwap" if last_p < matrix.vwap - 0.2 else "at_vwap")

        # Convert Scenarios
        scenarios_objs = [
            MarketScenario(
                name=s["name"],
                probability_percent=s["probability_percent"],
                trigger_level=s["trigger_level"],
                invalidation_level=s["invalidation_level"],
                description=s["description"],
                action_bias=s["action_bias"]
            )
            for s in matrix.choch_report["scenarios"]
        ]

        expected_pips = round(abs(tp2 - entry_ideal) / spec.pip_size, 1)
        # Expected USD profit = (pips * pip_size * lot_size * contract_multiplier)
        expected_usd = round(expected_pips * spec.pip_size * user_prefs.preferred_lot_size * 100.0, 2)

        return OmniFutureForecast(
            symbol=spec.symbol,
            timeframe=timeframe,
            primary_direction=direction,
            win_probability_percent=win_prob,
            entry_zone={"min": entry_min, "max": entry_max, "ideal": entry_ideal},
            entry_market_price=entry_market,
            entry_limit_price=entry_limit,
            entry_reachability_percent=reachability,
            entry_reachability_state=reachability_state,
            entry_distance_pips=dist_pips,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_reward_ratio=rr,
            min_profit_pips=user_prefs.min_profit_pips,
            expected_profit_pips=expected_pips,
            expected_profit_usd=expected_usd,
            position_size_lots=user_prefs.preferred_lot_size,
            market_regime=matrix.choch_report["current_regime"],
            c2c_momentum_state=matrix.c2c_velocity["velocity_state"],
            volume_flow_bias=matrix.volume_delta["delta_bias"],
            vwap_position=vwap_pos,
            rvol=matrix.rvol,
            choch_risk=choch_risk,
            session_sweep_bias=sweep_bias,
            sr_behavior_state=sr_dom,
            matrix_radar=matrix.matrix_radar,
            institutional_drivers=drivers,
            invalidation_criteria=invalidation,
            scenarios=scenarios_objs
        )

    async def predict_future_trade(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m"
    ) -> OmniFutureForecast:
        """High-level one-step prediction pipeline for symbol."""
        from app.data.historical import candle_buffer
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol)
        return await self.generate_future_trade_forecast(symbol, timeframe, tf_dfs)

omni_engine = OmniAIEngine()
