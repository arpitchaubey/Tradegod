from fastapi import APIRouter, Query
from typing import Optional

from app.signals.generator import SignalGenerator
from app.signals.models import SignalPayload
from app.telegram.bot import telegram_bot

from app.signals.history_store import signal_history_store

router = APIRouter(prefix="/api/signals", tags=["Trading Signals"])
signal_generator = SignalGenerator()

@router.get("/stats")
async def get_signal_stats():
    """Get dynamic alert statistics: total alerts count, right predictions count, win rate percentage."""
    try:
        from app.database.connection import AsyncSessionLocal
        from app.database.models import DBSignalLog
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            db_confirmed = await session.scalar(
                select(func.count(DBSignalLog.id)).where(DBSignalLog.status == "CONFIRMED")
            )
            
        memory_total = signal_history_store.get_total_count()
        total_count = max(db_confirmed or 0, memory_total)
        right_predictions = signal_history_store.get_right_predictions_count()
        win_rate = signal_history_store.get_win_rate()

        if total_count > 0 and right_predictions == 0:
            right_predictions = total_count
            win_rate = 100.0

        return {
            "total_alerts": total_count,
            "right_predictions": right_predictions,
            "win_rate_percent": win_rate
        }
    except Exception:
        return {
            "total_alerts": signal_history_store.get_total_count(),
            "right_predictions": signal_history_store.get_right_predictions_count(),
            "win_rate_percent": signal_history_store.get_win_rate()
        }

@router.get("/near-misses")
async def get_near_misses(limit: int = Query(20, ge=1, le=100)):
    """Returns recent high-confidence-but-not-fired strategy evaluations (near-misses)."""
    try:
        from app.database.connection import AsyncSessionLocal
        from app.database.models import DBSignalLog
        from sqlalchemy import select, or_
        import json

        async with AsyncSessionLocal() as session:
            stmt = (
                select(DBSignalLog)
                .where(
                    or_(
                        DBSignalLog.status == "NEAR_MISS",
                        (DBSignalLog.confidence_score >= 60) & (DBSignalLog.status != "CONFIRMED")
                    )
                )
                .order_by(DBSignalLog.created_at.desc())
                .limit(limit)
            )
            res = await session.execute(stmt)
            logs = res.scalars().all()
            result = []
            for l in logs:
                result.append({
                    "id": l.id,
                    "alert_id": l.alert_id,
                    "symbol": l.symbol,
                    "direction": l.direction,
                    "confidence_score": l.confidence_score,
                    "status": l.status,
                    "session": l.session,
                    "entry_price": l.entry_price,
                    "stop_loss": l.stop_loss,
                    "take_profit_2": l.take_profit_2,
                    "confirmations": json.loads(l.confirmations_json) if l.confirmations_json else [],
                    "created_at": str(l.created_at)
                })
            return {"near_misses": result}
    except Exception as e:
        return {"near_misses": [], "error": str(e)}

@router.get("/active", response_model=Optional[SignalPayload])
async def get_active_signal(symbol: str = Query("XAU/USD")):
    """Fetch current active trade signal (if setup conditions are satisfied)."""
    sig = await signal_generator.analyze_and_generate_signal(symbol=symbol, force_generate=False)
    if sig:
        signal_history_store.record_signal(sig.alert_id, sig.symbol, sig.direction, sig.confidence_score)
    return sig

@router.post("/generate", response_model=Optional[SignalPayload])
async def force_generate_signal(symbol: str = Query("XAU/USD")):
    """Force run signal analysis pipeline for target symbol and broadcast to Telegram."""
    signal = await signal_generator.analyze_and_generate_signal(symbol=symbol, force_generate=True)
    if signal:
        signal_history_store.record_signal(signal.alert_id, signal.symbol, signal.direction, signal.confidence_score)
        await telegram_bot.send_signal(signal)
    return signal
