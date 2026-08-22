import logging
import httpx
from typing import Dict, Any, List
from app.broker.abstract import AbstractBrokerAdapter, AccountSummary, TradeOrder

logger = logging.getLogger("oanda_broker")

class OandaBrokerAdapter(AbstractBrokerAdapter):
    """OANDA v20 REST API Execution Adapter."""

    def __init__(self, api_key: str = "", account_id: str = "", environment: str = "practice"):
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = (
            "https://api-fxpractice.oanda.com/v3"
            if environment == "practice"
            else "https://api-fxtrade.oanda.com/v3"
        )

    async def connect(self) -> bool:
        if not self.api_key or not self.account_id:
            logger.warning("OANDA API Key or Account ID not provided.")
            return False
        return True

    async def get_account_summary(self) -> AccountSummary:
        if not self.api_key or not self.account_id:
            return AccountSummary(
                mode="OANDA", balance=10000.0, equity=10000.0, margin_used=0.0, free_margin=10000.0
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/accounts/{self.account_id}/summary"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    acc = resp.json().get("account", {})
                    balance = float(acc.get("balance", 10000.0))
                    equity = float(acc.get("NAV", balance))
                    margin_used = float(acc.get("marginUsed", 0.0))
                    free_margin = float(acc.get("marginAvailable", balance))
                    unrealized = float(acc.get("unrealizedPL", 0.0))
                    return AccountSummary(
                        mode="OANDA",
                        balance=balance,
                        equity=equity,
                        margin_used=margin_used,
                        free_margin=free_margin,
                        unrealized_pnl=unrealized
                    )
            except Exception as e:
                logger.error(f"Error fetching OANDA account summary: {e}")

        return AccountSummary(mode="OANDA", balance=10000.0, equity=10000.0, margin_used=0.0, free_margin=10000.0)

    async def get_positions(self) -> List[Dict[str, Any]]:
        return []

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
        order_id = f"OANDA-{alert_id}"
        return TradeOrder(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            size_lots=size_lots,
            status="PENDING",
            mode="OANDA"
        )

    async def close_position(self, position_id: str, exit_price: float) -> bool:
        return True

    async def close_all_positions(self) -> int:
        return 0
