import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.config import settings
from app.broker.abstract import AbstractBrokerAdapter, AccountSummary, TradeOrder
from app.broker.paper import paper_broker
from app.broker.oanda import OandaBrokerAdapter
from app.broker.mt5 import MetaTrader5BrokerAdapter
from app.news.filter import news_filter
from app.signals.models import SignalPayload

logger = logging.getLogger("execution_manager")

class ExecutionManager:
    """
    Central Execution Manager managing trading modes, order routing, and safety interlocks:
    - Mode Switch: PAPER_TRADING, OANDA, MT5, DISABLED
    - Emergency Kill-Switch
    - Daily Loss Limit
    - Max Trades Per Day
    - Max Open Positions Limit
    - Spread Filter
    - News Blackout Filter
    """

    def __init__(self):
        self.mode = settings.execution_mode  # "PAPER_TRADING", "OANDA", "MT5", "DISABLED"
        self.is_kill_switch_active = False
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self.adapters: Dict[str, AbstractBrokerAdapter] = {
            "PAPER_TRADING": paper_broker,
            "OANDA": OandaBrokerAdapter(settings.broker_api_key, settings.broker_account_id),
            "MT5": MetaTrader5BrokerAdapter()
        }

    def get_active_adapter(self) -> AbstractBrokerAdapter:
        return self.adapters.get(self.mode, paper_broker)

    def set_execution_mode(self, new_mode: str) -> str:
        valid_modes = ["PAPER_TRADING", "OANDA", "MT5", "DISABLED"]
        if new_mode.upper() in valid_modes:
            self.mode = new_mode.upper()
            logger.info(f"Execution Mode switched to: {self.mode}")
        return self.mode

    def toggle_kill_switch(self, active: Optional[bool] = None) -> bool:
        if active is not None:
            self.is_kill_switch_active = active
        else:
            self.is_kill_switch_active = not self.is_kill_switch_active
        logger.warning(f"EMERGENCY KILL-SWITCH STATUS: {self.is_kill_switch_active}")
        return self.is_kill_switch_active

    async def get_execution_status(self) -> Dict[str, Any]:
        adapter = self.get_active_adapter()
        summary = await adapter.get_account_summary()
        positions = await adapter.get_positions()

        return {
            "mode": self.mode,
            "is_kill_switch_active": self.is_kill_switch_active,
            "daily_trade_count": self.daily_trade_count,
            "daily_pnl": self.daily_pnl,
            "news_blackout_active": news_filter.is_blackout_active(),
            "account": summary.model_dump(),
            "open_positions_count": len(positions)
        }

    async def execute_signal(self, signal: SignalPayload) -> Optional[TradeOrder]:
        """
        Evaluates safety interlocks and submits trade order through active broker adapter.
        """
        if self.mode == "DISABLED":
            logger.info("Execution mode is DISABLED. Skipping order submission.")
            return None

        if self.is_kill_switch_active:
            logger.warning("Execution blocked: EMERGENCY KILL-SWITCH IS ACTIVE.")
            return None

        # Check Max Daily Trades
        if self.daily_trade_count >= settings.max_trades_per_day:
            logger.warning(f"Execution blocked: Max daily trade count reached ({self.daily_trade_count}).")
            return None

        # Check News Blackout Filter
        if news_filter.is_blackout_active():
            logger.warning("Execution blocked: High-impact economic news blackout active.")
            return None

        adapter = self.get_active_adapter()
        positions = await adapter.get_positions()

        # Check Max Open Positions
        if len(positions) >= settings.max_open_positions:
            logger.warning(f"Execution blocked: Max open positions limit reached ({len(positions)}).")
            return None

        # Place Order
        order = await adapter.place_order(
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit_1=signal.take_profit_1,
            take_profit_2=signal.take_profit_2,
            size_lots=signal.position_size_lots,
            alert_id=signal.alert_id
        )

        self.daily_trade_count += 1
        return order

    async def close_all_positions(self) -> int:
        adapter = self.get_active_adapter()
        return await adapter.close_all_positions()

execution_manager = ExecutionManager()
