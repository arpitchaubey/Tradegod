import ssl
import json
import logging
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.config import settings
from app.database.models import Base, DBUser, DBStrategy, DBBrokerAccount

logger = logging.getLogger(__name__)

def normalize_database_url(raw_url: str) -> tuple[str, dict]:
    """
    Normalizes a DATABASE_URL for async SQLAlchemy with asyncpg or aiosqlite.
    Translates postgres/sqlite schemes, strips unsupported query arguments (like 'sslmode', 
    'channel_binding') that cause asyncpg.connect() unexpected keyword argument errors,
    and configures SSL context via connect_args.
    """
    connect_args = {}
    if not raw_url or not raw_url.strip():
        return "sqlite+aiosqlite:///./tradegod.db", connect_args

    url = raw_url.strip()

    # Translate URL schemes for async drivers
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    if "postgresql+asyncpg://" in url:
        parsed = urlparse(url)
        query_dict = dict(parse_qsl(parsed.query))

        # asyncpg.connect() does not accept 'sslmode' or 'channel_binding' as raw URL parameters
        sslmode = query_dict.pop("sslmode", None)
        ssl_param = query_dict.pop("ssl", None)
        query_dict.pop("channel_binding", None)

        # Retain only valid asyncpg connect keyword parameters in the query string
        valid_asyncpg_kwargs = {
            "command_timeout", "statement_cache_size", "max_cached_statement_lifetime",
            "max_cacheable_statement_size", "target_session_attrs", "krbsrvname", "gsslib",
            "server_settings", "timeout"
        }
        filtered_query = {k: v for k, v in query_dict.items() if k in valid_asyncpg_kwargs}

        ssl_val = (ssl_param or sslmode or "").lower()
        if ssl_val in ["disable", "false", "0", "no", "off"]:
            connect_args["ssl"] = False
        elif ssl_val in ["require", "prefer", "allow", "verify-ca", "verify-full", "true", "1", "yes"]:
            ctx = ssl.create_default_context()
            if ssl_val in ["require", "prefer", "allow"]:
                # Cloud PostgreSQL providers (Render, Neon, Supabase, Railway) use pooled or managed certs
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ctx
        else:
            # If no sslmode specified, check if connecting to a remote host (not localhost)
            hostname = parsed.hostname or ""
            if hostname and hostname not in ("localhost", "127.0.0.1", "::1"):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                connect_args["ssl"] = ctx

        new_query = urlencode(filtered_query)
        url = urlunparse(parsed._replace(query=new_query))

    return url, connect_args

class SessionMakerProxy:
    """Proxy that dynamically delegates to an active async_sessionmaker, allowing runtime engine fallback."""
    def __init__(self, maker):
        self._maker = maker

    def set_maker(self, maker):
        self._maker = maker

    def __call__(self, *args, **kwargs):
        return self._maker(*args, **kwargs)

    def begin(self, *args, **kwargs):
        return self._maker.begin(*args, **kwargs)

# Initialize engine and sessionmaker
db_url, db_connect_args = normalize_database_url(settings.database_url)
engine = create_async_engine(db_url, connect_args=db_connect_args, echo=False)
_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
AsyncSessionLocal = SessionMakerProxy(_session_maker)

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
                mode="PAPER_TRADING",
                balance=10000.0,
                equity=10000.0
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
        AsyncSessionLocal.set_maker(async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession))
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)

async def get_db():
    """Async session generator for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session
