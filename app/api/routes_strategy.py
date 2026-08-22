from fastapi import APIRouter, Query, Body, HTTPException, Header, Depends
from typing import Dict, Any, List, Optional
import json
from sqlalchemy import select, update

from app.strategy.schemas import get_default_gold_strategy, StrategyDefinition
from app.strategy.parser import parse_natural_language_strategy
from app.strategy.engine import StrategyEngine
from app.data.historical import candle_buffer
from app.strategy.active_store import active_strategy_store
from app.database.connection import AsyncSessionLocal
from app.database.models import DBStrategy, DBUser
from app.api.routes_auth import get_current_user_from_header

router = APIRouter(prefix="/api/strategy", tags=["Strategy Engine"])

@router.get("/current")
async def get_current_strategy():
    """Get active default strategy configuration."""
    return active_strategy_store.get_strategy().model_dump()

@router.get("/list")
async def list_saved_strategies(user: DBUser = Depends(get_current_user_from_header)):
    """Get saved strategies for the authenticated user."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBStrategy).where(DBStrategy.user_id == user.id).order_by(DBStrategy.created_at.desc())
        res = await session.execute(stmt)
        strats = res.scalars().all()
        result = []
        for s in strats:
            rules_data = json.loads(s.rules_json) if s.rules_json else {}
            result.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "raw_prompt": s.raw_prompt,
                "is_active": s.is_active,
                "strategy": rules_data,
                "created_at": str(s.created_at)
            })
        return {"strategies": result}

@router.post("/parse")
async def parse_strategy_text(
    payload: Dict[str, Any] = Body(...),
    user: DBUser = Depends(get_current_user_from_header)
):
    """Convert natural language English strategy prompt to structured JSON, set as active, and save to user's account."""
    prompt = payload.get("text", "")
    name = payload.get("name")
    strategy = parse_natural_language_strategy(prompt)
    if name:
        strategy.name = name
    strategy.raw_prompt = prompt

    await active_strategy_store.save_to_db(strategy, raw_prompt=prompt, user_id=user.id)

    # Broadcast updated strategy via Telegram
    rules_text = "\n".join([f"• {r.description}" for r in strategy.rules])
    msg = (
        f"🧠 *TRADEGOD AI — ACTIVE STRATEGY UPDATED*\n\n"
        f"User: *{user.full_name}*\n"
        f"Strategy Name: *{strategy.name}*\n"
        f"Symbol: *{strategy.symbol}*\n"
        f"Timeframes: *{strategy.timeframes.get('entry', '5m')}* (Entry) / *{strategy.timeframes.get('higher', '1h')}* (Higher)\n"
        f"Risk/Reward Ratio: *1:{strategy.risk_reward_ratio}*\n\n"
        f"📋 *Parsed Strategy Rules:*\n{rules_text}"
    )
    from app.telegram.bot import telegram_bot
    await telegram_bot.send_text_message(msg)

    return strategy.model_dump()

@router.post("/save")
async def save_strategy(
    payload: Dict[str, Any] = Body(...),
    user: DBUser = Depends(get_current_user_from_header)
):
    """Save custom strategy definition to database for target user."""
    name = payload.get("name", "Custom User Strategy")
    prompt = payload.get("prompt", "")
    strat_data = payload.get("strategy")

    if strat_data:
        strategy = StrategyDefinition(**strat_data)
        strategy.name = name
        strategy.raw_prompt = prompt
    else:
        strategy = parse_natural_language_strategy(prompt)
        strategy.name = name
        strategy.raw_prompt = prompt

    await active_strategy_store.save_to_db(strategy, raw_prompt=prompt, user_id=user.id)
    return {"status": "saved", "strategy": strategy.model_dump()}

@router.post("/activate/{name}")
async def activate_saved_strategy(
    name: str,
    user: DBUser = Depends(get_current_user_from_header)
):
    """Activate a previously saved strategy by name for current user."""
    async with AsyncSessionLocal() as session:
        stmt = select(DBStrategy).where((DBStrategy.user_id == user.id) & (DBStrategy.name == name))
        res = await session.execute(stmt)
        db_strat = res.scalar_one_or_none()
        if not db_strat or not db_strat.rules_json:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # Deactivate previous active strategies for user
        await session.execute(update(DBStrategy).where(DBStrategy.user_id == user.id).values(is_active=False))
        db_strat.is_active = True
        await session.commit()

        data = json.loads(db_strat.rules_json)
        data["raw_prompt"] = db_strat.raw_prompt
        strategy = StrategyDefinition(**data)
        await active_strategy_store.save_to_db(strategy, raw_prompt=db_strat.raw_prompt or "", user_id=user.id)
        return {"status": "activated", "strategy": strategy.model_dump()}

@router.post("/evaluate")
async def evaluate_strategy(symbol: str = Query("XAU/USD")):
    """Evaluate current strategy rules against live/historical market candles."""
    strategy = active_strategy_store.get_strategy()
    engine = StrategyEngine(strategy)
    tf_dfs = await candle_buffer.get_multi_timeframe_dfs(symbol, strategy.timeframes)
    res = engine.evaluate(tf_dfs)
    return res.model_dump()

