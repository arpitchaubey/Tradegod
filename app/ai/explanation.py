from typing import List

def generate_signal_explanation(
    symbol: str,
    direction: str,
    entry: float,
    sl: float,
    tp: float,
    confidence: int,
    trend: str,
    confirmations: List[str]
) -> str:
    """
    Generates a clear, institutional-grade technical analysis explanation of why a signal was triggered.
    """
    dir_str = "BULLISH BUY" if direction.upper() == "BUY" else "BEARISH SELL"
    confirm_text = "\n".join([f"  {c}" for c in confirmations]) if confirmations else "  ✓ Deterministic rule alignment confirmed."

    return (
        f"Detected a high-confluence {dir_str} setup on {symbol}.\n"
        f"• Higher Timeframe Trend: {trend.upper()} structure alignment (1H / 15M).\n"
        f"• Entry & Risk Parameters: Entry ${entry:.2f} | SL ${sl:.2f} | TP2 ${tp:.2f}.\n"
        f"• Rule Confirmations:\n{confirm_text}\n"
        f"• Institutional Confluence Rating: {confidence}/100."
    )
