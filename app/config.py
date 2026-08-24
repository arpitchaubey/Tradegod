import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Tradegod AI Signal Engine"
    default_symbol: str = "XAU/USD"
    default_data_provider: str = "spot"
    twelve_data_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_admin_ids: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./tradegod.db"
    default_risk_percent: float = 1.0
    max_daily_loss_percent: float = 2.0
    max_trades_per_day: int = 5
    max_open_positions: int = 3
    max_spread_pips: float = 5.0
    execution_mode: str = "PAPER_TRADING"
    broker_api_key: str = ""
    broker_account_id: str = ""
    news_filter_enabled: bool = True
    news_blackout_minutes: int = 15
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://frontend-phi-snowy-59.vercel.app,https://tradegod.vercel.app"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

