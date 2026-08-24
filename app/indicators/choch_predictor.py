from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from pydantic import BaseModel

from app.indicators.momentum import calculate_rsi, calculate_macd
from app.indicators.trend import calculate_ema, evaluate_adx_gate
from app.indicators.structure import find_swing_points
from app.indicators.volume_flow import calculate_rvol

class MarketScenario(BaseModel):
    name: str  # "Bullish Continuation", "Bearish CHoCH Reversal", "Range / Liquidity Trap"
    probability_percent: int  # e.g., 65
    trigger_level: float
    invalidation_level: float
    description: str
    action_bias: str  # "BUY", "SELL", "WAIT"

class CHoCHPredictionReport(BaseModel):
    symbol: str
    timeframe: str
    current_regime: str  # "strong_uptrend", "exhausting_uptrend", "strong_downtrend", "exhausting_downtrend", "ranging"
    choch_risk_level: str  # "LOW", "ELEVATED", "HIGH", "CONFIRMED"
    divergence_detected: str  # "none", "bearish_rsi_div", "bullish_rsi_div", "volume_exhaustion"
    scenarios: List[MarketScenario]
    key_reversal_trigger: float
    key_continuation_trigger: float
    notes: List[str]

def evaluate_choch_prediction(
    df_1h: pd.DataFrame,
    df_5m: pd.DataFrame,
    symbol: str = "XAU/USD"
) -> CHoCHPredictionReport:
    """
    Evaluates early Change of Character (CHoCH) probability, divergences, and forward-looking market transition scenarios.
    """
    if df_5m.empty or len(df_5m) < 15:
        # Fallback empty scenario
        return CHoCHPredictionReport(
            symbol=symbol,
            timeframe="5m",
            current_regime="ranging",
            choch_risk_level="LOW",
            divergence_detected="none",
            scenarios=[
                MarketScenario(
                    name="Consolidation",
                    probability_percent=100,
                    trigger_level=0.0,
                    invalidation_level=0.0,
                    description="Insufficient data for scenario modeling",
                    action_bias="WAIT"
                )
            ],
            key_reversal_trigger=0.0,
            key_continuation_trigger=0.0,
            notes=["Awaiting real-time candle data feed."]
        )

    latest_close = float(df_5m["close"].iloc[-1])
    notes = []

    # 1. Macro Trend State on 1H
    adx_val, adx_regime, _ = evaluate_adx_gate(df_1h if not df_1h.empty else df_5m)
    ema20_1h = float(calculate_ema(df_1h, 20).iloc[-1]) if len(df_1h) >= 20 else latest_close
    ema50_1h = float(calculate_ema(df_1h, 50).iloc[-1]) if len(df_1h) >= 50 else latest_close

    is_1h_bullish = (ema20_1h > ema50_1h)
    is_1h_bearish = (ema20_1h < ema50_1h)

    # 2. Divergence Analysis (RSI Divergence on 5M)
    rsi_series = calculate_rsi(df_5m, 14)
    swing_highs, swing_lows = find_swing_points(df_5m, window=3)

    div_type = "none"
    if len(swing_highs) >= 2 and is_1h_bullish:
        # Check Bearish Divergence (Price higher high, RSI lower high)
        sh1, sh2 = swing_highs[-2], swing_highs[-1]
        idx1, idx2 = sh1["index"], sh2["index"]
        if idx1 < len(rsi_series) and idx2 < len(rsi_series):
            rsi1 = rsi_series.iloc[idx1]
            rsi2 = rsi_series.iloc[idx2]
            if sh2["price"] > sh1["price"] and rsi2 < rsi1 - 3.0:
                div_type = "bearish_rsi_div"
                notes.append(f"⚠️ Bearish RSI Divergence: Price reached higher high ({sh2['price']:.2f}) on weakening momentum ({rsi2:.1f} vs {rsi1:.1f}).")

    elif len(swing_lows) >= 2 and is_1h_bearish:
        # Check Bullish Divergence (Price lower low, RSI higher low)
        sl1, sl2 = swing_lows[-2], swing_lows[-1]
        idx1, idx2 = sl1["index"], sl2["index"]
        if idx1 < len(rsi_series) and idx2 < len(rsi_series):
            rsi1 = rsi_series.iloc[idx1]
            rsi2 = rsi_series.iloc[idx2]
            if sl2["price"] < sl1["price"] and rsi2 > rsi1 + 3.0:
                div_type = "bullish_rsi_div"
                notes.append(f"🚀 Bullish RSI Divergence: Price made lower low ({sl2['price']:.2f}) on rising momentum ({rsi2:.1f} vs {rsi1:.1f}).")

    # 3. Volume Exhaustion Check
    rvol = calculate_rvol(df_5m)
    if rvol < 0.6 and (latest_close > ema20_1h or latest_close < ema20_1h):
        if div_type == "none":
            div_type = "volume_exhaustion"
        notes.append(f"📉 Low Volume Exhaustion: RVOL is {rvol:.2f}x average — potential liquidity fade.")

    # 4. Determine Reversal Risk & Current Regime
    if is_1h_bullish:
        if div_type in ["bearish_rsi_div", "volume_exhaustion"] and adx_val > 35:
            regime = "exhausting_uptrend"
            choch_risk = "ELEVATED"
        elif adx_val < 20:
            regime = "ranging"
            choch_risk = "HIGH"
        else:
            regime = "strong_uptrend"
            choch_risk = "LOW"
    elif is_1h_bearish:
        if div_type in ["bullish_rsi_div", "volume_exhaustion"] and adx_val > 35:
            regime = "exhausting_downtrend"
            choch_risk = "ELEVATED"
        elif adx_val < 20:
            regime = "ranging"
            choch_risk = "HIGH"
        else:
            regime = "strong_downtrend"
            choch_risk = "LOW"
    else:
        regime = "ranging"
        choch_risk = "HIGH"

    # Key Levels
    key_sh = swing_highs[-1]["price"] if swing_highs else latest_close + 5.0
    key_sl = swing_lows[-1]["price"] if swing_lows else latest_close - 5.0

    # 5. Build Scenarios
    scenarios: List[MarketScenario] = []

    if is_1h_bullish:
        cont_prob = 65 if choch_risk == "LOW" else (45 if choch_risk == "ELEVATED" else 30)
        choch_prob = 20 if choch_risk == "LOW" else (40 if choch_risk == "ELEVATED" else 50)
        range_prob = 100 - (cont_prob + choch_prob)

        scenarios.append(MarketScenario(
            name="Bullish Trend Continuation (BOS)",
            probability_percent=cont_prob,
            trigger_level=round(key_sh, 2),
            invalidation_level=round(key_sl, 2),
            description=f"Close above {key_sh:.2f} confirms bullish continuation toward next resistance zone.",
            action_bias="BUY"
        ))

        scenarios.append(MarketScenario(
            name="Bearish Change of Character (CHoCH Reversal)",
            probability_percent=choch_prob,
            trigger_level=round(key_sl, 2),
            invalidation_level=round(key_sh, 2),
            description=f"Loss and close below {key_sl:.2f} confirms market structure break and initiates reversal downward.",
            action_bias="SELL"
        ))

        scenarios.append(MarketScenario(
            name="Consolidation / Liquidity Trap",
            probability_percent=range_prob,
            trigger_level=round(latest_close, 2),
            invalidation_level=round(key_sl, 2),
            description=f"Chop between {key_sl:.2f} and {key_sh:.2f} — wait for breakout confirmation.",
            action_bias="WAIT"
        ))

    else:  # Bearish or Ranging
        cont_prob = 65 if choch_risk == "LOW" else (45 if choch_risk == "ELEVATED" else 30)
        choch_prob = 20 if choch_risk == "LOW" else (40 if choch_risk == "ELEVATED" else 50)
        range_prob = 100 - (cont_prob + choch_prob)

        scenarios.append(MarketScenario(
            name="Bearish Trend Continuation (BOS)",
            probability_percent=cont_prob,
            trigger_level=round(key_sl, 2),
            invalidation_level=round(key_sh, 2),
            description=f"Close below {key_sl:.2f} confirms bearish expansion toward lower liquidity pools.",
            action_bias="SELL"
        ))

        scenarios.append(MarketScenario(
            name="Bullish Change of Character (CHoCH Reversal)",
            probability_percent=choch_prob,
            trigger_level=round(key_sh, 2),
            invalidation_level=round(key_sl, 2),
            description=f"Break and close above {key_sh:.2f} confirms market structure reversal to bullish.",
            action_bias="BUY"
        ))

        scenarios.append(MarketScenario(
            name="Ranging / Fakeout Compression",
            probability_percent=range_prob,
            trigger_level=round(latest_close, 2),
            invalidation_level=round(key_sh, 2),
            description=f"Trapped between {key_sl:.2f} and {key_sh:.2f} — avoid premature market orders.",
            action_bias="WAIT"
        ))

    return CHoCHPredictionReport(
        symbol=symbol,
        timeframe="5m",
        current_regime=regime,
        choch_risk_level=choch_risk,
        divergence_detected=div_type,
        scenarios=scenarios,
        key_reversal_trigger=round(key_sl if is_1h_bullish else key_sh, 2),
        key_continuation_trigger=round(key_sh if is_1h_bullish else key_sl, 2),
        notes=notes
    )
