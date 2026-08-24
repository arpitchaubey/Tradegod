from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Optional
from app.backtest.engine import BacktestEngine
from app.backtest.metrics import BacktestReport
from app.backtest.history_store import backtest_history_store, BacktestHistoryItem
from app.ai.preferences import omni_preferences_store

router = APIRouter(prefix="/api/backtest", tags=["Backtesting Engine"])

@router.post("/run", response_model=BacktestReport)
async def run_backtest(
    symbol: str = Query("XAU/USD"),
    timeframe: str = Query("5m"),
    limit: int = Query(300, ge=50, le=1000),
    candle_limit: Optional[int] = Query(None)
):
    """Executes historical candle-by-candle strategy backtest simulation and records to history."""
    eff_limit = candle_limit or limit
    user_prefs = omni_preferences_store.get_preferences()
    engine = BacktestEngine(
        initial_balance=10000.0,
        risk_percent=user_prefs.max_risk_percent
    )
    report = await engine.run_backtest(symbol=symbol, timeframe=timeframe, candle_limit=eff_limit)
    backtest_history_store.record_backtest(
        symbol=symbol,
        timeframe=timeframe,
        candle_limit=eff_limit,
        report=report
    )
    return report


@router.get("/history", response_model=List[BacktestHistoryItem])
async def get_backtest_history(symbol: Optional[str] = Query(None)):
    """Retrieves all past backtest execution runs with performance metrics."""
    return backtest_history_store.get_all(symbol=symbol)

@router.get("/history/{history_id}", response_model=BacktestHistoryItem)
async def get_backtest_history_by_id(history_id: str = Path(...)):
    """Retrieves specific backtest run report by ID."""
    item = backtest_history_store.get_by_id(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return item

@router.delete("/history/{history_id}")
async def delete_backtest_history_item(history_id: str = Path(...)):
    """Deletes a specific backtest run from history."""
    deleted = backtest_history_store.delete_by_id(history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return {"status": "success", "message": f"Backtest {history_id} deleted"}

@router.delete("/history")
async def clear_backtest_history():
    """Clears all historical backtest logs."""
    backtest_history_store.clear()
    return {"status": "success", "message": "Backtesting history cleared"}
