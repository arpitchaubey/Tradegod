import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.backtest.metrics import BacktestReport

class BacktestHistoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str
    timeframe: str
    candle_limit: int
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: float
    profit_factor: float
    net_profit: float
    max_drawdown_percent: float
    expectancy: float
    report: BacktestReport

class BacktestHistoryStore:
    """In-memory and persistent backtesting history log."""

    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self._history: List[BacktestHistoryItem] = []

    def record_backtest(
        self,
        symbol: str,
        timeframe: str,
        candle_limit: int,
        report: BacktestReport
    ) -> BacktestHistoryItem:
        item = BacktestHistoryItem(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            timeframe=timeframe,
            candle_limit=candle_limit,
            total_trades=report.total_trades,
            winning_trades=report.winning_trades,
            losing_trades=report.losing_trades,
            win_rate_percent=report.win_rate_percent,
            profit_factor=report.profit_factor,
            net_profit=report.net_profit,
            max_drawdown_percent=report.max_drawdown_percent,
            expectancy=report.expectancy,
            report=report
        )
        self._history.insert(0, item)
        if len(self._history) > self.max_items:
            self._history = self._history[:self.max_items]
        return item

    def get_all(self, symbol: Optional[str] = None) -> List[BacktestHistoryItem]:
        if symbol:
            return [h for h in self._history if h.symbol.upper() == symbol.upper()]
        return list(self._history)

    def get_by_id(self, history_id: str) -> Optional[BacktestHistoryItem]:
        for h in self._history:
            if h.id == history_id:
                return h
        return None

    def delete_by_id(self, history_id: str) -> bool:
        initial_len = len(self._history)
        self._history = [h for h in self._history if h.id != history_id]
        return len(self._history) < initial_len

    def clear(self):
        self._history.clear()

backtest_history_store = BacktestHistoryStore()
