from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
import json
import logging
from app.config import settings
from app.database.models import Base, DBUser, DBStrategy, DBBrokerAccount

logger = logging.getLogger(__name__)

# Normalize DATABASE_URL for async SQLAlchemy
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def seed_initial_data(session: AsyncSession):
    """Automatically seeds default user, active strategy, and paper account if database is fresh."""
    try:
        # Check if users exist
        res = await session.execute(select(DBUser))
        user = res.scalars().first()
        if not user:
            from app.auth.security import hash_password
            user = DBUser(
                id=1,
                email="trader@tradegod.ai",
                full_name="Trader Account",
                hashed_password=hash_password("password123"),
                plan_tier="PRO",
                avatar_url="https://ui-avatars.com/api/?name=Trader+Account&background=2563eb&color=fff"
            )
            session.add(user)
            await session.commit()
            logger.info("Default user trader@tradegod.ai seeded successfully.")

        # Check if strategy exists
        strat_res = await session.execute(select(DBStrategy).where(DBStrategy.user_id == 1))
        strat = strat_res.scalars().first()
        if not strat:
            from app.strategy.schemas import get_default_gold_strategy
            default_strat = get_default_gold_strategy()
            rules_dict = [r.model_dump() for r in default_strat.rules]
            
            strat = DBStrategy(
                user_id=1,
                name=default_strat.name,
                description="Default Gold 5M Breakout & Retest Strategy",
                raw_prompt="Buy XAU/USD when 1H EMA20 > EMA50 and 5M RSI > 55 with 1:2 R:R",
                rules_json=json.dumps(rules_dict),
                is_active=1
            )
            session.add(strat)
            await session.commit()
            logger.info("Default Gold strategy seeded successfully.")

        # Check paper broker account
        broker_res = await session.execute(select(DBBrokerAccount).where(DBBrokerAccount.user_id == 1))
        broker = broker_res.scalars().first()
        if not broker:
            broker = DBBrokerAccount(
                user_id=1,
                broker_name="Paper Trading",
                account_id="PAPER_10000",
                balance=10000.0,
                equity=10000.0,
                is_active=1
            )
            session.add(broker)
            await session.commit()
            logger.info("Default paper broker account seeded successfully.")
    except Exception as e:
        logger.warning(f"Initial data seeding notice: {e}")

async def init_db():
    """Initializes database tables and seeds default data on startup with automatic SQLite fallback."""
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)
    except Exception as e:
        logger.warning(f"Database connection to {db_url[:30]}... failed ({e}). Falling back to local SQLite database.")
        fallback_url = "sqlite+aiosqlite:///./tradegod.db"
        engine = create_async_engine(fallback_url, echo=False)
        AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)

async def get_db():
    """Async session generator for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session
