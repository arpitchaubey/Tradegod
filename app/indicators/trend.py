from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
    """Calculates Exponential Moving Average for given period."""
    if df.empty or column not in df.columns:
        return pd.Series(dtype=float)
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_sma(df: pd.DataFrame, period: int = 50, column: str = "close") -> pd.Series:
    """Calculates Simple Moving Average for given period."""
    if df.empty or column not in df.columns:
        return pd.Series(dtype=float)
    return df[column].rolling(window=period).mean()

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculates Average Directional Index (ADX)."""
    if len(df) < period + 2:
        return pd.Series(25.0, index=df.index if not df.empty else None)

    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr_smooth = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean()
    plus_dm_smooth = pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean()
    minus_dm_smooth = pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean()

    plus_di = 100 * (plus_dm_smooth / tr_smooth.replace(0, np.nan))
    minus_di = 100 * (minus_dm_smooth / tr_smooth.replace(0, np.nan))

    di_diff = (plus_di - minus_di).abs()
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum.replace(0, np.nan))
    adx = dx.ewm(alpha=1/period, adjust=False).mean().fillna(25.0)

    return adx

def evaluate_adx_gate(df: pd.DataFrame, adx_threshold: float = 20.0, period: int = 14) -> Tuple[float, str, bool]:
    """
    Evaluates ADX trend strength gate.
    Returns: (adx_value: float, regime: ("trending" | "ranging"), passed: bool)
    """
    if df.empty or len(df) < period + 1:
        return (25.0, "trending", True)

    adx_series = calculate_adx(df, period=period)
    adx_val = float(adx_series.iloc[-1])
    regime = "trending" if adx_val >= adx_threshold else "ranging"
    passed = adx_val >= adx_threshold
    return (round(adx_val, 2), regime, passed)

def evaluate_trend_alignment(
    df: pd.DataFrame,
    fast_period: int = 20,
    slow_period: int = 50,
    adx_threshold: float = 20.0
) -> Tuple[str, bool, float, float]:
    """
    Evaluates trend direction and alignment based on EMA fast vs EMA slow.
    If ADX < adx_threshold, market is 'ranging' and trend alignment is False (suppressed).
    Returns: (trend_direction ("bullish" | "bearish" | "ranging"), aligned, fast_val, slow_val)
    """
    if df.empty or len(df) < 8:
        return ("ranging", False, 0.0, 0.0)

    eff_fast = min(fast_period, max(5, len(df) // 3))
    eff_slow = min(slow_period, max(8, len(df) - 1))

    adx_val, regime, adx_pass = evaluate_adx_gate(df, adx_threshold=adx_threshold)

    ema_fast = calculate_ema(df, eff_fast)
    ema_slow = calculate_ema(df, eff_slow)


    fast_val = float(ema_fast.iloc[-1])
    slow_val = float(ema_slow.iloc[-1])
    close_price = float(df["close"].iloc[-1])

    if not adx_pass:
        return ("ranging", False, fast_val, slow_val)

    if fast_val > slow_val and close_price > fast_val:
        return ("bullish", True, fast_val, slow_val)
    elif fast_val < slow_val and close_price < fast_val:
        return ("bearish", True, fast_val, slow_val)
    elif fast_val > slow_val:
        return ("bullish", False, fast_val, slow_val)
    elif fast_val < slow_val:
        return ("bearish", False, fast_val, slow_val)
    else:
        return ("ranging", False, fast_val, slow_val)
