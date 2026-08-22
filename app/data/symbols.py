from typing import Dict, Any, List
from pydantic import BaseModel

class SymbolSpecification(BaseModel):
    symbol: str
    display_name: str
    category: str  # "metals", "forex", "crypto", "indices"
    contract_size: float  # e.g., 100 troy oz for Gold, 100,000 for Forex
    quote_precision: int
    pip_size: float
    min_trade_size: float  # e.g., 0.01 lot
    max_trade_size: float  # e.g., 100.0 lot
    default_timeframes: Dict[str, str]  # {"trend": "1h", "setup": "15m", "entry": "5m"}

# Symbol Registry with XAU/USD as Default
SYMBOL_REGISTRY: Dict[str, SymbolSpecification] = {
    "XAU/USD": SymbolSpecification(
        symbol="XAU/USD",
        display_name="Gold Spot / US Dollar",
        category="metals",
        contract_size=100.0,  # 1 lot = 100 troy ounces
        quote_precision=2,
        pip_size=0.1,
        min_trade_size=0.01,
        max_trade_size=100.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    ),
    "XAG/USD": SymbolSpecification(
        symbol="XAG/USD",
        display_name="Silver Spot / US Dollar",
        category="metals",
        contract_size=5000.0,
        quote_precision=3,
        pip_size=0.01,
        min_trade_size=0.01,
        max_trade_size=50.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    ),
    "EUR/USD": SymbolSpecification(
        symbol="EUR/USD",
        display_name="Euro / US Dollar",
        category="forex",
        contract_size=100000.0,  # 1 standard lot = 100,000 units
        quote_precision=5,
        pip_size=0.0001,
        min_trade_size=0.01,
        max_trade_size=100.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    ),
    "GBP/USD": SymbolSpecification(
        symbol="GBP/USD",
        display_name="British Pound / US Dollar",
        category="forex",
        contract_size=100000.0,
        quote_precision=5,
        pip_size=0.0001,
        min_trade_size=0.01,
        max_trade_size=100.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    ),
    "USD/JPY": SymbolSpecification(
        symbol="USD/JPY",
        display_name="US Dollar / Japanese Yen",
        category="forex",
        contract_size=100000.0,
        quote_precision=3,
        pip_size=0.01,
        min_trade_size=0.01,
        max_trade_size=100.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    ),
    "BTC/USD": SymbolSpecification(
        symbol="BTC/USD",
        display_name="Bitcoin / US Dollar",
        category="crypto",
        contract_size=1.0,
        quote_precision=2,
        pip_size=1.0,
        min_trade_size=0.01,
        max_trade_size=10.0,
        default_timeframes={"trend": "4h", "setup": "1h", "entry": "15m"}
    ),
    "ETH/USD": SymbolSpecification(
        symbol="ETH/USD",
        display_name="Ethereum / US Dollar",
        category="crypto",
        contract_size=1.0,
        quote_precision=2,
        pip_size=0.1,
        min_trade_size=0.1,
        max_trade_size=100.0,
        default_timeframes={"trend": "4h", "setup": "1h", "entry": "15m"}
    ),
    "US30": SymbolSpecification(
        symbol="US30",
        display_name="Dow Jones Industrial Average",
        category="indices",
        contract_size=1.0,
        quote_precision=1,
        pip_size=1.0,
        min_trade_size=0.1,
        max_trade_size=50.0,
        default_timeframes={"trend": "1h", "setup": "15m", "entry": "5m"}
    )
}

DEFAULT_SYMBOL = "XAU/USD"

def get_symbol_spec(symbol: str) -> SymbolSpecification:
    """Returns symbol specification or falls back to XAU/USD default."""
    formatted = symbol.strip().upper()
    if "/" not in formatted and formatted.startswith("XAU"):
        formatted = "XAU/USD"
    return SYMBOL_REGISTRY.get(formatted, SYMBOL_REGISTRY[DEFAULT_SYMBOL])

def list_supported_symbols() -> List[Dict[str, Any]]:
    """Lists all supported trading symbols."""
    return [spec.model_dump() for spec in SYMBOL_REGISTRY.values()]
