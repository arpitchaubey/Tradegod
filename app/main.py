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
from app.api.routes_omni import router as omni_router
from app.telegram.bot import telegram_bot

from app.strategy.active_store import active_strategy_store
from app.bot.worker import omni_bot_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    await init_db()
    await active_strategy_store.load_from_db()
    telegram_bot.setup()
    await telegram_bot.start_polling()
    omni_bot_worker.start()
    yield
    # Shutdown lifecycle
    await omni_bot_worker.stop()
    await telegram_bot.stop_polling()

app = FastAPI(
    title=settings.app_name,
    description="XAU/USD & Multi-Instrument AI Trading Signal Engine API",
    version="1.0.0",
    lifespan=lifespan
)

raw_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-phi-snowy-59.vercel.app",
    "https://tradegod.vercel.app"
]
allowed_origins_list = list(set(raw_origins + default_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

app.include_router(market_router)
app.include_router(strategy_router)
app.include_router(signals_router)
app.include_router(backtest_router)
app.include_router(execution_router)
app.include_router(bot_router)
app.include_router(settings_router)
app.include_router(auth_router)
app.include_router(omni_router)

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

