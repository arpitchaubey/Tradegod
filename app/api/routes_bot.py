from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.config import settings
from app.telegram.bot import telegram_bot

router = APIRouter(prefix="/api/bot", tags=["Bot Control"])

class BotConditionSettings(BaseModel):
    bot_active: bool = Field(default=True)
    default_lot_size: float = Field(default=0.10, ge=0.01, le=10.0)
    max_positions: int = Field(default=3, ge=1, le=10)
    max_risk_percent: float = Field(default=2.0, ge=0.5, le=10.0)
    execution_mode: str = Field(default="PAPER_TRADING")
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    notify_on_new_signal: bool = Field(default=True)
    notify_on_position_close: bool = Field(default=True)
    notify_on_news_blackout: bool = Field(default=True)
    notify_on_max_loss: bool = Field(default=True)
    min_confidence_score: int = Field(default=75, ge=50, le=100)
    min_risk_reward_ratio: float = Field(default=1.5, ge=1.0, le=5.0)
    include_ai_explanation: bool = Field(default=True)

# In-memory bot settings store
current_bot_settings = BotConditionSettings(
    telegram_bot_token=settings.telegram_bot_token,
    telegram_chat_id=settings.telegram_chat_id
)

@router.get("/settings")
async def get_bot_settings():
    """Retrieve current Telegram bot alert condition settings."""
    return {
        "settings": current_bot_settings.model_dump(),
        "is_connected": bool(current_bot_settings.telegram_bot_token and current_bot_settings.telegram_chat_id),
        "bot_active": current_bot_settings.bot_active
    }

@router.post("/toggle")
async def toggle_bot_active():
    """Toggle bot execution state (STOP / START)."""
    global current_bot_settings
    current_bot_settings.bot_active = not current_bot_settings.bot_active
    status_str = "ACTIVE & SCANNING" if current_bot_settings.bot_active else "STOPPED / PAUSED"

    # Send instant Telegram notification
    msg = (
        f"🚨 *TRADEGOD AI — BOT ENGINE STATUS CHANGE*\n\n"
        f"State: *{status_str}*\n"
        f"• Default Lot Size: *{current_bot_settings.default_lot_size} lots*\n"
        f"• Max Account Risk: *{current_bot_settings.max_risk_percent}%*\n"
        f"• Execution Adapter: *{current_bot_settings.execution_mode}*"
    )
    await telegram_bot.send_text_message(msg)

    return {
        "status": "success",
        "bot_active": current_bot_settings.bot_active,
        "message": f"Bot status switched to {status_str}"
    }

@router.post("/settings")
async def update_bot_settings(new_settings: BotConditionSettings):
    """Update Telegram bot alert condition settings."""
    global current_bot_settings
    current_bot_settings = new_settings

    # Update telegram bot instance settings
    telegram_bot.token = new_settings.telegram_bot_token
    telegram_bot.chat_id = new_settings.telegram_chat_id
    if new_settings.telegram_bot_token:
        telegram_bot.setup()

    # Send instant Telegram notification
    msg = (
        "⚡ *TRADEGOD AI — BOT PARAMETERS UPDATED*\n\n"
        f"• Bot Active: *{'YES (SCANNING)' if new_settings.bot_active else 'NO (HALTED)'}*\n"
        f"• Default Lot Size: *{new_settings.default_lot_size} lots*\n"
        f"• Max Open Positions: *{new_settings.max_positions}*\n"
        f"• Max Risk Per Trade: *{new_settings.max_risk_percent}%*\n"
        f"• Min Confidence Score: *{new_settings.min_confidence_score}%*\n"
        f"• Min Risk/Reward Ratio: *1:{new_settings.min_risk_reward_ratio}*\n"
        f"• Execution Mode: *{new_settings.execution_mode}*"
    )
    await telegram_bot.send_text_message(msg)

    return {
        "status": "success",
        "message": "Bot alert conditions updated successfully",
        "settings": current_bot_settings.model_dump()
    }

@router.post("/test-alert")
async def send_test_alert():
    """Send an instant test notification message via Telegram Bot."""
    if not current_bot_settings.telegram_bot_token or not current_bot_settings.telegram_chat_id:
        # Fallback test confirmation if credentials not configured
        return {
            "status": "mock_sent",
            "message": "Test alert simulated (Telegram Token or Chat ID not configured)."
        }

    url = f"https://api.telegram.org/bot{current_bot_settings.telegram_bot_token}/sendMessage"
    msg = (
        "⚡ *TRADEGOD AI BOT — TEST NOTIFICATION*\n\n"
        "✅ Telegram Bot connection is *ACTIVE*!\n"
        "• Instrument: *XAU/USD*\n"
        "• Alert Triggers: Active\n"
        "• Min Confidence: *" + str(current_bot_settings.min_confidence_score) + "%*\n"
        "• Min R:R Ratio: *1:" + str(current_bot_settings.min_risk_reward_ratio) + "*\n\n"
        "Your Bot Control Panel conditions are live and configured."
    )
    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json={
                "chat_id": current_bot_settings.telegram_chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            })
            if resp.status_code == 200:
                return {"status": "sent", "message": "Test alert sent successfully to Telegram!"}
            else:
                return {"status": "error", "message": f"Telegram API returned {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to send Telegram alert: {str(e)}"}
