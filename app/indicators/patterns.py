from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from pydantic import BaseModel

class FVGInfo(BaseModel):
    fvg_type: str  # "bullish", "bearish", "bullish_inversion", "bearish_inversion", "none"
    top_price: float
    bottom_price: float
    gap_size: float
    is_mitigated: bool = False
    is_inverted: bool = False
    retested_inversion: bool = False
    description: str = ""

class StructureEvent(BaseModel):
    event_type: str  # "BOS", "CHoCH", "SWEEP", "NONE"
    direction: str   # "bullish", "bearish", "neutral"
    level: float
    timestamp: str
    description: str

def calculate_c2c_velocity(df: pd.DataFrame, window: int = 5) -> Dict[str, Any]:
    """
    Calculates Close-to-Close (C2C) momentum velocity and acceleration.
    """
    if len(df) < window + 2:
        return {"c2c_velocity": 0.0, "c2c_acceleration": 0.0, "velocity_state": "flat"}

    closes = df["close"]
    returns = closes.pct_change()
    c2c_vel = float(returns.tail(window).mean() * 1000)  # Basis point scale
    c2c_acc = float(returns.diff().tail(window).mean() * 1000)

    if c2c_vel > 1.5 and c2c_acc >= 0:
        state = "accelerating_bullish"
    elif c2c_vel > 0.5:
        state = "steady_bullish"
    elif c2c_vel < -1.5 and c2c_acc <= 0:
        state = "accelerating_bearish"
    elif c2c_vel < -0.5:
        state = "steady_bearish"
    else:
        state = "flat_consolidation"

    return {
        "c2c_velocity": round(c2c_vel, 3),
        "c2c_acceleration": round(c2c_acc, 3),
        "velocity_state": state
    }

def detect_fair_value_gaps(df: pd.DataFrame, min_gap_pips: float = 0.5) -> List[FVGInfo]:
    """
    Detects 3-candle Fair Value Gaps (FVG) and Inversion FVGs (iFVG).
    - Standard Bullish FVG: C1 High < C3 Low
    - Standard Bearish FVG: C1 Low > C3 High
    - Inversion FVG (iFVG): When price closes completely through an FVG,
      converting former support into resistance (or former resistance into support).
    """
    fvgs: List[FVGInfo] = []
    if len(df) < 4:
        return fvgs

    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values

    for i in range(2, len(df)):
        c1_high = highs[i - 2]
        c1_low = lows[i - 2]
        c3_high = highs[i]
        c3_low = lows[i]

        # 1. Bullish FVG
        if c3_low > c1_high:
            gap = c3_low - c1_high
            if gap >= min_gap_pips:
                current_p = closes[-1]
                mitigated = (current_p <= c3_low and current_p >= c1_high)

                # Check for Inversion (Price closed below bottom level c1_high)
                is_inverted = any(closes[j] < c1_high for j in range(i + 1, len(df)))
                retested = False
                fvg_type = "bullish"
                desc = f"Bullish FVG support at ${c1_high:.2f} - ${c3_low:.2f}"

                if is_inverted:
                    fvg_type = "bearish_inversion"
                    retested = (current_p >= c1_high and current_p <= c3_low)
                    desc = f"🚨 Bearish Inversion FVG: Broken support now acting as overhead resistance at ${c1_high:.2f} - ${c3_low:.2f}"

                fvgs.append(FVGInfo(
                    fvg_type=fvg_type,
                    top_price=round(float(c3_low), 2),
                    bottom_price=round(float(c1_high), 2),
                    gap_size=round(float(gap), 2),
                    is_mitigated=mitigated,
                    is_inverted=is_inverted,
                    retested_inversion=retested,
                    description=desc
                ))

        # 2. Bearish FVG
        elif c1_low > c3_high:
            gap = c1_low - c3_high
            if gap >= min_gap_pips:
                current_p = closes[-1]
                mitigated = (current_p >= c3_high and current_p <= c1_low)

                # Check for Inversion (Price closed above top level c1_low)
                is_inverted = any(closes[j] > c1_low for j in range(i + 1, len(df)))
                retested = False
                fvg_type = "bearish"
                desc = f"Bearish FVG resistance at ${c3_high:.2f} - ${c1_low:.2f}"

                if is_inverted:
                    fvg_type = "bullish_inversion"
                    retested = (current_p <= c1_low and current_p >= c3_high)
                    desc = f"🚀 Bullish Inversion FVG: Broken resistance now acting as base support at ${c3_high:.2f} - ${c1_low:.2f}"

                fvgs.append(FVGInfo(
                    fvg_type=fvg_type,
                    top_price=round(float(c1_low), 2),
                    bottom_price=round(float(c3_high), 2),
                    gap_size=round(float(gap), 2),
                    is_mitigated=mitigated,
                    is_inverted=is_inverted,
                    retested_inversion=retested,
                    description=desc
                ))

    return fvgs[-6:]  # Return most recent 6 FVGs / iFVGs

