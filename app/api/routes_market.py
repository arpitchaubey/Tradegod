from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any

from app.data.symbols import list_supported_symbols, DEFAULT_SYMBOL
from app.data.historical import candle_buffer
from app.data.chart_info import ActiveChartInfo

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/symbols")
async def get_symbols():
    """List all supported instruments (XAU/USD default, Forex, Crypto, Indices)."""
    return {"default_symbol": DEFAULT_SYMBOL, "symbols": list_supported_symbols()}

@router.get("/chart-info", response_model=ActiveChartInfo)
async def get_active_chart_info(symbol: str = Query(DEFAULT_SYMBOL)):
    """Get active chart metadata (Symbol, Timeframe, Provider, Spread, Candle Count)."""
    return await candle_buffer.get_active_chart_info(symbol=symbol)

@router.get("/candles")
async def get_candles(
    symbol: str = Query(DEFAULT_SYMBOL),
    timeframe: str = Query("5m"),
    limit: int = Query(100, ge=1, le=1000),
    provider: Optional[str] = Query(None)
):
    """Get historical OHLC candles for interactive chart rendering."""
    df = await candle_buffer.get_candles_df(symbol=symbol, timeframe=timeframe, limit=limit, force_refresh=True)
    if not df.empty:
        df = df.iloc[-limit:]
    records = df.to_dict(orient="records")
    for r in records:
        if "timestamp" in r:
            r["timestamp"] = str(r["timestamp"])
    return {"symbol": symbol, "timeframe": timeframe, "count": len(records), "candles": records}

