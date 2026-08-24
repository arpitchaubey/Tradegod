import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ForecastHistoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str
    timeframe: str
    primary_direction: str
    win_probability_percent: int
    entry_market_price: float
    entry_limit_price: float
    entry_reachability_percent: int
    entry_reachability_state: str
    entry_distance_pips: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: Optional[float] = None
    risk_reward_ratio: float
    min_profit_pips: float
    expected_profit_pips: float
    expected_profit_usd: float
    position_size_lots: float
    market_regime: str
    institutional_drivers: List[str]
    invalidation_criteria: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ForecastHistoryStore:
    """In-memory and persisted log of Omni AI trade projections."""

    def __init__(self, max_items: int = 150):
        self.max_items = max_items
        self._history: List[ForecastHistoryItem] = []

    def record_forecast(self, forecast: Any) -> ForecastHistoryItem:
        # Avoid duplicate consecutive forecast within 30 seconds for the same symbol
        item = ForecastHistoryItem(
            id=str(uuid.uuid4())[:8],
            symbol=forecast.symbol,
            timeframe=forecast.timeframe,
            primary_direction=forecast.primary_direction,
            win_probability_percent=forecast.win_probability_percent,
            entry_market_price=forecast.entry_market_price,
            entry_limit_price=forecast.entry_limit_price,
            entry_reachability_percent=forecast.entry_reachability_percent,
            entry_reachability_state=forecast.entry_reachability_state,
            entry_distance_pips=forecast.entry_distance_pips,
            stop_loss=forecast.stop_loss,
            take_profit_1=forecast.take_profit_1,
            take_profit_2=forecast.take_profit_2,
            take_profit_3=forecast.take_profit_3,
            risk_reward_ratio=forecast.risk_reward_ratio,
            min_profit_pips=forecast.min_profit_pips,
            expected_profit_pips=forecast.expected_profit_pips,
            expected_profit_usd=forecast.expected_profit_usd,
            position_size_lots=forecast.position_size_lots,
            market_regime=forecast.market_regime,
            institutional_drivers=forecast.institutional_drivers,
            invalidation_criteria=forecast.invalidation_criteria,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self._history.insert(0, item)
        if len(self._history) > self.max_items:
            self._history = self._history[:self.max_items]
        return item

    def get_all(self, symbol: Optional[str] = None) -> List[ForecastHistoryItem]:
        if symbol:
            return [f for f in self._history if f.symbol.upper() == symbol.upper()]
        return list(self._history)

    def get_by_id(self, forecast_id: str) -> Optional[ForecastHistoryItem]:
        for f in self._history:
            if f.id == forecast_id:
                return f
        return None

    def delete_by_id(self, forecast_id: str) -> bool:
        initial_len = len(self._history)
        self._history = [f for f in self._history if f.id != forecast_id]
        return len(self._history) < initial_len

    def clear(self):
        self._history.clear()

forecast_history_store = ForecastHistoryStore()
