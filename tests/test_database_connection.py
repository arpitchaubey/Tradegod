import pytest
import ssl
from app.database.connection import normalize_database_url, SessionMakerProxy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

def test_normalize_database_url_postgres_sslmode_require():
    raw_url = "postgresql://user:pass@ep-cool-123.aws.neon.tech/neondb?sslmode=require"
    url, connect_args = normalize_database_url(raw_url)
    
    assert "sslmode" not in url
    assert url.startswith("postgresql+asyncpg://")
    assert "ssl" in connect_args
    assert isinstance(connect_args["ssl"], ssl.SSLContext)
    # verify engine can be instantiated without raising schema/argument parse errors
    engine = create_async_engine(url, connect_args=connect_args, echo=False)
    assert engine is not None

def test_normalize_database_url_postgres_with_extra_query_params():
    raw_url = "postgres://user:pass@render-db.render.com:5432/tradegod?sslmode=require&channel_binding=disable"
    url, connect_args = normalize_database_url(raw_url)
    
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert url.startswith("postgresql+asyncpg://")
    assert "ssl" in connect_args
    assert isinstance(connect_args["ssl"], ssl.SSLContext)

def test_normalize_database_url_postgres_ssl_disable():
    raw_url = "postgresql+asyncpg://user:pass@localhost:5432/tradegod?sslmode=disable"
    url, connect_args = normalize_database_url(raw_url)
    
    assert "sslmode" not in url
    assert connect_args.get("ssl") is False

def test_normalize_database_url_sqlite():
    raw_url = "sqlite:///./tradegod.db"
    url, connect_args = normalize_database_url(raw_url)
    
    assert url == "sqlite+aiosqlite:///./tradegod.db"
    assert connect_args == {}

@pytest.mark.asyncio
async def test_session_maker_proxy():
    engine_1 = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    maker_1 = async_sessionmaker(engine_1, expire_on_commit=False, class_=AsyncSession)
    
    proxy = SessionMakerProxy(maker_1)
    
    async with proxy() as session:
        assert isinstance(session, AsyncSession)
        
    # Reconfigure
    engine_2 = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    maker_2 = async_sessionmaker(engine_2, expire_on_commit=False, class_=AsyncSession)
    proxy.set_maker(maker_2)
    
    async with proxy() as session:
        assert isinstance(session, AsyncSession)
