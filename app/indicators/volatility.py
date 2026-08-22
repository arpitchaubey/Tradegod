from typing import Tuple
import pandas as pd
import numpy as np

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    if len(df) < period + 1:
        return pd.Series(dtype=float)

    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_atr_percentile(df: pd.DataFrame, atr_period: int = 14, lookback: int = 100) -> float:
    """
    Calculates rolling ATR(14) percentile rank (0 to 100) over the last N periods.
    """
    if df.empty or len(df) < atr_period + 2:
        return 50.0

    atr_series = calculate_atr(df, atr_period).dropna()
    if len(atr_series) == 0:
        return 50.0

    window = atr_series.iloc[-min(len(atr_series), lookback):]
    current_val = float(window.iloc[-1])
    less_count = (window < current_val).sum()
    percentile = (less_count / max(1, len(window))) * 100.0
    return round(float(percentile), 2)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculates Volume Weighted Average Price (VWAP)."""
    if df.empty or "volume" not in df.columns or df["volume"].sum() == 0:
        return df["close"] if not df.empty else pd.Series(dtype=float)

    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    vwap = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    return vwap

def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    column: str = "close"
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Bollinger Bands.
    Returns: (upper_band, middle_band, lower_band)
    """
    if len(df) < period or column not in df.columns:
        empty = pd.Series(dtype=float)
        return empty, empty, empty

    middle = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()

    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)

    return upper, middle, lower
