from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from pydantic import BaseModel

class SRLevel(BaseModel):
    level_type: str  # "resistance" or "support"
    price: float
    touches: int
    strength: str  # "strong", "medium", "weak"

class BreakoutInfo(BaseModel):
    is_breakout: bool = False
    direction: str = "none"  # "long" or "short"
    level: float = 0.0
    confirmed: bool = False
    retested: bool = False

def find_swing_points(
    df: pd.DataFrame,
    window: int = 3
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Finds swing highs and swing lows in candle series using a rolling window.
    Returns: (swing_highs, swing_lows)
    """
    if len(df) < (window * 2 + 1):
        return [], []

    swing_highs = []
    swing_lows = []

    highs = df["high"].values
    lows = df["low"].values
    times = df["timestamp"].values

    for i in range(window, len(df) - window):
        current_high = highs[i]
        current_low = lows[i]

        # Check Swing High
        if all(current_high > highs[i - j] for j in range(1, window + 1)) and \
           all(current_high >= highs[i + j] for j in range(1, window + 1)):
            swing_highs.append({"index": i, "price": float(current_high), "timestamp": str(times[i])})

        # Check Swing Low
        if all(current_low < lows[i - j] for j in range(1, window + 1)) and \
           all(current_low <= lows[i + j] for j in range(1, window + 1)):
            swing_lows.append({"index": i, "price": float(current_low), "timestamp": str(times[i])})

    return swing_highs, swing_lows

def identify_support_resistance(
    df: pd.DataFrame,
    pip_threshold: float = 0.5
) -> Tuple[List[SRLevel], List[SRLevel]]:
    """
    Identifies key resistance and support levels from swing highs/lows.
    Returns: (supports, resistances)
    """
    swing_highs, swing_lows = find_swing_points(df, window=3)

    resistances: List[SRLevel] = []
    supports: List[SRLevel] = []

    # Cluster resistance levels
    if swing_highs:
        prices = [sh["price"] for sh in swing_highs]
        # Sort and group prices within pip_threshold
        sorted_p = sorted(prices, reverse=True)
        used = [False] * len(sorted_p)

        for i in range(len(sorted_p)):
            if used[i]:
                continue
            cluster = [sorted_p[i]]
            used[i] = True
            for j in range(i + 1, len(sorted_p)):
                if not used[j] and abs(sorted_p[i] - sorted_p[j]) <= pip_threshold * 2:
                    cluster.append(sorted_p[j])
                    used[j] = True

            avg_price = sum(cluster) / len(cluster)
            touches = len(cluster)
            strength = "strong" if touches >= 3 else ("medium" if touches == 2 else "weak")
            resistances.append(SRLevel(level_type="resistance", price=avg_price, touches=touches, strength=strength))

    # Cluster support levels
    if swing_lows:
        prices = [sl["price"] for sl in swing_lows]
        sorted_p = sorted(prices)
        used = [False] * len(sorted_p)

        for i in range(len(sorted_p)):
            if used[i]:
                continue
            cluster = [sorted_p[i]]
            used[i] = True
            for j in range(i + 1, len(sorted_p)):
                if not used[j] and abs(sorted_p[i] - sorted_p[j]) <= pip_threshold * 2:
                    cluster.append(sorted_p[j])
                    used[j] = True

            avg_price = sum(cluster) / len(cluster)
            touches = len(cluster)
            strength = "strong" if touches >= 3 else ("medium" if touches == 2 else "weak")
            supports.append(SRLevel(level_type="support", price=avg_price, touches=touches, strength=strength))

    return supports, resistances

def detect_breakout(
    df: pd.DataFrame,
    pip_threshold: float = 0.2,
    atr_multiplier: float = 0.1,
    swing_window: int = 3
) -> BreakoutInfo:
    """
    Detects breakout across confirmed swing support/resistance levels with anti-fakeout confirmation:
    Requires EITHER:
      a) Candle close beyond level by at least atr_multiplier * ATR(14)
      b) 2 consecutive candle closes beyond the swing level.
    """
    if len(df) < (swing_window * 2 + 3):
        return BreakoutInfo()

    from app.indicators.volatility import calculate_atr
    atr_series = calculate_atr(df, 14)
    atr_val = float(atr_series.iloc[-1]) if not atr_series.empty and not pd.isna(atr_series.iloc[-1]) else 1.0
    atr_margin = atr_multiplier * atr_val

    supports, resistances = identify_support_resistance(df, pip_threshold=pip_threshold)

    latest_close = float(df["close"].iloc[-1])
    latest_open = float(df["open"].iloc[-1])
    latest_high = float(df["high"].iloc[-1])
    latest_low = float(df["low"].iloc[-1])
    prev_close = float(df["close"].iloc[-2])

    candle_range = max(1e-5, latest_high - latest_low)
    upper_wick = latest_high - max(latest_close, latest_open)
    lower_wick = min(latest_close, latest_open) - latest_low

    # Long Breakout above swing resistance
    for r in resistances:
        if latest_close > r.price:
            atr_confirmed = (latest_close >= r.price + atr_margin)
            two_closes_confirmed = (latest_close > r.price and prev_close > r.price)
            # Rejection wick filter: upper wick cannot dominate the candle (less than 60% of total candle range)
            no_topping_tail = (upper_wick / candle_range) < 0.60
            confirmed = (atr_confirmed or two_closes_confirmed) and (latest_close >= latest_open) and no_topping_tail

            return BreakoutInfo(
                is_breakout=True,
                direction="long",
                level=round(r.price, 2),
                confirmed=confirmed,
                retested=False
            )

    # Short Breakout below swing support
    for s in supports:
        if latest_close < s.price:
            atr_confirmed = (latest_close <= s.price - atr_margin)
            two_closes_confirmed = (latest_close < s.price and prev_close < s.price)
            # Rejection wick filter: lower wick cannot dominate the candle (less than 60% of total candle range)
            no_bottom_tail = (lower_wick / candle_range) < 0.60
            confirmed = (atr_confirmed or two_closes_confirmed) and (latest_close <= latest_open) and no_bottom_tail

            return BreakoutInfo(
                is_breakout=True,
                direction="short",
                level=round(s.price, 2),
                confirmed=confirmed,
                retested=False
            )

    return BreakoutInfo()
