import pytest
from app.data.symbols import get_symbol_spec, list_supported_symbols, DEFAULT_SYMBOL
from app.data.provider import MockDataProvider
from app.data.normalizer import normalize_candles_df

@pytest.mark.asyncio
async def test_symbol_specs():
    gold_spec = get_symbol_spec("XAU/USD")
    assert gold_spec.symbol == "XAU/USD"
    assert gold_spec.contract_size == 100.0
    assert gold_spec.default_timeframes["entry"] == "5m"

    eur_spec = get_symbol_spec("EUR/USD")
    assert eur_spec.symbol == "EUR/USD"
    assert eur_spec.contract_size == 100000.0

    all_symbols = list_supported_symbols()
    assert len(all_symbols) >= 5
    assert any(s["symbol"] == DEFAULT_SYMBOL for s in all_symbols)

@pytest.mark.asyncio
async def test_mock_data_provider():
    provider = MockDataProvider()
    candles = await provider.fetch_candles("XAU/USD", timeframe="5m", limit=50)
    assert len(candles) == 50
    assert candles[0].open > 0
    assert candles[0].symbol == "XAU/USD"

    df = normalize_candles_df(candles)
    assert len(df) == 50
    assert "close" in df.columns
    assert "timestamp" in df.columns
