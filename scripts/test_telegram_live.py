import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.telegram.bot import telegram_bot

async def main():
    print("Initializing Telegram bot setup...")
    telegram_bot.setup()
    print("Starting Telegram live polling...")
    await telegram_bot.start_polling()
    print("Sending welcome message to chat...")
    await telegram_bot.send_text_message("⚡ *TradeGod AI Telegram Bot is LIVE!* Commands like /status, /help, /stop are active and ready.")
    print("Waiting 10 seconds for live updates...")
    await asyncio.sleep(10)
    await telegram_bot.stop_polling()

if __name__ == "__main__":
    asyncio.run(main())
