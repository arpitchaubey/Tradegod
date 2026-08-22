import re
from typing import Dict, Any
from app.strategy.schemas import StrategyDefinition, StrategyRule, get_default_gold_strategy

def parse_natural_language_strategy(text: str) -> StrategyDefinition:
    """
    Parses a plain English strategy statement into structured StrategyDefinition JSON rules.
    Example text: 'Analyze XAU/USD on the 5-minute chart. Buy when price breaks resistance,
    the 20 EMA is above the 50 EMA, RSI is above 55. Use a 1:2 risk/reward ratio.'
    """
    text_lower = text.lower()

    # Detect symbol
    symbol = "XAU/USD"
    if "eur/usd" in text_lower or "eurusd" in text_lower:
        symbol = "EUR/USD"
    elif "gbp/usd" in text_lower or "gbpusd" in text_lower:
        symbol = "GBP/USD"
    elif "btc/usd" in text_lower or "btcusd" in text_lower:
        symbol = "BTC/USD"

    # Detect direction
    direction = "long"
    if "sell" in text_lower or "short" in text_lower:
        direction = "short"

    # Detect risk reward
    rr = 2.0
    rr_match = re.search(r"1:(\d+(?:\.\d+)?)", text_lower)
    if rr_match:
        rr = float(rr_match.group(1))

    # Detect RSI
    rsi_val = 55.0
    rsi_match = re.search(r"rsi\s*(?:is\s*)?(?:above|>)\s*(\d+)", text_lower)
    if rsi_match:
        rsi_val = float(rsi_match.group(1))

    rules = [
        StrategyRule(
            id="r1_trend_ema",
            description="1H Trend Alignment: EMA 20 > EMA 50",
            condition_type="indicator_compare",
            left_operand="ema20",
            operator=">",
            right_operand="ema50",
            timeframe="trend"
        ),
        StrategyRule(
            id="r2_entry_ema",
            description="5M Entry: EMA 20 > EMA 50",
            condition_type="indicator_compare",
            left_operand="ema20",
            operator=">",
            right_operand="ema50",
            timeframe="entry"
        ),
        StrategyRule(
            id="r3_rsi",
            description=f"5M Momentum: RSI > {rsi_val}",
            condition_type="indicator_compare",
            left_operand="rsi",
            operator=">",
            right_operand=rsi_val,
            timeframe="entry"
        ),
        StrategyRule(
            id="r4_breakout",
            description="5M Price breaks key level",
            condition_type="breakout",
            left_operand="close",
            operator=">",
            right_operand="resistance" if direction == "long" else "support",
            timeframe="entry"
        ),
        StrategyRule(
            id="r5_confirmation",
            description="5M Candle confirmation close",
            condition_type="candle_close",
            left_operand="close",
            operator=">",
            right_operand="breakout_level",
            timeframe="entry"
        )
    ]

    return StrategyDefinition(
        id=f"custom_strategy_{symbol.replace('/', '').lower()}",
        name=f"Custom Parsed Strategy for {symbol}",
        symbol=symbol,
        timeframes={"trend": "1h", "setup": "15m", "entry": "5m"},
        direction=direction,
        rules=rules,
        risk_reward_ratio=rr,
        sl_method="structure",
        tp_method="fixed_rr",
        min_confidence_score=70
    )
