import json
import re
from typing import Dict, Any, List
from app.strategy.schemas import StrategyDefinition, StrategyRule, get_default_gold_strategy

def parse_natural_language_strategy(prompt: str) -> StrategyDefinition:
    """
    Parses a user's natural language strategy description into structured rules.
    Extracts timeframes, direction, indicator thresholds, SL/TP rules, and risk/reward ratio.
    """
    text = prompt.lower()

    # Default fallback
    base_strategy = get_default_gold_strategy()

    # Determine Symbol
    symbol = "XAU/USD"
    if "eur" in text or "eurusd" in text:
        symbol = "EUR/USD"
    elif "gbp" in text or "gbpusd" in text:
        symbol = "GBP/USD"
    elif "btc" in text or "btcusd" in text:
        symbol = "BTC/USD"
    elif "eth" in text or "ethusd" in text:
        symbol = "ETH/USD"
    elif "us30" in text or "dow" in text:
        symbol = "US30"

    # Determine Direction
    direction = "long"
    if "sell" in text or "short" in text:
        direction = "short"

    # Risk Reward Ratio
    rr_match = re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", text)
    if rr_match:
        try:
            r1, r2 = float(rr_match.group(1)), float(rr_match.group(2))
            risk_reward = round(r2 / r1, 2) if r1 > 0 else 2.0
        except Exception:
            risk_reward = 2.0
    elif "1:3" in text or "3r" in text:
        risk_reward = 3.0
    elif "1:1" in text or "1r" in text:
        risk_reward = 1.0
    else:
        risk_reward = 2.0

    rules: List[StrategyRule] = []
    rule_counter = 1

    # EMA Rules
    if "ema" in text or "moving average" in text:
        if direction == "long":
            rules.append(StrategyRule(
                id=f"rule_{rule_counter}",
                description="EMA 20 > EMA 50 trend alignment",
                condition_type="indicator_compare",
                left_operand="ema20",
                operator=">",
                right_operand="ema50",
                timeframe="entry"
            ))
        else:
            rules.append(StrategyRule(
                id=f"rule_{rule_counter}",
                description="EMA 20 < EMA 50 trend alignment",
                condition_type="indicator_compare",
                left_operand="ema20",
                operator="<",
                right_operand="ema50",
                timeframe="entry"
            ))
        rule_counter += 1

    # RSI Rules
    rsi_match = re.search(r"rsi\s*(?:>|<|above|below)\s*(\d+)", text)
    if rsi_match:
        rsi_val = float(rsi_match.group(1))
        op = ">" if ("above" in text or ">" in text) else "<"
        rules.append(StrategyRule(
            id=f"rule_{rule_counter}",
            description=f"RSI Momentum {op} {rsi_val}",
            condition_type="indicator_compare",
            left_operand="rsi",
            operator=op,
            right_operand=rsi_val,
            timeframe="entry"
        ))
        rule_counter += 1
    else:
        rsi_val = 55.0 if direction == "long" else 45.0
        op = ">" if direction == "long" else "<"
        rules.append(StrategyRule(
            id=f"rule_{rule_counter}",
            description=f"RSI Momentum {op} {rsi_val}",
            condition_type="indicator_compare",
            left_operand="rsi",
            operator=op,
            right_operand=rsi_val,
            timeframe="entry"
        ))
        rule_counter += 1

    # Breakout & Retest Rules
    if "break" in text or "resistance" in text or "support" in text or "breakout" in text:
        level_target = "resistance" if direction == "long" else "support"
        op = ">" if direction == "long" else "<"
        rules.append(StrategyRule(
            id=f"rule_{rule_counter}",
            description=f"Price {op} {level_target} level",
            condition_type="breakout",
            left_operand="close",
            operator=op,
            right_operand=level_target,
            timeframe="entry"
        ))
        rule_counter += 1

        rules.append(StrategyRule(
            id=f"rule_{rule_counter}",
            description="Candle close confirmation",
            condition_type="candle_close",
            left_operand="close",
            operator=op,
            right_operand="breakout_level",
            timeframe="entry"
        ))
        rule_counter += 1

    # Fallback rules if none extracted
    if not rules:
        rules = base_strategy.rules

    # Formulate Strategy Title
    name = f"{symbol} Custom Strategy ({direction.upper()})"

    return StrategyDefinition(
        id=f"custom_strategy_{hash(prompt) % 10000}",
        name=name,
        symbol=symbol,
        timeframes={"trend": "1h", "setup": "15m", "entry": "5m"},
        direction=direction,
        rules=rules,
        risk_reward_ratio=risk_reward,
        sl_method="structure",
        tp_method="fixed_rr",
        min_confidence_score=70
    )
