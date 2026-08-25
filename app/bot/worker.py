import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.config import settings
from app.data.historical import candle_buffer
from app.data.symbols import list_supported_symbols
from app.ai.omni_engine import omni_engine
from app.telegram.bot import telegram_bot
from app.signals.deduplicator import deduplicator
from app.execution.manager import execution_manager
from app.learning.feedback_engine import feedback_engine
from app.news.filter import news_filter
from app.signals.history_store import signal_history_store

logger = logging.getLogger("omni_bot_worker")

class OmniBotWorker:
    """
    Autonomous Bot Orchestrator implementing the full system loop:
    [DATA] -> [BOT (configured by SETTINGS)] <-> [OMNI AI ENGINE] -> [TELEGRAM]
    """

    def __init__(self):
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.scan_interval_seconds: int = 15
        self.last_scan_time: Optional[datetime] = None
        self.scan_count: int = 0
        self.alerts_sent_count: int = 0
        self.last_prediction_result: Dict[str, Any] = {}

    def start(self):
        """Starts the autonomous background worker loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("⚡ Omni Bot Autonomous Orchestrator started in background!")

    async def stop(self):
        """Stops the autonomous background worker loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Omni Bot Autonomous Orchestrator stopped cleanly.")

    async def _run_loop(self):
        """Continuous background execution loop."""
        # Initial warmup delay
        await asyncio.sleep(3)
        while self._running:
            try:
                await self.execute_cycle()
            except Exception as e:
                logger.error(f"Error in Omni Bot execution cycle: {e}")
            
            await asyncio.sleep(self.scan_interval_seconds)

    async def execute_cycle(self):
        """Executes a single end-to-end data -> omni engine -> bot -> telegram cycle."""
        from app.ai.preferences import omni_preferences_store

        user_prefs = omni_preferences_store.get_preferences()
        self.last_scan_time = datetime.now(timezone.utc)
        self.scan_count += 1

        # 1. Check open positions against live market prices for TP/SL management & self-learning
        await self._manage_open_positions()

        # If bot is paused by user preference, skip new signal generation
        if not user_prefs.bot_active:
            return

        # 2. Check news blackout filter setting
        if user_prefs.notify_on_news_blackout and news_filter.is_blackout_active():
            logger.info("Scanning paused due to active high-impact economic news blackout.")
            return

        # 3. Check position limits from user settings
        adapter = execution_manager.get_active_adapter()
        positions = await adapter.get_positions()
        if len(positions) >= user_prefs.max_positions:
            return

        # 4. Scan primary active symbol (e.g. XAU/USD)
        active_symbol = telegram_bot.active_symbol or settings.default_symbol
        await self._evaluate_and_execute_symbol(active_symbol, user_prefs)


    async def _evaluate_and_execute_symbol(self, symbol: str, bot_settings: Any):
        """Pulls DATA, feeds to OMNI AI ENGINE, receives RESULT, and triggers BOT/TELEGRAM."""
        try:
            # 1. Fetch DATA (Multi-Timeframe Candles)
            entry_df = await candle_buffer.get_candles_df(symbol, "5m", limit=100)
            if entry_df is None or entry_df.empty:
                return

            last_close = float(entry_df["close"].iloc[-1])
            last_ts = str(entry_df["timestamp"].iloc[-1])

            # 2. Feed DATA to OMNI AI ENGINE -> Get RESULT (Future Trade Projection)
            projection = await omni_engine.predict_future_trade(symbol)
            self.last_prediction_result[symbol] = projection.model_dump()

            direction = projection.primary_direction.upper()
            win_prob = projection.win_probability_percent
            confidence = int(sum(projection.matrix_radar.values()) / max(1, len(projection.matrix_radar)))

            # Check if setup is tradeable
            if direction not in ["BUY", "SELL"]:
                return

            # 3. Filter by User SETTINGS PREFERENCE
            if win_prob < bot_settings.min_confidence_score:
                return
            if projection.risk_reward_ratio < bot_settings.min_risk_reward_ratio:
                return

            # 4. Deduplicate (Avoid re-alerting the exact same candle setup)
            alert_id = deduplicator.generate_alert_id(symbol, "5m", direction, last_ts)
            if deduplicator.is_duplicate(alert_id):
                return

            deduplicator.mark_as_sent(alert_id)
            self.alerts_sent_count += 1
            signal_history_store.increment_total_count()

            # 5. BOT Execution: Place Order (Paper / Live Broker)
            entry_price = projection.entry_zone.get("ideal", last_close)
            sl_price = projection.stop_loss
            tp1_price = projection.take_profit_1
            tp2_price = projection.take_profit_2
            tp3_price = projection.take_profit_3

            trade_position = await adapter_place_position(
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                stop_loss=sl_price,
                take_profit_1=tp1_price,
                take_profit_2=tp2_price,
                lot_size=bot_settings.default_lot_size,
                alert_id=alert_id
            )

            # 6. Broadcast rich Omni AI signal alert to TELEGRAM
            if bot_settings.notify_on_new_signal and telegram_bot.token and telegram_bot.chat_id:
                drivers_summary = "\n".join([f"• {d}" for d in projection.institutional_drivers[:3]])
                tele_msg = (
                    f"🎯 *TRADEGOD OMNI AI — NEW TRADE PROJECTION*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📈 *Symbol:* `{symbol}` (5M Matrix)\n"
                    f"⚡ *Action:* *{direction} LIMIT / PULLBACK*\n"
                    f"🎯 *Entry Zone:* `${entry_price:.2f}`\n"
                    f"🛑 *Stop Loss:* `${sl_price:.2f}`\n"
                    f"🏆 *Take Profit 1:* `${tp1_price:.2f}`\n"
                    f"🏆 *Take Profit 2:* `${tp2_price:.2f}`\n"
                    f"🏆 *Take Profit 3:* `${tp3_price:.2f}`\n"
                    f"⚖️ *Risk / Reward:* `1:{projection.risk_reward_ratio:.1f}`\n"
                    f"📊 *Win Probability:* `{win_prob}%` (Score: `{confidence}/100`)\n"
                    f"🔄 *CHoCH Risk:* `{projection.choch_risk}`\n"
                    f"📦 *Position Size:* `{bot_settings.default_lot_size} Lots`\n\n"
                    f"🧠 *Institutional Drivers:*\n"
                    f"{drivers_summary}\n\n"
                    f"⚙️ *Execution Mode:* `{bot_settings.execution_mode}`\n"
                    f"🆔 `{alert_id}`"
                )
                await telegram_bot.send_text_message(tele_msg)

        except Exception as e:
            logger.error(f"Error evaluating symbol {symbol} in Omni Bot: {e}")

    async def _manage_open_positions(self):
        """Monitors open positions, checks TP/SL, triggers self-learning on trade exit."""
        from app.api.routes_bot import current_bot_settings

        adapter = execution_manager.get_active_adapter()
        positions = await adapter.get_positions()
        if not positions:
            return

        for p in positions:
            sym = p.get("symbol", "XAU/USD")
            direction = p.get("direction", "BUY").upper()
            entry_p = float(p.get("entry_price", 0.0))
            sl_p = float(p.get("stop_loss", 0.0))
            tp2_p = float(p.get("take_profit_2", 0.0))
            pos_id = p.get("id") or p.get("position_id")

            # Get current live price
            entry_df = await candle_buffer.get_candles_df(sym, "5m", limit=3)
            if entry_df.empty:
                continue
            current_price = float(entry_df["close"].iloc[-1])

            # Check Exit Conditions
            is_tp = (direction == "BUY" and current_price >= tp2_p) or (direction == "SELL" and current_price <= tp2_p and tp2_p > 0)
            is_sl = (direction == "BUY" and current_price <= sl_p and sl_p > 0) or (direction == "SELL" and current_price >= sl_p)

            if is_tp or is_sl:
                outcome = "WIN" if is_tp else "LOSS"
                pnl_dollars = (current_price - entry_p) * 100 * float(p.get("size_lots", 0.1)) if direction == "BUY" else (entry_p - current_price) * 100 * float(p.get("size_lots", 0.1))

                # Close position
                await adapter.close_position(pos_id or sym, exit_price=current_price)

                # Feed result into Omni Self-Learning Feedback Engine
                feedback_engine.record_trade_outcome(
                    symbol=sym,
                    outcome=outcome,
                    r_multiple=2.0 if is_tp else -1.0,
                    session="ACTIVE",
                    rvol_bucket="NORMAL"
                )

                if is_tp:
                    signal_history_store.increment_right_predictions()

                # Send Telegram notification
                if current_bot_settings.notify_on_position_close and telegram_bot.token and telegram_bot.chat_id:
                    icon = "🎉" if is_tp else "🛑"
                    exit_msg = (
                        f"{icon} *TRADE CLOSED — {outcome}*\n\n"
                        f"• Symbol: *{sym}* ({direction})\n"
                        f"• Exit Price: *${current_price:.2f}*\n"
                        f"• Entry Price: *${entry_p:.2f}*\n"
                        f"• Realized PnL: *${pnl_dollars:+.2f}*\n"
                        f"• Trigger: *{'Take Profit Hit 🎯' if is_tp else 'Stop Loss Hit 🛑'}*\n"
                        f"🧠 *Feedback Engine:* Trade logged to self-learning matrix."
                    )
                    await telegram_bot.send_text_message(exit_msg)

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Returns real-time status of each node in the system diagram."""
        from app.api.routes_bot import current_bot_settings

        return {
            "status": "RUNNING" if self._running else "STOPPED",
            "bot_active": current_bot_settings.bot_active,
            "scan_count": self.scan_count,
            "alerts_sent_count": self.alerts_sent_count,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "scan_interval_seconds": self.scan_interval_seconds,
            "nodes": {
                "data": {
                    "provider": settings.default_data_provider,
                    "status": "STREAMING_LIVE",
                    "feed": "Spot Market Real-Time"
                },
                "settings": {
                    "execution_mode": current_bot_settings.execution_mode,
                    "min_confidence_score": current_bot_settings.min_confidence_score,
                    "max_risk_percent": current_bot_settings.max_risk_percent,
                    "default_lot_size": current_bot_settings.default_lot_size
                },
                "bot": {
                    "state": "ACTIVE & AUTO-SCANNING" if current_bot_settings.bot_active else "PAUSED",
                    "total_scans": self.scan_count,
                    "total_alerts": self.alerts_sent_count
                },
                "omni_engine": {
                    "status": "ACTIVE_VISION",
                    "multi_timeframe": "1H / 15M / 5M Synced",
                    "last_projection": self.last_prediction_result.get("XAU/USD")
                },
                "telegram": {
                    "configured": bool(current_bot_settings.telegram_bot_token and current_bot_settings.telegram_chat_id),
                    "notify_on_signal": current_bot_settings.notify_on_new_signal,
                    "notify_on_close": current_bot_settings.notify_on_position_close
                }
            }
        }

async def adapter_place_position(
    symbol: str,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit_1: float,
    take_profit_2: float,
    lot_size: float,
    alert_id: str
):
    """Helper to place a position in the active execution manager."""
    from app.execution.models import ExecutionOrderRequest
    order = ExecutionOrderRequest(
        symbol=symbol,
        direction=direction,
        order_type="LIMIT",
        lot_size=lot_size,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit_1=take_profit_1,
        take_profit_2=take_profit_2,
        alert_id=alert_id
    )
    return await execution_manager.execute_order(order)

omni_bot_worker = OmniBotWorker()
