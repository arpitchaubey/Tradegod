from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import math
import random
import httpx

from app.data.normalizer import Candle
from app.data.symbols import get_symbol_spec

import json
import logging

logger = logging.getLogger(__name__)

async def log_execution_event(event_type: str, message: str, details: dict = None):
    """Utility helper to persist system events to DBExecutionLog."""
    try:
        from app.database.connection import AsyncSessionLocal
        from app.database.models import DBExecutionLog
        async with AsyncSessionLocal() as session:
            log_item = DBExecutionLog(
                event_type=event_type,
                message=message,
                details_json=json.dumps(details or {})
            )
            session.add(log_item)
            await session.commit()
    except Exception as e:
        logger.warning(f"Could not write execution log: {e}")

class BaseDataProvider(ABC):
    """Abstract base class for all market data providers."""

    @abstractmethod
    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        """Fetch historical candles for a symbol and timeframe."""
        pass

class MockDataProvider(BaseDataProvider):
    """
    Realistic synthetic candle generator for offline development, backtesting,
    and testing multi-timeframe strategies across XAU/USD, Forex, Crypto, etc.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    async def fetch_candles(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        spec = get_symbol_spec(symbol)
        tf_minutes_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
        minutes = tf_minutes_map.get(timeframe.lower(), 5)

        base_prices = {
            "XAU/USD": 4670.0,
            "XAG/USD": 69.50,
            "EUR/USD": 1.1670,
            "GBP/USD": 1.3640,
            "USD/JPY": 159.10,
            "BTC/USD": 78000.0,
            "ETH/USD": 2480.0,
            "US30": 53400.0
        }

        start_price = base_prices.get(spec.symbol, 4670.0)
        volatility = spec.pip_size * (20 if spec.category == "metals" else 15)

        now = datetime.now(timezone.utc)
        start_time = now - timedelta(minutes=minutes * limit)

        candles: List[Candle] = []
        current_price = start_price

        # Use deterministic random generator based on symbol and index
        random.seed(self.seed + hash(symbol) % 1000)

        trend_factor = 0.05  # Slight upward drift
        for i in range(limit):
            candle_time = start_time + timedelta(minutes=minutes * i)

            # Generate OHLC
            change = (random.gauss(0, 1) + trend_factor) * volatility
            open_p = current_price
            close_p = open_p + change

            high_extra = abs(random.gauss(0, 1)) * volatility * 0.8
            low_extra = abs(random.gauss(0, 1)) * volatility * 0.8

            high_p = max(open_p, close_p) + high_extra
            low_p = min(open_p, close_p) - low_extra
            volume = round(random.uniform(100, 1500), 2)

            candles.append(Candle(
                symbol=spec.symbol,
                timeframe=timeframe,
                timestamp=candle_time,
                open=round(open_p, spec.quote_precision),
                high=round(high_p, spec.quote_precision),
                low=round(low_p, spec.quote_precision),
                close=round(close_p, spec.quote_precision),
                volume=volume,
                source="synthetic"
            ))

            current_price = close_p

        return candles

class TwelveDataProvider(BaseDataProvider):
    """Data provider client for Twelve Data REST API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"

    async def fetch_candles(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        if not self.api_key:
            await log_execution_event("DATA_FALLBACK", "No Twelve Data API key provided. Falling back to Yahoo Finance", {"symbol": symbol, "timeframe": timeframe})
            return await YahooFinanceProvider().fetch_candles(symbol, timeframe, limit)

        tf_param_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1day"}
        interval = tf_param_map.get(timeframe.lower(), "5min")

        spec = get_symbol_spec(symbol)
        api_symbol = spec.symbol

        params = {
            "symbol": api_symbol,
            "interval": interval,
            "outputsize": limit,
            "apikey": self.api_key
        }

        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/time_series", params=params)
                data = resp.json()
                if "values" not in data or not data["values"]:
                    # Fallback to Real-time Live Spot Market Provider
                    await log_execution_event("DATA_FALLBACK", "Twelve Data API quota reached/empty. Falling back to Live Spot Market Feed", {"symbol": symbol, "response": str(data)[:150]})
                    return await LiveSpotMarketProvider().fetch_candles(symbol, timeframe, limit)

                candles: List[Candle] = []
                for item in reversed(data["values"]):
                    dt_str = item["datetime"]
                    try:
                        if " " in dt_str:
                            ts = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        else:
                            ts = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
                    except Exception:
                        ts = datetime.now(timezone.utc)

                    candles.append(Candle(
                        symbol=spec.symbol,
                        timeframe=timeframe,
                        timestamp=ts,
                        open=float(item["open"]),
                        high=float(item["high"]),
                        low=float(item["low"]),
                        close=float(item["close"]),
                        volume=float(item.get("volume", 0)),
                        source="twelvedata"
                    ))
                return candles
            except Exception as e:
                await log_execution_event("DATA_FALLBACK", f"Twelve Data connection error ({e}). Falling back to Live Spot Market Feed", {"symbol": symbol, "error": str(e)})
                return await LiveSpotMarketProvider().fetch_candles(symbol, timeframe, limit)

class YahooFinanceProvider(BaseDataProvider):
    """Data provider fallback using public Yahoo Finance endpoints."""

    async def fetch_candles(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        ticker_map = {
            "XAU/USD": "GC=F",
            "XAG/USD": "SI=F",
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "USD/JPY": "JPY=X",
            "BTC/USD": "BTC-USD",
            "ETH/USD": "ETH-USD",
            "US30": "^DJI"
        }
        spec = get_symbol_spec(symbol)
        ticker = ticker_map.get(spec.symbol, "GC=F")

        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "1d": "1d"}
        interval = interval_map.get(timeframe.lower(), "5m")

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval={interval}&range=5d"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    await log_execution_event("DATA_FALLBACK", f"Yahoo Finance returned status {resp.status_code}. Falling back to synthetic mock data", {"symbol": symbol})
                    return await MockDataProvider().fetch_candles(symbol, timeframe, limit)

                data = resp.json()
                result = data["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                quote = result["indicators"]["quote"][0]

                all_candles: List[Candle] = []
                for idx in range(len(timestamps)):
                    ts = timestamps[idx]
                    o = quote["open"][idx]
                    h = quote["high"][idx]
                    l = quote["low"][idx]
                    c = quote["close"][idx]
                    v = quote.get("volume", [0] * len(timestamps))[idx]

                    if ts is None or o is None or c is None or h is None or l is None:
                        continue

                    ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    all_candles.append(Candle(
                        symbol=spec.symbol,
                        timeframe=timeframe,
                        timestamp=ts_dt,
                        open=round(float(o), spec.quote_precision),
                        high=round(float(h), spec.quote_precision),
                        low=round(float(l), spec.quote_precision),
                        close=round(float(c), spec.quote_precision),
                        volume=float(v or 0),
                        source="yahoo"
                    ))

                valid_candles = all_candles[-limit:] if len(all_candles) >= limit else all_candles
                if not valid_candles:
                    await log_execution_event("DATA_FALLBACK", "Yahoo Finance returned 0 valid candles. Falling back to synthetic mock data", {"symbol": symbol})
                    return await MockDataProvider().fetch_candles(symbol, timeframe, limit)
                return valid_candles
            except Exception as e:
                await log_execution_event("DATA_FALLBACK", f"Yahoo Finance error ({e}). Falling back to synthetic mock data", {"symbol": symbol, "error": str(e)})
                return await MockDataProvider().fetch_candles(symbol, timeframe, limit)


class BinanceSpotProvider(BaseDataProvider):
    """Direct high-frequency real-time Spot market data provider."""

    async def fetch_candles(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        spec = get_symbol_spec(symbol)
        pair_map = {
            "XAU/USD": "PAXGUSDT",  # 1:1 Spot Gold in USD matching TradingView OANDA:XAUUSD
            "BTC/USD": "BTCUSDT",
            "ETH/USD": "ETHUSDT",
            "EUR/USD": "EURUSDT",
            "GBP/USD": "GBPUSDT"
        }
        binance_symbol = pair_map.get(spec.symbol)
        if not binance_symbol:
            return await YahooFinanceProvider().fetch_candles(symbol, timeframe, limit)

        tf_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h", "1d": "1d"
        }
        interval = tf_map.get(timeframe.lower(), "5m")
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={interval}&limit={limit}"

        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return await YahooFinanceProvider().fetch_candles(symbol, timeframe, limit)

                data = resp.json()
                candles: List[Candle] = []
                for k in data:
                    ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc)
                    candles.append(Candle(
                        symbol=spec.symbol,
                        timeframe=timeframe,
                        timestamp=ts,
                        open=round(float(k[1]), spec.quote_precision),
                        high=round(float(k[2]), spec.quote_precision),
                        low=round(float(k[3]), spec.quote_precision),
                        close=round(float(k[4]), spec.quote_precision),
                        volume=round(float(k[5]), 2),
                        source="binance_spot"
                    ))
                return candles
            except Exception as e:
                await log_execution_event("DATA_FALLBACK", f"Binance Spot error ({e}). Falling back to Yahoo Finance", {"symbol": symbol, "error": str(e)})
                return await YahooFinanceProvider().fetch_candles(symbol, timeframe, limit)

class LiveSpotMarketProvider(BaseDataProvider):
    """
    Hybrid multi-source real-time Spot Market Data Provider.
    Routes Gold & Crypto to instant Binance Spot feeds (PAXG, BTC, ETH) matching TradingView 1:1,
    and Forex/Indices to Yahoo Finance / FX spot feeds.
    """
    def __init__(self):
        self.binance = BinanceSpotProvider()
        self.yahoo = YahooFinanceProvider()

    async def fetch_candles(
        self,
        symbol: str = "XAU/USD",
        timeframe: str = "5m",
        limit: int = 100
    ) -> List[Candle]:
        spec = get_symbol_spec(symbol)
        if spec.symbol in ["XAU/USD", "BTC/USD", "ETH/USD"]:
            candles = await self.binance.fetch_candles(symbol, timeframe, limit)
            if candles:
                return candles
        return await self.yahoo.fetch_candles(symbol, timeframe, limit)

def get_data_provider(provider_type: str = "yfinance", api_key: str = "") -> BaseDataProvider:
    """Factory method to get instances of Data Provider."""
    p_type = provider_type.lower()
    if p_type == "twelvedata" and api_key:
        return TwelveDataProvider(api_key=api_key)
    elif p_type == "mock":
        return MockDataProvider()
    else:
        return LiveSpotMarketProvider()

