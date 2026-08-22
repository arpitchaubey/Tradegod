from app.data.symbols import get_symbol_spec

def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float,
    symbol: str = "XAU/USD"
) -> float:
    """
    Calculates exact trade position size (lot size) based on risk percentage and contract specs.

    Formula:
    Max Money Risk = Account Balance * (Risk Percent / 100)
    Point Risk = |Entry Price - Stop Loss Price|
    Position Size (Lots) = Max Money Risk / (Point Risk * Contract Size)
    """
    if entry_price <= 0 or stop_loss_price <= 0 or entry_price == stop_loss_price:
        return 0.01

    spec = get_symbol_spec(symbol)
    max_risk_amount = account_balance * (risk_percent / 100.0)
    point_risk = abs(entry_price - stop_loss_price)

    if point_risk <= 0:
        return spec.min_trade_size

    # Monetary risk per 1 lot = point_risk * spec.contract_size
    monetary_risk_per_lot = point_risk * spec.contract_size

    if monetary_risk_per_lot <= 0:
        return spec.min_trade_size

    raw_lots = max_risk_amount / monetary_risk_per_lot

    # Clamp to symbol limits and round to 2 decimals
    clamped_lots = min(max(raw_lots, spec.min_trade_size), spec.max_trade_size)
    return round(clamped_lots, 2)