def detect_market_structure_events(df: pd.DataFrame, swing_window: int = 3) -> List[StructureEvent]:
    """
    Identifies Break of Structure (BOS), Change of Character (CHoCH), and Liquidity Sweeps.
    """
    from app.indicators.structure import find_swing_points
    swing_highs, swing_lows = find_swing_points(df, window=swing_window)
    events: List[StructureEvent] = []

    if not swing_highs or not swing_lows or len(df) < 10:
        return events

    latest_close = float(df["close"].iloc[-1])
    latest_high = float(df["high"].iloc[-1])
    latest_low = float(df["low"].iloc[-1])
    ts = str(df["timestamp"].iloc[-1])

    recent_sh = swing_highs[-1]["price"]
    recent_sl = swing_lows[-1]["price"]

    # 1. Bullish BOS / Sweep
    if latest_high > recent_sh:
        if latest_close > recent_sh:
            events.append(StructureEvent(
                event_type="BOS",
                direction="bullish",
                level=recent_sh,
                timestamp=ts,
                description=f"Bullish Break of Structure: Closed above swing high at {recent_sh:.2f}"
            ))
        else:
            events.append(StructureEvent(
                event_type="SWEEP",
                direction="bearish",  # Sweep of high often precedes bearish rejection
                level=recent_sh,
                timestamp=ts,
                description=f"Liquidity Sweep above {recent_sh:.2f}: Pierced high without body close"
            ))

    # 2. Bearish BOS / Sweep
    if latest_low < recent_sl:
        if latest_close < recent_sl:
            events.append(StructureEvent(
                event_type="BOS",
                direction="bearish",
                level=recent_sl,
                timestamp=ts,
                description=f"Bearish Break of Structure: Closed below swing low at {recent_sl:.2f}"
            ))
        else:
            events.append(StructureEvent(
                event_type="SWEEP",
                direction="bullish",  # Sweep of low often precedes bullish bounce
                level=recent_sl,
                timestamp=ts,
                description=f"Liquidity Sweep below {recent_sl:.2f}: Pierced low without body close"
            ))

    # 3. CHoCH (Change of Character): Reversal past intermediate structural pivots
    if len(swing_lows) >= 2 and len(swing_highs) >= 2:
        prev_sl = swing_lows[-2]["price"]
        prev_sh = swing_highs[-2]["price"]

        # Bearish CHoCH: Uptrending price breaks the previous structural higher low
        if latest_close < prev_sl and recent_sh > prev_sh:
            events.append(StructureEvent(
                event_type="CHoCH",
                direction="bearish",
                level=prev_sl,
                timestamp=ts,
                description=f"🚨 Bearish Change of Character (CHoCH): Broke key structural support at {prev_sl:.2f}"
            ))

        # Bullish CHoCH: Downtrending price breaks the previous structural lower high
        elif latest_close > prev_sh and recent_sl < prev_sl:
            events.append(StructureEvent(
                event_type="CHoCH",
                direction="bullish",
                level=prev_sh,
                timestamp=ts,
                description=f"🚀 Bullish Change of Character (CHoCH): Broke key structural resistance at {prev_sh:.2f}"
            ))

    return events

def detect_candlestick_formations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies high-probability candlestick patterns (Pinbars, Engulfing, Marubozu).
    """
    if len(df) < 2:
        return {"pattern": "none", "bias": "neutral", "strength": 0}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    c = float(last["close"])
    o = float(last["open"])
    h = float(last["high"])
    l = float(last["low"])

    prev_c = float(prev["close"])
    prev_o = float(prev["open"])

    total_range = max(1e-5, h - l)
    body = abs(c - o)
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    # Bullish Pinbar (Hammer)
    if lower_wick / total_range >= 0.60 and upper_wick / total_range <= 0.15:
        return {"pattern": "Bullish Pinbar", "bias": "bullish", "strength": 85}

    # Bearish Pinbar (Shooting Star)
    if upper_wick / total_range >= 0.60 and lower_wick / total_range <= 0.15:
        return {"pattern": "Bearish Shooting Star", "bias": "bearish", "strength": 85}

    # Bullish Engulfing
    if prev_c < prev_o and c > o and c >= prev_o and o <= prev_c and body > abs(prev_c - prev_o):
        return {"pattern": "Bullish Engulfing", "bias": "bullish", "strength": 80}

    # Bearish Engulfing
    if prev_c > prev_o and c < o and c <= prev_o and o >= prev_c and body > abs(prev_c - prev_o):
        return {"pattern": "Bearish Engulfing", "bias": "bearish", "strength": 80}

    # Marubozu (Strong Momentum)
    if body / total_range >= 0.85:
        pattern_name = "Bullish Marubozu" if c > o else "Bearish Marubozu"
        bias = "bullish" if c > o else "bearish"
        return {"pattern": pattern_name, "bias": bias, "strength": 75}

    return {"pattern": "Normal Candle", "bias": "neutral", "strength": 40}
