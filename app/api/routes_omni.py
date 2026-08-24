from fastapi import APIRouter, Query, HTTPException, Body, Path
from typing import Optional, Dict, Any, List

from app.data.historical import candle_buffer
from app.ai.omni_engine import omni_engine, OmniMarketMatrix, OmniFutureForecast
from app.indicators.choch_predictor import evaluate_choch_prediction, CHoCHPredictionReport
from app.learning.feedback_engine import feedback_engine
from app.ai.preferences import omni_preferences_store, OmniPreferences
from app.ai.forecast_history import forecast_history_store, ForecastHistoryItem

router = APIRouter(prefix="/api/omni", tags=["Omni AI Vision & Self-Learning Engine"])

@router.get("/preferences", response_model=OmniPreferences)
async def get_omni_preferences():
    """Returns active user preferences configured for Omni Engine & Bot."""
    return omni_preferences_store.get_preferences()

@router.post("/preferences", response_model=OmniPreferences)
async def update_omni_preferences(prefs: OmniPreferences = Body(...)):
    """Updates and persists user preferences for Omni Engine & Bot."""
    return omni_preferences_store.update_preferences(prefs)

@router.get("/market-matrix", response_model=OmniMarketMatrix)
async def get_omni_market_matrix(
    symbol: str = Query("XAU/USD"),
    timeframe: str = Query("5m")
):
    """
    Returns full-spectrum quantitative chart matrix:
    - Close-to-Close (C2C) Velocity & Acceleration
    - Volume Profiling & Order Flow (VWAP, RVOL, OBV, Delta)
    - Market Structure (BOS, CHoCH, Fair Value Gaps, Liquidity Sweeps)
    - Multi-Timeframe Alignment & Radar Ratings
    """
    try:
        tf_map = {"trend": "1h", "setup": "15m", "entry": timeframe}
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, tf_map, limit=120)
        matrix = await omni_engine.analyze_market_matrix(symbol, timeframe, tf_dfs)
        return matrix
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute Omni market matrix: {str(e)}")

@router.get("/choch-forecast", response_model=CHoCHPredictionReport)
async def get_choch_prediction(
    symbol: str = Query("XAU/USD")
):
    """
    Returns early warning Change of Character (CHoCH) trend reversal analysis
    and forward-looking market scenario transition probability maps.
    """
    try:
        tf_map = {"trend": "1h", "entry": "5m"}
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, tf_map, limit=120)
        df_1h = tf_dfs.get("1h", list(tf_dfs.values())[0])
        df_5m = tf_dfs.get("5m", list(tf_dfs.values())[0])
        report = evaluate_choch_prediction(df_1h, df_5m, symbol=symbol)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CHoCH forecast: {str(e)}")

@router.post("/predict", response_model=OmniFutureForecast)
async def generate_predictive_future_trade(
    symbol: str = Query("XAU/USD"),
    timeframe: str = Query("5m")
):
    """
    Generates actionable institutional Future Trade Projection with reachability analysis:
    - Direction (BUY / SELL / REVERSAL_WAIT / RANGE_WAIT)
    - Guaranteed Live Market Entry + Feasible Sniper Pullback Limit
    - Reachability Probability & Feasibility Rating
    - Win Probability Rating (0-100%)
    - Multi-Tier Profit Targets (TP1/TP2/TP3) matching user's min profit pips
    """
    try:
        tf_map = {"trend": "1h", "setup": "15m", "entry": timeframe}
        tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, tf_map, limit=120)
        forecast = await omni_engine.generate_future_trade_forecast(symbol, timeframe, tf_dfs)
        # Record into forecast history log
        forecast_history_store.record_forecast(forecast)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trade forecast: {str(e)}")

@router.get("/forecasts/history", response_model=List[ForecastHistoryItem])
async def get_forecast_history(symbol: Optional[str] = Query(None)):
    """Retrieves all past AI trade projection records with entries and targets."""
    return forecast_history_store.get_all(symbol=symbol)

@router.get("/forecasts/history/{forecast_id}", response_model=ForecastHistoryItem)
async def get_forecast_history_by_id(forecast_id: str = Path(...)):
    """Retrieves specific forecast projection by ID."""
    item = forecast_history_store.get_by_id(forecast_id)
    if not item:
        raise HTTPException(status_code=404, detail="Forecast record not found")
    return item

@router.delete("/forecasts/history/{forecast_id}")
async def delete_forecast_history_item(forecast_id: str = Path(...)):
    """Deletes a specific forecast from history."""
    deleted = forecast_history_store.delete_by_id(forecast_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Forecast record not found")
    return {"status": "success", "message": f"Forecast {forecast_id} deleted"}

@router.delete("/forecasts/history")
async def clear_forecast_history():
    """Clears all historical forecast projection records."""
    forecast_history_store.clear()
    return {"status": "success", "message": "Forecast history cleared"}

@router.get("/learning-stats")
async def get_self_learning_analytics():
    """
    Returns continuous self-learning feedback analytics:
    - Analyzed trade outcomes & post-mortems
    - Empirical win rates by trading session and market condition
    - Active dynamically auto-tuned strategy weights and parameter tuning history
    """
    return feedback_engine.get_learning_stats()

@router.post("/self-update")
async def trigger_self_learning_update():
    """
    Triggers an immediate autonomous recalibration of strategy weights and gates
    based on accumulated trade feedback history.
    """
    new_weights = feedback_engine.auto_tune_parameters()
    return {
        "status": "success",
        "message": f"Autonomous parameter self-tuning completed (Generation {new_weights.tuning_generation})",
        "active_weights": new_weights.model_dump()
    }
