from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SignalStatus(str, Enum):
    WAITING = "WAITING"
    WATCHING = "WATCHING"
    SETUP_DETECTED = "SETUP_DETECTED"
    CONFIRMING = "CONFIRMING"
    CONFIRMED = "CONFIRMED"
    SIGNAL_SENT = "SIGNAL_SENT"
    ACTIVE = "ACTIVE"
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"

class SignalPayload(BaseModel):
    alert_id: str
    symbol: str
    direction: str  # "BUY", "SELL", "NO_TRADE"
    entry_price: float
    entry_market_price: Optional[float] = None
    entry_limit_price: Optional[float] = None
    entry_reachability_percent: Optional[int] = 100
    entry_reachability_state: Optional[str] = "INSTANT_MARKET_FILL"
    entry_distance_pips: Optional[float] = 0.0
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: Optional[float] = None
    risk_reward_ratio: float
    min_profit_pips: Optional[float] = 30.0
    expected_profit_pips: Optional[float] = 30.0
    expected_profit_usd: Optional[float] = 0.0
    position_size_lots: float
    confidence_score: int
    timeframe: str = "5m"
    higher_tf_trend: str = "bullish"
    status: SignalStatus = SignalStatus.CONFIRMED
    confirmations: List[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    chart_info: Dict[str, Any] = Field(default_factory=dict)
    ai_explanation: Optional[str] = None
