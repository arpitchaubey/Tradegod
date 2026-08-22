from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import pandas as pd
from pydantic import BaseModel, Field

class Candle(BaseModel):
    symbol: str = "XAU/USD"
    timeframe: str = "5m"
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    source: str = "twelvedata"  # "twelvedata", "yahoo", or "synthetic"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source
        }

def normalize_candles_df(candles: List[Candle]) -> pd.DataFrame:
    """Converts a list of Candle objects into a standardized pandas DataFrame."""
    if not candles:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "source"])

    records = [
        {
            "timestamp": pd.to_datetime(c.timestamp),
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
            "source": str(getattr(c, "source", "twelvedata"))
        }
        for c in candles
    ]

    df = pd.DataFrame(records)
    df.sort_values("timestamp", inplace=True)
    df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def resample_candles(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
    """
    Resamples standard lower timeframe candles (e.g., 5m) into target higher timeframe (e.g., 15m, 1h).
    target_timeframe options: '5m', '15m', '1h', '4h', '1d'.
    """
    if df.empty or "timestamp" not in df.columns:
        return df

    tf_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d"
    }

    freq = tf_map.get(target_timeframe.lower(), "5Min")
    df_copy = df.copy()
    df_copy.set_index("timestamp", inplace=True)

    agg_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }
    if "source" in df_copy.columns:
        agg_dict["source"] = "last"

    resampled = df_copy.resample(freq).agg(agg_dict).dropna()

    resampled.reset_index(inplace=True)
    return resampled
