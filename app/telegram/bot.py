import logging
from typing import Optional
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.data.historical import candle_buffer
from app.signals.models import SignalPayload
from app.signals.generator import SignalGenerator
from app.telegram.formatter import format_telegram_signal, format_status_message
from app.data.symbols import list_supported_symbols

logger = logging.getLogger("telegram_bot")

class TelegramBot:
    """Telegram Bot Controller."""

    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.app: Optional[Application] = None
        self.signal_generator = SignalGenerator()
        self.active_symbol = settings.default_symbol

    def setup(self):
        if not self.token:
            logger.info("No TELEGRAM_BOT_TOKEN provided. Telegram Bot running in mock/disabled mode.")
            return

        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("symbol", self.cmd_symbol))
        self.app.add_handler(CommandHandler("analyze", self.cmd_analyze))
        self.app.add_handler(CommandHandler("symbols", self.cmd_symbols))
        self.app.add_handler(CommandHandler("killswitch", self.cmd_killswitch))
        self.app.add_handler(CommandHandler("positions", self.cmd_positions))
        self.app.add_handler(CommandHandler("closeall", self.cmd_closeall))
        self.app.add_handler(CommandHandler("stop", self.cmd_stop))
        self.app.add_handler(CommandHandler("mode", self.cmd_mode))
        self.app.add_handler(CommandHandler("nearmisses", self.cmd_nearmisses))
        self.app.add_handler(CommandHandler("backtest", self.cmd_backtest))
        self.app.add_handler(CommandHandler("strategy", self.cmd_strategy))

    async def start_polling(self):
        """Starts live polling for incoming Telegram commands and messages in background."""
        if not self.app or not self.token:
            logger.info("Telegram Bot token not provided or app not setup. Live command polling disabled.")
            return

        try:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=False)
            logger.info("⚡ Telegram Bot live polling started! Ready to process commands.")
        except Exception as e:
            logger.error(f"Failed to start Telegram Bot polling: {e}")

    async def stop_polling(self):
        """Cleanly stops Telegram Bot polling on application shutdown."""
        if self.app and self.app.updater and self.app.updater.running:
            try:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                logger.info("Telegram Bot polling stopped cleanly.")
            except Exception as e:
                logger.error(f"Error stopping Telegram Bot polling: {e}")

    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.execution.manager import execution_manager
        execution_manager.set_execution_mode("DISABLED")
        await update.message.reply_text("🛑 *TradeGod AI Trading Engine STOPPED.* (Execution set to DISABLED)", parse_mode="Markdown")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Welcome to *TRADE GOD — Quantitative Insights Bot*!\n\n"
            "I analyze XAU/USD and other instruments using deterministic strategy rules and AI explanations.\n"
            "Use /status to see current chart info, or /help to see all commands.",
            parse_mode="Markdown"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "🛠️ *TRADE GOD — Official Telegram Commands:*\n\n"
            "/start - Start Bot & receive welcome briefing\n"
            "/help - Show command list & usage guide\n"
            "/status - View price, ADX, regime & engine status\n"
            "/analyze [SYMBOL] - Run immediate signal analysis\n"
            "/symbol [SYMBOL] - Switch target instrument\n"
            "/symbols - List supported trading instruments\n"
            "/positions - View open trade positions with PnL\n"
            "/closeall - Emergency close all active positions\n"
            "/stop - Stop auto-trading execution engine\n"
            "/killswitch - Toggle emergency kill-switch\n"
            "/mode [PAPER_TRADING|OANDA|MT5|DISABLED] - Set mode\n"
            "/nearmisses - View recent near-miss evaluations\n"
            "/backtest [SYMBOL] - Run backtest simulation\n"
            "/strategy - Display active strategy rules"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chart_info = await candle_buffer.get_active_chart_info(self.active_symbol)
        msg = format_status_message(chart_info)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args:
            new_sym = context.args[0].upper()
            self.active_symbol = new_sym
            await update.message.reply_text(f"✅ Active symbol switched to *{self.active_symbol}*.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Current active symbol is *{self.active_symbol}*.", parse_mode="Markdown")

    async def cmd_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        syms = list_supported_symbols()
        lines = [f"• *{s['symbol']}*: {s['display_name']} ({s['category']})" for s in syms]
        msg = "📈 *Supported Instruments:*\n\n" + "\n".join(lines)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_killswitch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.execution.manager import execution_manager
        active = execution_manager.toggle_kill_switch()
        state_str = "🛑 ACTIVATED (Trading Halted & Positions Closed)" if active else "✅ DEACTIVATED (Trading Resumed)"
        await update.message.reply_text(f"🚨 *Emergency Kill-Switch:* {state_str}", parse_mode="Markdown")

    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.execution.manager import execution_manager
        adapter = execution_manager.get_active_adapter()
        positions = await adapter.get_positions()
        if not positions:
            await update.message.reply_text("📦 *No Open Positions.*", parse_mode="Markdown")
            return

        lines = []
        for p in positions:
            lines.append(
                f"• *{p['symbol']}* ({p['direction']}) - Lots: {p['size_lots']} | Entry: {p['entry_price']} | PnL: ${p.get('unrealized_pnl', 0.0):+.2f}"
            )
        msg = "💼 *Open Positions:*\n\n" + "\n".join(lines)
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_closeall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.execution.manager import execution_manager
        count = await execution_manager.close_all_positions()
        await update.message.reply_text(f"🧹 *Closed {count} open positions.*", parse_mode="Markdown")

    async def cmd_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.execution.manager import execution_manager
        if context.args:
            mode = context.args[0].upper()
            active_mode = execution_manager.set_execution_mode(mode)
            await update.message.reply_text(f"⚙️ Execution Mode set to: *{active_mode}*", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Current Execution Mode: *{execution_manager.mode}*", parse_mode="Markdown")

    async def cmd_nearmisses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            from app.database.connection import AsyncSessionLocal
            from app.database.models import DBSignalLog
            from sqlalchemy import select, or_
            async with AsyncSessionLocal() as session:
                stmt = select(DBSignalLog).where(
                    or_(DBSignalLog.status == "NEAR_MISS", (DBSignalLog.confidence_score >= 60) & (DBSignalLog.status != "CONFIRMED"))
                ).order_by(DBSignalLog.created_at.desc()).limit(5)
                res = await session.execute(stmt)
                logs = res.scalars().all()
                if not logs:
                    await update.message.reply_text("🔎 *No Near-Miss Signal Setups Recorded.*", parse_mode="Markdown")
                    return

                lines = []
                for l in logs:
                    lines.append(f"• *{l.symbol}* ({l.direction}) — Confidence: *{l.confidence_score}%* | Status: `{l.status}` | Session: `{l.session}`")
                msg = "👀 *Recent Near-Miss Setups:*\n\n" + "\n".join(lines)
                await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error fetching near-misses: {e}")

    async def cmd_backtest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sym = context.args[0].upper() if context.args else self.active_symbol
        await update.message.reply_text(f"⏳ Running backtest simulation for *{sym}*...", parse_mode="Markdown")
        from app.backtest.engine import BacktestEngine
        from app.strategy.active_store import active_strategy_store
        engine = BacktestEngine(active_strategy_store.get_strategy())
        report = await engine.run_backtest(symbol=sym, timeframe="5m", candle_limit=300)

        msg = (
            f"📊 *Backtest Simulation Results — {report.symbol}*\n\n"
            f"Evaluated Candles: *{report.total_candles}*\n"
            f"Total Trades: *{report.total_trades}*\n"
            f"Win Rate: *{report.win_rate_percent}%*\n"
            f"Profit Factor: *{report.profit_factor}*\n"
            f"Net Profit: *${report.net_profit:.2f}*\n"
            f"Max Drawdown: *{report.max_drawdown_percent}%*\n"
            f"Average Risk:Reward: *1:{report.average_r}*"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_strategy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from app.strategy.active_store import active_strategy_store
        strat = active_strategy_store.get_strategy()
        rules = "\n".join([f"• {r.description}" for r in strat.rules])
        msg = (
            f"🧠 *Active Strategy Definition*\n\n"
            f"Name: *{strat.name}*\n"
            f"Symbol: *{strat.symbol}*\n"
            f"Risk/Reward: *1:{strat.risk_reward_ratio}*\n"
            f"Stop Loss Method: *{strat.sl_method}*\n\n"
            f"📋 *Rules:*\n{rules}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sym = context.args[0].upper() if context.args else self.active_symbol
        await update.message.reply_text(f"🔍 Analyzing *{sym}* on 5M timeframe...", parse_mode="Markdown")
        signal = await self.signal_generator.analyze_and_generate_signal(sym, force_generate=True)
        if signal:
            msg = format_telegram_signal(signal)
            await update.message.reply_text(msg, parse_mode="Markdown")
            await self.send_signal(signal)
        else:
            await update.message.reply_text(f"⚪ *{sym} — NO TRADE SETUP*\nNo valid setup detected at this time.", parse_mode="Markdown")

    async def send_signal(self, signal: SignalPayload) -> bool:
        """Sends formatted signal message to configured Telegram Chat ID if filters pass."""
        if not self.token or not self.chat_id:
            logger.info("Telegram Bot token or chat ID not set. Skipping Telegram notification.")
            return False

        from app.api.routes_bot import current_bot_settings

        if not current_bot_settings.notify_on_new_signal:
            logger.info("Telegram signal alerts disabled in Bot Control Panel settings.")
            return False

        if signal.confidence_score < current_bot_settings.min_confidence_score:
            logger.info(
                f"Signal confidence score ({signal.confidence_score}%) is below configured min_confidence_score ({current_bot_settings.min_confidence_score}%). Skipping Telegram broadcast."
            )
            return False

        if signal.risk_reward_ratio < current_bot_settings.min_risk_reward_ratio:
            logger.info(
                f"Signal R:R ({signal.risk_reward_ratio}) is below configured min_risk_reward_ratio ({current_bot_settings.min_risk_reward_ratio}). Skipping Telegram broadcast."
            )
            return False

        msg = format_telegram_signal(signal)
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
                return False

    async def send_text_message(self, text: str) -> bool:
        """Sends custom text message to configured Telegram Chat ID."""
        if not self.token or not self.chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send Telegram text message: {e}")
                return False

telegram_bot = TelegramBot()
