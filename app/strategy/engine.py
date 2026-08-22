from typing import Dict, List, Any, Optional
import pandas as pd
from pydantic import BaseModel, Field

from app.strategy.schemas import StrategyDefinition, get_default_gold_strategy
from app.strategy.conditions import evaluate_rule
from app.indicators.trend import evaluate_trend_alignment
from app.indicators.structure import detect_breakout

class RuleEvaluationResult(BaseModel):
    rule_id: str
    description: str
    passed: bool
    explanation: str

class StrategyEvaluationResult(BaseModel):
    strategy_id: str
    symbol: str
    direction: str  # "BUY", "SELL", or "NO_TRADE"
    is_valid_setup: bool
    confidence_score: int  # 0 to 100
    score_breakdown: Dict[str, int]
    rule_results: List[RuleEvaluationResult]
    higher_tf_trend: str  # "bullish", "bearish", "neutral"
    setup_notes: List[str]

class StrategyEngine:
    """Deterministic Multi-Timeframe Strategy Evaluation Engine."""

    def __init__(self, strategy: Optional[StrategyDefinition] = None):
        self.strategy = strategy or get_default_gold_strategy()

    def evaluate(
        self,
        tf_dataframes: Dict[str, pd.DataFrame]
    ) -> StrategyEvaluationResult:
        """
        Evaluates the strategy rules across higher timeframe (1H), setup (15M), and entry (5M).
        """
        rule_results: List[RuleEvaluationResult] = []
        passed_count = 0
        total_rules = len(self.strategy.rules)

        for rule in self.strategy.rules:
            passed, explanation = evaluate_rule(rule, tf_dataframes)
            if passed:
                passed_count += 1
            rule_results.append(RuleEvaluationResult(
                rule_id=rule.id,
                description=rule.description,
                passed=passed,
                explanation=explanation
            ))

        # Check Higher Timeframe Trend & ADX Gate
        trend_tf_df = tf_dataframes.get(self.strategy.timeframes.get("trend", "1h"))
        if trend_tf_df is None or trend_tf_df.empty:
            trend_tf_df = list(tf_dataframes.values())[0]

        trend_dir, trend_aligned, _, _ = evaluate_trend_alignment(trend_tf_df, adx_threshold=20.0)

        # Weighted Confidence Scoring Model (0 to 100)
        # 1. Rule compliance ratio: up to 50 points
        rule_compliance_score = int((passed_count / max(1, total_rules)) * 50)

        # 2. Trend & ADX alignment score: up to 25 points
        if trend_dir != "ranging" and trend_aligned:
            trend_score = 25
        elif trend_dir != "ranging":
            trend_score = 15
        else:
            trend_score = 0

        # 3. Entry & Momentum confirmation score: up to 25 points
        passed_rule_ids = [r.rule_id for r in rule_results if r.passed]
        momentum_score = 25 if len(passed_rule_ids) >= (total_rules - 1) else (15 if len(passed_rule_ids) >= (total_rules // 2) else 5)

        total_confidence = min(100, max(0, rule_compliance_score + trend_score + momentum_score))

        # Setup is strictly valid when all rules pass and confidence meets or exceeds threshold
        min_thresh = getattr(self.strategy, "min_confidence_score", 100)
        is_valid = (passed_count == total_rules) and (total_confidence >= min_thresh)
        direction = "BUY" if (self.strategy.direction == "long" or trend_dir == "bullish") else "SELL"

        notes = [r.explanation for r in rule_results]

        score_breakdown = {
            "rule_compliance": rule_compliance_score,
            "trend_alignment": trend_score,
            "momentum_volume": momentum_score
        }

        return StrategyEvaluationResult(
            strategy_id=self.strategy.id,
            symbol=self.strategy.symbol,
            direction=direction,
            is_valid_setup=is_valid,
            confidence_score=total_confidence,
            score_breakdown=score_breakdown,
            rule_results=rule_results,
            higher_tf_trend=trend_dir,
            setup_notes=notes
        )
