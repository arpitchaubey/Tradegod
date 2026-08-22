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
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward_ratio: float
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
