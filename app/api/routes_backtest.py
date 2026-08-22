from fastapi import APIRouter, Query
from app.backtest.engine import BacktestEngine
from app.backtest.metrics import BacktestReport

router = APIRouter(prefix="/api/backtest", tags=["Backtesting Engine"])

@router.post("/run", response_model=BacktestReport)
async def run_backtest(
    symbol: str = Query("XAU/USD"),
    timeframe: str = Query("5m"),
    limit: int = Query(300, ge=50, le=1000)
):
    """Executes historical candle-by-candle strategy backtest simulation."""
    engine = BacktestEngine(initial_balance=10000.0, risk_percent=1.0)
    report = await engine.run_backtest(symbol=symbol, timeframe=timeframe, candle_limit=limit)
    return report
