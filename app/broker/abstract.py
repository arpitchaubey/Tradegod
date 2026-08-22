from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class AccountSummary(BaseModel):
    mode: str
    balance: float
    equity: float
    margin_used: float
    free_margin: float
    unrealized_pnl: float = 0.0

class TradeOrder(BaseModel):
    order_id: str
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    size_lots: float
    status: str = "FILLED"
    mode: str = "PAPER_TRADING"

class AbstractBrokerAdapter(ABC):
    """Abstract interface for execution broker adapters (Paper, OANDA, MT5)."""

    @abstractmethod
    async def connect() -> bool:
        pass

    @abstractmethod
    async def get_account_summary(self) -> AccountSummary:
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: float,
        size_lots: float,
        alert_id: str
    ) -> TradeOrder:
        pass

    @abstractmethod
    async def close_position(self, position_id: str, exit_price: float) -> bool:
        pass

    @abstractmethod
    async def close_all_positions(self) -> int:
        pass
