from typing import Dict, List, Optional
import asyncio
import time
import pandas as pd

from app.data.normalizer import Candle, normalize_candles_df, resample_candles
from app.data.provider import get_data_provider, BaseDataProvider
from app.data.chart_info import build_chart_info, ActiveChartInfo
from app.config import settings

class CandleBufferManager:
    """High-performance in-memory cache and buffer for symbol candles across multi-timeframes."""

    def __init__(self, provider: Optional[BaseDataProvider] = None):
        self.provider = provider or get_data_provider(settings.default_data_provider, settings.twelve_data_api_key)
        self.cache: Dict[str, Dict[str, pd.DataFrame]] = {}  # {symbol: {timeframe: df}}
        self.cache_time: Dict[str, Dict[str, float]] = {}    # {symbol: {timeframe: timestamp}}
        self.ttl_seconds: float = 20.0

    async def get_candles_df(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 120,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Retrieves candles DataFrame for a given symbol and timeframe with high-speed caching."""
        symbol = symbol.upper()
        if symbol not in self.cache:
            self.cache[symbol] = {}
            self.cache_time[symbol] = {}

        now = time.time()
        last_fetch = self.cache_time[symbol].get(timeframe, 0.0)
        is_expired = (now - last_fetch) > self.ttl_seconds

        if force_refresh or is_expired or timeframe not in self.cache[symbol]:
            try:
                raw_candles = await self.provider.fetch_candles(symbol, timeframe, limit)
                if raw_candles:
                    df = normalize_candles_df(raw_candles)
                    self.cache[symbol][timeframe] = df
                    self.cache_time[symbol][timeframe] = now
            except Exception:
                # If network fails but we have cached data, retain cached data
                if timeframe not in self.cache[symbol]:
                    from app.data.provider import MockDataProvider
                    mock_candles = await MockDataProvider().fetch_candles(symbol, timeframe, limit)
                    self.cache[symbol][timeframe] = normalize_candles_df(mock_candles)
                    self.cache_time[symbol][timeframe] = now

        return self.cache[symbol].get(timeframe, pd.DataFrame())

    async def get_multi_timeframe_dfs(
        self,
        symbol: str = "XAU/USD",
        timeframes: Optional[Dict[str, str]] = None,
        limit: int = 120
    ) -> Dict[str, pd.DataFrame]:
        """Fetches all timeframes in parallel using asyncio.gather for sub-second execution."""
        tf_dict = timeframes or {"trend": "1h", "setup": "15m", "entry": "5m"}
        unique_tfs = list(set(tf_dict.values()))
        
        # Parallel concurrent fetch
        tasks = [self.get_candles_df(symbol, tf, limit=limit) for tf in unique_tfs]
        dfs = await asyncio.gather(*tasks, return_exceptions=True)

        result: Dict[str, pd.DataFrame] = {}
        for tf, df in zip(unique_tfs, dfs):
            if isinstance(df, pd.DataFrame) and not df.empty:
                result[tf] = df
            else:
                # Fallback to cached or mock
                result[tf] = self.cache.get(symbol.upper(), {}).get(tf, pd.DataFrame())

        # Map semantic aliases ('trend' -> '1h', 'setup' -> '15m', 'entry' -> '5m')
        for tf_key, tf_val in tf_dict.items():
            if tf_val in result:
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
        df = await self.get_candles_df(symbol, entry_tf, limit=60)

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
