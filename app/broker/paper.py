import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.broker.abstract import AbstractBrokerAdapter, AccountSummary, TradeOrder

class PaperBrokerAdapter(AbstractBrokerAdapter):
    """Paper trading execution adapter simulating live balance, equity, positions & PnL."""

    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.closed_trades: List[Dict[str, Any]] = []

    async def connect(self) -> bool:
        return True

    async def get_account_summary(self) -> AccountSummary:
        unrealized = sum(p.get("unrealized_pnl", 0.0) for p in self.positions.values())
        equity = self.balance + unrealized
        margin_used = sum(p.get("margin", 0.0) for p in self.positions.values())
        free_margin = max(0.0, equity - margin_used)

        return AccountSummary(
            mode="PAPER_TRADING",
            balance=round(self.balance, 2),
            equity=round(equity, 2),
            margin_used=round(margin_used, 2),
            free_margin=round(free_margin, 2),
            unrealized_pnl=round(unrealized, 2)
        )

    async def get_positions(self) -> List[Dict[str, Any]]:
        return list(self.positions.values())

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
        order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}"

        # Estimate margin requirement (e.g. for gold 1 lot = 100 oz)
        margin = size_lots * entry_price * 0.02  # 1:50 leverage

        pos = {
            "position_id": order_id,
            "alert_id": alert_id,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "size_lots": size_lots,
            "margin": margin,
            "unrealized_pnl": 0.0,
            "status": "OPEN",
            "opened_at": datetime.now(timezone.utc).isoformat()
        }

        self.positions[order_id] = pos

        return TradeOrder(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            size_lots=size_lots,
            status="FILLED",
            mode="PAPER_TRADING"
        )

    def update_live_prices(self, symbol: str, current_price: float):
        """Updates PnL on open paper positions against current live price ticks/candles."""
        for order_id, pos in self.positions.items():
            if pos["symbol"] != symbol or pos["status"] != "OPEN":
                continue

            pos["current_price"] = current_price
            direction = pos["direction"]
            entry = pos["entry_price"]
            lots = pos["size_lots"]

            # Calculate tick PnL (For XAU/USD, 1 lot = 100 oz, 1.0 price change = $100 PnL)
            contract_multiplier = 100.0 if "XAU" in symbol else 100000.0
            if direction == "BUY" or direction == "long":
                pnl = (current_price - entry) * lots * contract_multiplier
            else:
                pnl = (entry - current_price) * lots * contract_multiplier

            pos["unrealized_pnl"] = round(pnl, 2)

    async def close_position(self, position_id: str, exit_price: float) -> bool:
        if position_id not in self.positions:
            return False

        pos = self.positions.pop(position_id)
        pos["current_price"] = exit_price
        direction = pos["direction"]
        entry = pos["entry_price"]
        lots = pos["size_lots"]

        contract_multiplier = 100.0 if "XAU" in pos["symbol"] else 100000.0
        if direction == "BUY" or direction == "long":
            realized = (exit_price - entry) * lots * contract_multiplier
        else:
            realized = (entry - exit_price) * lots * contract_multiplier

        pos["realized_pnl"] = round(realized, 2)
        pos["status"] = "CLOSED"
        pos["closed_at"] = datetime.now(timezone.utc).isoformat()

        self.balance += pos["realized_pnl"]
        self.closed_trades.append(pos)
        return True

    async def close_all_positions(self) -> int:
        count = len(self.positions)
        p_ids = list(self.positions.keys())
        for pid in p_ids:
            cur_price = self.positions[pid]["current_price"]
            await self.close_position(pid, cur_price)
        return count

paper_broker = PaperBrokerAdapter()
