from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database.connection import init_db
from app.api.routes_market import router as market_router
from app.api.routes_strategy import router as strategy_router
from app.api.routes_signals import router as signals_router
from app.api.routes_backtest import router as backtest_router
from app.api.routes_execution import router as execution_router
from app.api.routes_bot import router as bot_router
from app.api.routes_settings import router as settings_router
from app.api.routes_auth import router as auth_router
from app.telegram.bot import telegram_bot

from app.strategy.active_store import active_strategy_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    await init_db()
    await active_strategy_store.load_from_db()
    telegram_bot.setup()
    await telegram_bot.start_polling()
    yield
    # Shutdown lifecycle
    await telegram_bot.stop_polling()

app = FastAPI(
    title=settings.app_name,
    description="XAU/USD & Multi-Instrument AI Trading Signal Engine API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router)
app.include_router(strategy_router)
app.include_router(signals_router)
app.include_router(backtest_router)
app.include_router(execution_router)
app.include_router(bot_router)
app.include_router(settings_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.app_name,
        "default_symbol": settings.default_symbol,
        "execution_mode": settings.execution_mode,
        "version": "1.0.0",
        "docs_url": "/docs"
    }

