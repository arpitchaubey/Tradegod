from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.data.symbols import get_symbol_spec, SymbolSpecification

class ActiveChartInfo(BaseModel):
    symbol: str = "XAU/USD"
    display_name: str = "Gold Spot / US Dollar"
    category: str = "metals"
    provider: str = "yfinance"
    timeframes: Dict[str, str] = Field(
        default_factory=lambda: {"trend": "1h", "setup": "15m", "entry": "5m"}
    )
    last_price: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    spread: float = 0.0
    candle_count: int = 0
    adx_1h: float = 25.0
    regime: str = "trending"  # "trending" or "ranging"
    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: str = "ACTIVE"
    data_quality: str = "REALTIME"

def build_chart_info(
    symbol: str = "XAU/USD",
    provider: str = "yfinance",
    timeframes: Optional[Dict[str, str]] = None,
    last_price: float = 0.0,
    bid: float = 0.0,
    ask: float = 0.0,
    candle_count: int = 0,
    adx_1h: float = 25.0,
    regime: str = "trending",
    status: str = "ACTIVE"
) -> ActiveChartInfo:
    """Builds structured metadata object for active chart state."""
    spec: SymbolSpecification = get_symbol_spec(symbol)
    tf = timeframes or spec.default_timeframes

    calc_bid = bid if bid > 0 else (last_price - spec.pip_size * 0.5)
    calc_ask = ask if ask > 0 else (last_price + spec.pip_size * 0.5)
    spread = round(max(0.0, calc_ask - calc_bid), spec.quote_precision)

    return ActiveChartInfo(
        symbol=spec.symbol,
        display_name=spec.display_name,
        category=spec.category,
        provider=provider,
        timeframes=tf,
        last_price=round(last_price, spec.quote_precision),
        bid_price=round(calc_bid, spec.quote_precision),
        ask_price=round(calc_ask, spec.quote_precision),
        spread=spread,
        candle_count=candle_count,
        adx_1h=round(adx_1h, 2),
        regime=regime,
        last_updated=datetime.now(timezone.utc).isoformat(),
        status=status,
        data_quality="REALTIME" if provider != "mock" else "MOCK_SIMULATION"
    )
