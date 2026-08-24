from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from pydantic import BaseModel

from app.indicators.structure import identify_support_resistance, SRLevel
from app.indicators.volatility import calculate_atr
from app.indicators.volume_flow import calculate_rvol

class LevelBehaviorReport(BaseModel):
    level_price: float
    level_type: str  # "resistance" or "support"
    behavior: str    # "REJECTION_BOUNCE", "CLEAN_BREAKOUT", "FAKEOUT_SWEEP", "RETEST_CONFIRMED", "APPROACHING"
    touches_history: int
    strength: str    # "strong", "medium", "weak"
    distance_pips: float
    description: str

class SRPriceBehaviorAnalysis(BaseModel):
    nearest_support: Optional[LevelBehaviorReport] = None
    nearest_resistance: Optional[LevelBehaviorReport] = None
    dominant_behavior: str
    active_levels_count: int
    summary: str

def analyze_sr_price_behavior(df: pd.DataFrame, pip_threshold: float = 0.5) -> SRPriceBehaviorAnalysis:
    """
    Evaluates price history and immediate behavior at key Support and Resistance levels.
    """
    if df.empty or len(df) < 10:
        return SRPriceBehaviorAnalysis(
            nearest_support=None,
            nearest_resistance=None,
            dominant_behavior="NEUTRAL",
            active_levels_count=0,
            summary="Insufficient data for S/R behavior analysis."
        )

    supports, resistances = identify_support_resistance(df, pip_threshold=pip_threshold)

    latest_close = float(df["close"].iloc[-1])
    latest_open = float(df["open"].iloc[-1])
    latest_high = float(df["high"].iloc[-1])
    latest_low = float(df["low"].iloc[-1])
    prev_close = float(df["close"].iloc[-2])

    atr_series = calculate_atr(df, 14)
    atr_val = float(atr_series.iloc[-1]) if not atr_series.empty else 1.0
    rvol = calculate_rvol(df)

    candle_range = max(1e-5, latest_high - latest_low)
    upper_wick = latest_high - max(latest_close, latest_open)
    lower_wick = min(latest_close, latest_open) - latest_low

    nearest_res_report: Optional[LevelBehaviorReport] = None
    nearest_sup_report: Optional[LevelBehaviorReport] = None

    # Evaluate Resistance Behavior
    res_candidates = [r for r in resistances if r.price >= latest_close - (atr_val * 0.5)]
    if res_candidates:
        closest_res = min(res_candidates, key=lambda r: abs(r.price - latest_close))
        dist = round(abs(closest_res.price - latest_close), 2)

        # Classify behavior at resistance
        if latest_high >= closest_res.price and latest_close < closest_res.price and (upper_wick / candle_range) >= 0.40:
            behavior = "FAKEOUT_SWEEP"
            desc = f"Resistance at ${closest_res.price:.2f} rejected with upper wick sweep (Bearish Fakeout)."
        elif latest_close > closest_res.price and prev_close <= closest_res.price and rvol >= 1.2:
            behavior = "CLEAN_BREAKOUT"
            desc = f"Clean breakout above resistance at ${closest_res.price:.2f} on high volume ({rvol}x)."
        elif latest_low <= closest_res.price and latest_close >= closest_res.price and prev_close > closest_res.price:
            behavior = "RETEST_CONFIRMED"
            desc = f"Successful retest of broken resistance at ${closest_res.price:.2f}, now holding as new support."
        elif abs(latest_close - closest_res.price) <= (atr_val * 0.3):
            behavior = "REJECTION_BOUNCE" if latest_close < closest_res.price else "CLEAN_BREAKOUT"
            desc = f"Price testing key resistance at ${closest_res.price:.2f} with {closest_res.touches} historical touches."
        else:
            behavior = "APPROACHING"
            desc = f"Approaching overhead resistance zone at ${closest_res.price:.2f} ({dist} pips away)."

        nearest_res_report = LevelBehaviorReport(
            level_price=round(closest_res.price, 2),
            level_type="resistance",
            behavior=behavior,
            touches_history=closest_res.touches,
            strength=closest_res.strength,
            distance_pips=dist,
            description=desc
        )

    # Evaluate Support Behavior
    sup_candidates = [s for s in supports if s.price <= latest_close + (atr_val * 0.5)]
    if sup_candidates:
        closest_sup = min(sup_candidates, key=lambda s: abs(s.price - latest_close))
        dist = round(abs(latest_close - closest_sup.price), 2)

        # Classify behavior at support
        if latest_low <= closest_sup.price and latest_close > closest_sup.price and (lower_wick / candle_range) >= 0.40:
            behavior = "FAKEOUT_SWEEP"
            desc = f"Support at ${closest_sup.price:.2f} swept and defended with lower wick rejection (Bullish Fakeout)."
        elif latest_close < closest_sup.price and prev_close >= closest_sup.price and rvol >= 1.2:
            behavior = "CLEAN_BREAKOUT"
            desc = f"Clean breakdown below support at ${closest_sup.price:.2f} on volume expansion ({rvol}x)."
        elif latest_high >= closest_sup.price and latest_close <= closest_sup.price and prev_close < closest_sup.price:
            behavior = "RETEST_CONFIRMED"
            desc = f"Successful retest of broken support at ${closest_sup.price:.2f}, now acting as new resistance."
        elif abs(latest_close - closest_sup.price) <= (atr_val * 0.3):
            behavior = "REJECTION_BOUNCE" if latest_close > closest_sup.price else "CLEAN_BREAKOUT"
            desc = f"Price interacting with support at ${closest_sup.price:.2f} ({closest_sup.touches} touches)."
        else:
            behavior = "APPROACHING"
            desc = f"Price trading above key support at ${closest_sup.price:.2f} ({dist} pips away)."

        nearest_sup_report = LevelBehaviorReport(
            level_price=round(closest_sup.price, 2),
            level_type="support",
            behavior=behavior,
            touches_history=closest_sup.touches,
            strength=closest_sup.strength,
            distance_pips=dist,
            description=desc
        )

    # Dominant behavior
    dom = "NEUTRAL"
    if nearest_res_report and nearest_res_report.behavior in ["CLEAN_BREAKOUT", "RETEST_CONFIRMED"]:
        dom = "BULLISH_EXPANSION"
    elif nearest_sup_report and nearest_sup_report.behavior in ["CLEAN_BREAKOUT", "RETEST_CONFIRMED"]:
        dom = "BEARISH_EXPANSION"
    elif (nearest_res_report and nearest_res_report.behavior in ["REJECTION_BOUNCE", "FAKEOUT_SWEEP"]):
        dom = "BEARISH_REJECTION"
    elif (nearest_sup_report and nearest_sup_report.behavior in ["REJECTION_BOUNCE", "FAKEOUT_SWEEP"]):
        dom = "BULLISH_BOUNCE"

    total_levels = len(supports) + len(resistances)
    summary_parts = []
    if nearest_res_report:
        summary_parts.append(nearest_res_report.description)
    if nearest_sup_report:
        summary_parts.append(nearest_sup_report.description)

    summary = " | ".join(summary_parts) if summary_parts else "Price moving freely between S/R liquidity clusters."

    return SRPriceBehaviorAnalysis(
        nearest_support=nearest_sup_report,
        nearest_resistance=nearest_res_report,
        dominant_behavior=dom,
        active_levels_count=total_levels,
        summary=summary
    )
