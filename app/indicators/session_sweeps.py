from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timezone
from pydantic import BaseModel

class SessionLevel(BaseModel):
    session_name: str  # "ASIAN", "LONDON", "NEW_YORK", "PREVIOUS_DAY"
    high_price: float
    low_price: float
    is_swept_high: bool = False
    is_swept_low: bool = False
    sweep_type: str = "none"  # "bullish_low_sweep", "bearish_high_sweep", "none"
    sweep_description: str = ""

class SessionSweepsReport(BaseModel):
    asian_high: float
    asian_low: float
    london_high: float
    london_low: float
    prev_day_high: float
    prev_day_low: float
    active_sweeps: List[SessionLevel]
    liquidity_bias: str  # "bullish_reversal_sweep", "bearish_reversal_sweep", "neutral"
    sweep_summary: str

def calculate_session_levels_and_sweeps(df: pd.DataFrame) -> SessionSweepsReport:
    """
    Extracts Asian High/Low, London High/Low, Previous Day High/Low (PDH/PDL)
    and detects institutional liquidity sweeps (Judas swings).
    """
    if df.empty or len(df) < 10:
        return SessionSweepsReport(
            asian_high=0.0,
            asian_low=0.0,
            london_high=0.0,
            london_low=0.0,
            prev_day_high=0.0,
            prev_day_low=0.0,
            active_sweeps=[],
            liquidity_bias="neutral",
            sweep_summary="Insufficient historical candle data for session analysis."
        )

    # Ensure timestamp is datetime
    df_copy = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_copy["timestamp"]):
        df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"], utc=True)

    df_copy["hour"] = df_copy["timestamp"].dt.hour
    df_copy["date"] = df_copy["timestamp"].dt.date

    unique_dates = df_copy["date"].unique()
    current_date = unique_dates[-1]

    # 1. Previous Day High / Low
    if len(unique_dates) >= 2:
        prev_date = unique_dates[-2]
        prev_day_df = df_copy[df_copy["date"] == prev_date]
        pdh = float(prev_day_df["high"].max()) if not prev_day_df.empty else float(df_copy["high"].max())
        pdl = float(prev_day_df["low"].min()) if not prev_day_df.empty else float(df_copy["low"].min())
    else:
        # Fallback to rolling previous 24h
        pdh = float(df_copy["high"].iloc[:-10].max()) if len(df_copy) > 10 else float(df_copy["high"].max())
        pdl = float(df_copy["low"].iloc[:-10].min()) if len(df_copy) > 10 else float(df_copy["low"].min())

    # 2. Asian Session (00:00 to 08:00 UTC)
    today_df = df_copy[df_copy["date"] == current_date]
    asian_df = today_df[(today_df["hour"] >= 0) & (today_df["hour"] < 8)]
    if not asian_df.empty:
        asian_high = float(asian_df["high"].max())
        asian_low = float(asian_df["low"].min())
    else:
        # Fallback to first 8 hours of available current day
        asian_high = float(df_copy["high"].iloc[:min(20, len(df_copy))].max())
        asian_low = float(df_copy["low"].iloc[:min(20, len(df_copy))].min())

    # 3. London Session (08:00 to 13:00 UTC)
    london_df = today_df[(today_df["hour"] >= 8) & (today_df["hour"] < 13)]
    if not london_df.empty:
        london_high = float(london_df["high"].max())
        london_low = float(london_df["low"].min())
    else:
        london_high = asian_high
        london_low = asian_low

    latest_close = float(df_copy["close"].iloc[-1])
    latest_high = float(df_copy["high"].iloc[-1])
    latest_low = float(df_copy["low"].iloc[-1])
    latest_open = float(df_copy["open"].iloc[-1])

    active_sweeps: List[SessionLevel] = []
    liquidity_bias = "neutral"
    sweep_notes = []

    # 4. Check Asian High / Low Sweep
    asian_level = SessionLevel(
        session_name="ASIAN",
        high_price=round(asian_high, 2),
        low_price=round(asian_low, 2)
    )

    # Asian High Sweep (Price spiked above Asian High but closed below it -> Bearish Judas Reversal)
    if latest_high > asian_high and latest_close <= asian_high:
        asian_level.is_swept_high = True
        asian_level.sweep_type = "bearish_high_sweep"
        asian_level.sweep_description = f"Asian High (${asian_high:.2f}) swept and rejected — institutional liquidity grab (Bearish)."
        active_sweeps.append(asian_level)
        liquidity_bias = "bearish_reversal_sweep"
        sweep_notes.append(asian_level.sweep_description)

    # Asian Low Sweep (Price spiked below Asian Low but closed above it -> Bullish Judas Reversal)
    elif latest_low < asian_low and latest_close >= asian_low:
        asian_level.is_swept_low = True
        asian_level.sweep_type = "bullish_low_sweep"
        asian_level.sweep_description = f"Asian Low (${asian_low:.2f}) swept and rejected — buyer absorption liquidity grab (Bullish)."
        active_sweeps.append(asian_level)
        liquidity_bias = "bullish_reversal_sweep"
        sweep_notes.append(asian_level.sweep_description)

    # 5. Check Previous Day High / Low Sweep (PDH / PDL)
    pd_level = SessionLevel(
        session_name="PREVIOUS_DAY",
        high_price=round(pdh, 2),
        low_price=round(pdl, 2)
    )

    if latest_high > pdh and latest_close <= pdh:
        pd_level.is_swept_high = True
        pd_level.sweep_type = "bearish_high_sweep"
        pd_level.sweep_description = f"Previous Day High (PDH ${pdh:.2f}) swept and rejected (Bearish)."
        active_sweeps.append(pd_level)
        if liquidity_bias == "neutral":
            liquidity_bias = "bearish_reversal_sweep"
        sweep_notes.append(pd_level.sweep_description)

    elif latest_low < pdl and latest_close >= pdl:
        pd_level.is_swept_low = True
        pd_level.sweep_type = "bullish_low_sweep"
        pd_level.sweep_description = f"Previous Day Low (PDL ${pdl:.2f}) swept and rejected (Bullish)."
        active_sweeps.append(pd_level)
        if liquidity_bias == "neutral":
            liquidity_bias = "bullish_reversal_sweep"
        sweep_notes.append(pd_level.sweep_description)

    if not sweep_notes:
        summary = "No active session liquidity sweeps detected. Price trading within established session boundaries."
    else:
        summary = " | ".join(sweep_notes)

    return SessionSweepsReport(
        asian_high=round(asian_high, 2),
        asian_low=round(asian_low, 2),
        london_high=round(london_high, 2),
        london_low=round(london_low, 2),
        prev_day_high=round(pdh, 2),
        prev_day_low=round(pdl, 2),
        active_sweeps=active_sweeps,
        liquidity_bias=liquidity_bias,
        sweep_summary=summary
    )
