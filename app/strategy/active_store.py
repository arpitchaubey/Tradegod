import json
import logging
from typing import Optional
from sqlalchemy import select, update
from app.strategy.schemas import StrategyDefinition, get_default_gold_strategy
from app.database.connection import AsyncSessionLocal
from app.database.models import DBStrategy

logger = logging.getLogger(__name__)

class ActiveStrategyStore:
    """Singleton store for active user-configured strategy definition with database persistence."""

    def __init__(self):
        self._strategy: StrategyDefinition = get_default_gold_strategy()

    def update_strategy(self, strategy: StrategyDefinition):
        self._strategy = strategy

    def get_strategy(self) -> StrategyDefinition:
        return self._strategy

    async def load_from_db(self):
        """Loads the active strategy from SQLite database if present."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(DBStrategy).where(DBStrategy.is_active == True).order_by(DBStrategy.id.desc()).limit(1)
                res = await session.execute(stmt)
                db_strat = res.scalar_one_or_none()
                if db_strat and db_strat.rules_json:
                    data = json.loads(db_strat.rules_json)
                    data["raw_prompt"] = db_strat.raw_prompt
                    self._strategy = StrategyDefinition(**data)
                    logger.info(f"Loaded active strategy '{self._strategy.name}' from database.")
        except Exception as e:
            logger.warning(f"Could not load active strategy from DB, using default: {e}")

    async def save_to_db(self, strategy: StrategyDefinition, raw_prompt: str = "", user_id: int = 1):
        """Persists the strategy to SQLite database for specified user and marks it active."""
        self._strategy = strategy
        if raw_prompt:
            self._strategy.raw_prompt = raw_prompt

        try:
            async with AsyncSessionLocal() as session:
                # Deactivate previous active strategies for this user
                await session.execute(update(DBStrategy).where(DBStrategy.user_id == user_id).values(is_active=False))

                stmt = select(DBStrategy).where((DBStrategy.user_id == user_id) & (DBStrategy.name == strategy.name))
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()

                strat_dict = strategy.model_dump()
                rules_json = json.dumps(strat_dict)

                if existing:
                    existing.description = f"Risk/Reward 1:{strategy.risk_reward_ratio}, Symbol: {strategy.symbol}"
                    existing.raw_prompt = strategy.raw_prompt or raw_prompt
                    existing.rules_json = rules_json
                    existing.is_active = True
                else:
                    new_db = DBStrategy(
                        user_id=user_id,
                        name=strategy.name,
                        description=f"Risk/Reward 1:{strategy.risk_reward_ratio}, Symbol: {strategy.symbol}",
                        raw_prompt=strategy.raw_prompt or raw_prompt,
                        rules_json=rules_json,
                        is_active=True
                    )
                    session.add(new_db)
                await session.commit()
                logger.info(f"Persisted active strategy '{strategy.name}' for user_id={user_id} to database.")
        except Exception as e:
            logger.error(f"Failed to persist strategy to DB: {e}")

active_strategy_store = ActiveStrategyStore()

