import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from app.data.normalizer import Candle, normalize_candles_df
from app.indicators.trend import calculate_adx, evaluate_adx_gate
from app.indicators.structure import detect_breakout, BreakoutInfo
from app.data.provider import MockDataProvider

@pytest.mark.asyncio
async def test_mock_provider_synthetic_source_tag():
    """Verify that MockDataProvider tags all generated candles with source='synthetic'."""
    provider = MockDataProvider(seed=42)
    candles = await provider.fetch_candles("XAU/USD", timeframe="5m", limit=50)
    assert len(candles) == 50
    assert all(c.source == "synthetic" for c in candles)

    df = normalize_candles_df(candles)
    assert "source" in df.columns
    assert (df["source"] == "synthetic").all()

def test_adx_gate_calculation():
    """Verify ADX calculation and ranging vs trending market regime evaluation."""
    dates = [datetime.now(timezone.utc) - timedelta(minutes=5*i) for i in range(100)][::-1]
    # Strong upward trend data
    close_prices = [3000.0 + i * 2.5 for i in range(100)]
    high_prices = [p + 1.5 for p in close_prices]
    low_prices = [p - 1.5 for p in close_prices]

    df = pd.DataFrame({
        "timestamp": dates,
        "open": close_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": [1000.0] * 100
    })

    adx_series = calculate_adx(df, period=14)
    assert not adx_series.empty
    val, regime, passed = evaluate_adx_gate(df, adx_threshold=20.0)
    assert regime == "trending"
    assert passed is True
    assert val > 20.0

def test_breakout_anti_fakeout_confirmation():
    """Verify anti-fakeout confirmation requires close beyond ATR margin or two consecutive closes."""
    dates = [datetime.now(timezone.utc) - timedelta(minutes=5*i) for i in range(20)][::-1]
    # Create price data with clear swing high at index 10 (price 3350)
    prices = [3340.0] * 20
    prices[10] = 3350.0  # Swing high
    prices[18] = 3352.0  # Breakout close
    prices[19] = 3354.0  # Second consecutive close

    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.5 for p in prices],
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [1000.0] * 20
    })

    bo = detect_breakout(df, pip_threshold=0.2, atr_multiplier=0.1, swing_window=3)
    assert bo.is_breakout is True
    assert bo.direction == "long"
    assert bo.confirmed is True
