from typing import Dict, List, Optional
import pandas as pd

from app.data.normalizer import Candle, normalize_candles_df, resample_candles
from app.data.provider import get_data_provider, BaseDataProvider
from app.data.chart_info import build_chart_info, ActiveChartInfo
from app.config import settings

import time

class CandleBufferManager:
    """In-memory cache and buffer for symbol candles across timeframes."""

    def __init__(self, provider: Optional[BaseDataProvider] = None):
        self.provider = provider or get_data_provider(settings.default_data_provider, settings.twelve_data_api_key)
        self.cache: Dict[str, Dict[str, pd.DataFrame]] = {}  # {symbol: {timeframe: df}}
        self.cache_time: Dict[str, Dict[str, float]] = {}    # {symbol: {timeframe: timestamp}}
        self.ttl_seconds: float = 4.0

    async def get_candles_df(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Retrieves candles DataFrame for a given symbol and timeframe with TTL expiration."""
        symbol = symbol.upper()
        if symbol not in self.cache:
            self.cache[symbol] = {}
            self.cache_time[symbol] = {}

        now = time.time()
        last_fetch = self.cache_time[symbol].get(timeframe, 0.0)
        is_expired = (now - last_fetch) > self.ttl_seconds

        if force_refresh or is_expired or timeframe not in self.cache[symbol]:
            raw_candles = await self.provider.fetch_candles(symbol, timeframe, limit)
            df = normalize_candles_df(raw_candles)
            self.cache[symbol][timeframe] = df
            self.cache_time[symbol][timeframe] = now

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
                df = await self.get_candles_df(symbol, tf_val, limit=max(limit, 200))
                result[tf_val] = df
            # Map semantic alias
            result[tf_key] = result[tf_val]

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
