from typing import Dict, List, Optional
import pandas as pd

from app.data.normalizer import Candle, normalize_candles_df, resample_candles
from app.data.provider import get_data_provider, BaseDataProvider
from app.data.chart_info import build_chart_info, ActiveChartInfo
from app.config import settings

class CandleBufferManager:
    """In-memory cache and buffer for symbol candles across timeframes."""

    def __init__(self, provider: Optional[BaseDataProvider] = None):
        self.provider = provider or get_data_provider(settings.default_data_provider, settings.twelve_data_api_key)
        self.cache: Dict[str, Dict[str, pd.DataFrame]] = {}  # {symbol: {timeframe: df}}

    async def get_candles_df(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Retrieves candles DataFrame for a given symbol and timeframe."""
        symbol = symbol.upper()
        if symbol not in self.cache:
            self.cache[symbol] = {}

        if force_refresh or timeframe not in self.cache[symbol]:
            raw_candles = await self.provider.fetch_candles(symbol, timeframe, limit)
            df = normalize_candles_df(raw_candles)
            self.cache[symbol][timeframe] = df

        return self.cache[symbol][timeframe]

    async def get_multi_timeframe_dfs(
        self,
        symbol: str = "XAU/USD",
        timeframes: Optional[Dict[str, str]] = None,
        limit: int = 500
    ) -> Dict[str, pd.DataFrame]:
        """Fetches trend (1H), setup (15M), and entry (5M) dataframes."""
        tf_dict = timeframes or {"trend": "1h", "setup": "15m", "entry": "5m"}
        result: Dict[str, pd.DataFrame] = {}

        entry_tf = tf_dict.get("entry", "5m")
        entry_df = await self.get_candles_df(symbol, entry_tf, limit=limit)
        result[entry_tf] = entry_df

        for tf_key, tf_val in tf_dict.items():
            if tf_val not in result:
                if len(entry_df) > 0 and tf_val in ["15m", "1h", "4h"]:
                    # Resample from entry df if possible for consistency
                    resampled = resample_candles(entry_df, tf_val)
                    result[tf_val] = resampled
                else:
                    df = await self.get_candles_df(symbol, tf_val, limit=limit)
                    result[tf_val] = df

        return result

    async def get_active_chart_info(
        self,
        symbol: str = "XAU/USD",
        timeframes: Optional[Dict[str, str]] = None
    ) -> ActiveChartInfo:
        """Builds active chart metadata for given symbol."""
        tf_dict = timeframes or {"trend": "1h", "setup": "15m", "entry": "5m"}
        entry_tf = tf_dict.get("entry", "5m")
        df = await self.get_candles_df(symbol, entry_tf, limit=100)

        last_price = float(df["close"].iloc[-1]) if not df.empty else 0.0
        candle_count = len(df)

        return build_chart_info(
            symbol=symbol,
            provider=settings.default_data_provider,
            timeframes=tf_dict,
            last_price=last_price,
            candle_count=candle_count
        )

# Global buffer instance
candle_buffer = CandleBufferManager()
