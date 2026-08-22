from fastapi import APIRouter, Query, Body, HTTPException
from typing import Dict, Any, List

from app.execution.manager import execution_manager
from app.news.filter import news_filter
from app.broker.paper import paper_broker

router = APIRouter(prefix="/api/execution", tags=["Execution & Broker Engine"])

@router.get("/status")
async def get_execution_status():
    """Get current broker execution engine status, account metrics, and safety interlocks."""
    return await execution_manager.get_execution_status()

@router.post("/mode")
async def set_execution_mode(payload: Dict[str, str] = Body(...)):
    """Set execution mode: PAPER_TRADING, OANDA, MT5, DISABLED."""
    mode = payload.get("mode", "PAPER_TRADING")
    active_mode = execution_manager.set_execution_mode(mode)
    return {"mode": active_mode}

@router.post("/kill-switch")
async def toggle_kill_switch(payload: Dict[str, bool] = Body(default={})):
    """Toggle Emergency Kill-Switch."""
    active = payload.get("active", None)
    status = execution_manager.toggle_kill_switch(active)
    if status:
        # If kill switch activated, immediately close all open positions
        await execution_manager.close_all_positions()
    return {"is_kill_switch_active": status}

@router.get("/positions")
async def get_open_positions():
    """Get active open trade positions."""
    adapter = execution_manager.get_active_adapter()
    positions = await adapter.get_positions()
    return {"positions": positions}

@router.post("/positions/{position_id}/close")
async def close_position(position_id: str, payload: Dict[str, float] = Body(default={})):
    """Manually close a specific paper/broker position."""
    adapter = execution_manager.get_active_adapter()
    exit_price = payload.get("exit_price", 3345.0)
    success = await adapter.close_position(position_id, exit_price)
    if not success:
        raise HTTPException(status_code=404, detail="Position ID not found or already closed.")
    return {"status": "CLOSED", "position_id": position_id}

@router.post("/close-all")
async def close_all_positions():
    """Emergency close all open paper and broker positions."""
    closed_count = await execution_manager.close_all_positions()
    return {"status": "SUCCESS", "closed_positions_count": closed_count}

@router.get("/news")
async def get_news_events():
    """Get economic calendar news filter status and upcoming high-impact events."""
    return {
        "is_blackout_active": news_filter.is_blackout_active(),
        "events": news_filter.get_upcoming_events()
    }
