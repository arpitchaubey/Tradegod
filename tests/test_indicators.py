import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone

from app.indicators.trend import calculate_ema, calculate_sma, evaluate_trend_alignment
from app.indicators.momentum import calculate_rsi, calculate_macd
from app.indicators.volatility import calculate_atr
from app.indicators.structure import identify_support_resistance, detect_breakout

def create_synthetic_df(num_candles=100, start_price=3345.0, trend=0.5):
    records = []
    now = datetime.now(timezone.utc)
    price = start_price
    for i in range(num_candles):
        price += trend
        records.append({
            "timestamp": now + timedelta(minutes=5*i),
            "open": price - 0.2,
            "high": price + 1.0,
            "low": price - 0.5,
            "close": price,
            "volume": 500.0
        })
    return pd.DataFrame(records)

def test_ema_sma():
    df = create_synthetic_df(100)
    ema20 = calculate_ema(df, 20)
    sma50 = calculate_sma(df, 50)
    assert len(ema20) == 100
    assert len(sma50) == 100
    assert ema20.iloc[-1] > sma50.iloc[-1]

def test_rsi_macd_atr():
    df = create_synthetic_df(100)
    rsi = calculate_rsi(df, 14)
    macd, signal, hist = calculate_macd(df)
    atr = calculate_atr(df, 14)

    assert not rsi.empty
    assert 0 <= rsi.iloc[-1] <= 100
    assert not atr.empty

def test_structure_and_breakout():
    df = create_synthetic_df(100)
    supports, resistances = identify_support_resistance(df)
    assert isinstance(supports, list)
    assert isinstance(resistances, list)

    bo_info = detect_breakout(df)
    assert hasattr(bo_info, "is_breakout")
