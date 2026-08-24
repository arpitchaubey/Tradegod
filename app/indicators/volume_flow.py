from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np

def calculate_vwap(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates Volume Weighted Average Price (VWAP) with +/- 1 and +/- 2 standard deviation bands.
    Returns: (vwap_series, upper_band_1, lower_band_1)
    """
    if df.empty or "close" not in df.columns:
        empty = pd.Series(dtype=float)
        return empty, empty, empty

    volume = df["volume"] if "volume" in df.columns and (df["volume"] > 0).any() else pd.Series(1000.0, index=df.index)
    high = df["high"] if "high" in df.columns else df["close"]
    low = df["low"] if "low" in df.columns else df["close"]
    close = df["close"]

    typical_price = (high + low + close) / 3.0
    cum_vol_price = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum().replace(0, np.nan)
    vwap = cum_vol_price / cum_vol

    # Standard deviation bands
    rolling_std = typical_price.rolling(window=min(20, len(df)), min_periods=1).std().fillna(0.5)
    upper_band_1 = vwap + (rolling_std * 1.5)
    lower_band_1 = vwap - (rolling_std * 1.5)

    return vwap.fillna(close), upper_band_1.fillna(close + 1.0), lower_band_1.fillna(close - 1.0)

def calculate_rvol(df: pd.DataFrame, period: int = 20) -> float:
    """
    Calculates Relative Volume (RVOL) = Current Candle Volume / Rolling Mean Volume.
    RVOL > 1.5 indicates institutional volume surge.
    """
    if df.empty or "volume" not in df.columns or len(df) < 5:
        return 1.0

    vol = df["volume"]
    if (vol == 0).all():
        return 1.0

    avg_vol = vol.rolling(window=min(period, len(df)), min_periods=1).mean().iloc[-1]
    current_vol = vol.iloc[-1]

    if avg_vol <= 0:
        return 1.0

    return round(float(current_vol / avg_vol), 2)

def calculate_obv(df: pd.DataFrame) -> Tuple[pd.Series, str]:
    """
    Calculates On-Balance Volume (OBV) and OBV Trend (Accumulation vs Distribution).
    Returns: (obv_series, obv_trend: "accumulation" | "distribution" | "neutral")
    """
    if df.empty or "close" not in df.columns:
        return pd.Series(dtype=float), "neutral"

    volume = df["volume"] if "volume" in df.columns and (df["volume"] > 0).any() else pd.Series(1000.0, index=df.index)
    close = df["close"]

    price_diff = close.diff()
    direction = np.where(price_diff > 0, 1, np.where(price_diff < 0, -1, 0))
    obv = (direction * volume).cumsum()

    # OBV Slope over last 10 periods
    if len(obv) >= 10:
        obv_sma = obv.rolling(10).mean()
        latest_obv = obv.iloc[-1]
        latest_sma = obv_sma.iloc[-1]
        if latest_obv > latest_sma:
            obv_trend = "accumulation"
        elif latest_obv < latest_sma:
            obv_trend = "distribution"
        else:
            obv_trend = "neutral"
    else:
        obv_trend = "neutral"

    return obv, obv_trend

def estimate_volume_delta(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Estimates Buying vs Selling Volume Delta based on candle body & wick dynamics.
    """
    if df.empty:
        return {"buy_volume_pct": 50.0, "sell_volume_pct": 50.0, "delta_bias": "neutral"}

    last = df.iloc[-1]
    c = float(last["close"])
    o = float(last["open"])
    h = float(last.get("high", c))
    l = float(last.get("low", c))

    total_range = max(1e-5, h - l)
    body = abs(c - o)
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    if c >= o:
        # Bullish candle: body + lower wick contribute to buy pressure
        buy_weight = (body + lower_wick) / total_range
        sell_weight = upper_wick / total_range
    else:
        # Bearish candle: body + upper wick contribute to sell pressure
        sell_weight = (body + upper_wick) / total_range
        buy_weight = lower_wick / total_range

    total_w = buy_weight + sell_weight
    if total_w <= 0:
        buy_pct = 50.0
        sell_pct = 50.0
    else:
        buy_pct = round((buy_weight / total_w) * 100, 1)
        sell_pct = round((sell_weight / total_w) * 100, 1)

    bias = "bullish_delta" if buy_pct > 58 else ("bearish_delta" if sell_pct > 58 else "neutral")

    return {
        "buy_volume_pct": buy_pct,
        "sell_volume_pct": sell_pct,
        "delta_bias": bias
    }
