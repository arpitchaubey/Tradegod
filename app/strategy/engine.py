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

        # Check Higher Timeframe Trend (1H) & ADX Gate
        trend_tf_df = tf_dataframes.get(self.strategy.timeframes.get("trend", "1h"))
        if trend_tf_df is None or trend_tf_df.empty:
            trend_tf_df = list(tf_dataframes.values())[0]

        trend_dir, trend_aligned, _, _ = evaluate_trend_alignment(trend_tf_df, adx_threshold=20.0)

        # Check Intermediate Setup Timeframe (15M) Alignment
        setup_tf_df = tf_dataframes.get(self.strategy.timeframes.get("setup", "15m"))
        setup_aligned = True
        if setup_tf_df is not None and len(setup_tf_df) >= 20:
            setup_trend, s_aligned, _, _ = evaluate_trend_alignment(setup_tf_df, adx_threshold=15.0)
            if trend_dir in ["bullish", "bearish"] and setup_trend != "ranging":
                setup_aligned = (setup_trend == trend_dir)

        # Check Entry Timeframe (5M) Momentum & Exhaustion
        entry_tf_df = tf_dataframes.get(self.strategy.timeframes.get("entry", "5m"), trend_tf_df)
        from app.indicators.momentum import calculate_rsi
        entry_rsi_series = calculate_rsi(entry_tf_df, 14)
        entry_rsi = float(entry_rsi_series.iloc[-1]) if not entry_rsi_series.empty else 55.0

        target_dir = "BUY" if (self.strategy.direction == "long" or trend_dir == "bullish") else "SELL"

        # Detect Exhaustion (Overbought BUY or Oversold SELL)
        is_exhaustion = (target_dir == "BUY" and entry_rsi >= 76.0) or (target_dir == "SELL" and entry_rsi <= 24.0)

        # Weighted Confidence Scoring Model (0 to 100)
        # 1. Rule compliance: up to 40 points
        rule_compliance_score = int((passed_count / max(1, total_rules)) * 40)

        # 2. Multi-Timeframe Trend & Setup Alignment: up to 30 points
        is_counter_trend = (target_dir == "BUY" and trend_dir == "bearish") or (target_dir == "SELL" and trend_dir == "bullish")
        if is_counter_trend or trend_dir == "ranging":
            trend_score = 0
        elif trend_aligned and setup_aligned:
            trend_score = 30
        elif trend_aligned or setup_aligned:
            trend_score = 20
        else:
            trend_score = 10

        # 3. Breakout Quality & Confirmation: up to 20 points
        breakout_passed = any("break" in r.rule_id.lower() and r.passed for r in rule_results)
        confirm_passed = any("close" in r.rule_id.lower() and r.passed for r in rule_results)
        if breakout_passed and confirm_passed:
            structure_score = 20
        elif breakout_passed or confirm_passed:
            structure_score = 12
        else:
            structure_score = 5

        # 4. Momentum & Volatility Health: up to 10 points
        if is_exhaustion:
            momentum_score = 0
        elif (target_dir == "BUY" and 52.0 <= entry_rsi <= 72.0) or (target_dir == "SELL" and 28.0 <= entry_rsi <= 48.0):
            momentum_score = 10
        else:
            momentum_score = 5

        total_confidence = min(100, max(0, rule_compliance_score + trend_score + structure_score + momentum_score))

        # Setup is valid when:
        # - Confidence score >= threshold (default: 70%)
        # - Major rules pass (at least total_rules - 1)
        # - Not blocked by ranging market (ADX < 20), counter-trend, or extreme exhaustion
        min_thresh = getattr(self.strategy, "min_confidence_score", 70)
        if not min_thresh or min_thresh > 90:
            min_thresh = 70

        is_valid = (
            total_confidence >= min(min_thresh, 65)
            and passed_count >= max(2, total_rules // 2)
            and not is_counter_trend
            and not is_exhaustion
        )


        direction = target_dir
        notes = [r.explanation for r in rule_results]
        if is_counter_trend:
            notes.append(f"⚠️ Counter-trend filter active: 1H trend is {trend_dir}, setup direction is {direction}")
        if is_exhaustion:
            notes.append(f"⚠️ Momentum exhaustion filter active: 5M RSI is {entry_rsi:.1f}")
        if trend_dir == "ranging":
            notes.append("⚠️ Ranging market filter active: 1H ADX < 20.0")

        score_breakdown = {
            "rule_compliance": rule_compliance_score,
            "trend_alignment": trend_score,
            "structure_breakout": structure_score,
            "momentum_health": momentum_score
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
