from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class StrategyRule(BaseModel):
    id: str
    description: str
    condition_type: str  # "indicator_compare", "breakout", "structure", "candle_close"
    left_operand: str    # e.g., "ema20", "rsi", "close"
    operator: str        # ">", "<", ">=", "<=", "==", "cross_above", "cross_below"
    right_operand: Any   # e.g., "ema50", 55.0, "resistance"
    timeframe: str = "entry"  # "trend", "setup", "entry"

class StrategyDefinition(BaseModel):
    id: str = "gold_breakout_v1"
    name: str = "Gold Multi-Timeframe Breakout Strategy"
    symbol: str = "XAU/USD"
    raw_prompt: Optional[str] = None
    timeframes: Dict[str, str] = Field(
        default_factory=lambda: {"trend": "1h", "setup": "15m", "entry": "5m"}
    )
    direction: str = "long"  # "long", "short", or "both"
    rules: List[StrategyRule] = Field(default_factory=list)
    risk_reward_ratio: float = 2.0
    sl_method: str = "structure"  # "structure", "atr", "fixed"
    tp_method: str = "fixed_rr"   # "fixed_rr", "multiple_rr", "resistance"
    min_confidence_score: int = 70

def get_default_gold_strategy() -> StrategyDefinition:
    """Returns the default Gold Multi-Timeframe Breakout Strategy definition."""
    return StrategyDefinition(
        id="gold_breakout_default",
        name="Gold 5M Breakout & Retest Strategy",
        symbol="XAU/USD",
        timeframes={"trend": "1h", "setup": "15m", "entry": "5m"},
        direction="long",
        risk_reward_ratio=2.0,
        sl_method="structure",
        tp_method="fixed_rr",
        min_confidence_score=70,
        rules=[
            StrategyRule(
                id="r1_trend_ema",
                description="1H Trend: Fast EMA (20) above Slow EMA (50)",
                condition_type="indicator_compare",
                left_operand="ema20",
                operator=">",
                right_operand="ema50",
                timeframe="trend"
            ),
            StrategyRule(
                id="r2_entry_ema",
                description="5M Entry: EMA 20 above EMA 50",
                condition_type="indicator_compare",
                left_operand="ema20",
                operator=">",
                right_operand="ema50",
                timeframe="entry"
            ),
            StrategyRule(
                id="r3_rsi_momentum",
                description="5M Momentum: RSI > 55",
                condition_type="indicator_compare",
                left_operand="rsi",
                operator=">",
                right_operand=55.0,
                timeframe="entry"
            ),
            StrategyRule(
                id="r4_break_resistance",
                description="5M Price breaks key resistance level",
                condition_type="breakout",
                left_operand="close",
                operator=">",
                right_operand="resistance",
                timeframe="entry"
            ),
            StrategyRule(
                id="r5_candle_close",
                description="5M Candle closes strictly above breakout level",
                condition_type="candle_close",
                left_operand="close",
                operator=">",
                right_operand="breakout_level",
                timeframe="entry"
            )
        ]
    )
