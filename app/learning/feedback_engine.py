import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger("feedback_engine")

class TradeOutcomeRecord(BaseModel):
    alert_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    result: str  # "WIN_TP1", "WIN_TP2", "LOSS_SL", "MANUAL_CLOSE"
    r_multiple: float
    session: str
    rvol: float
    adx_1h: float
    rsi_5m: float
    confidence_score: int
    created_at: str
    closed_at: str

class AdaptiveWeights(BaseModel):
    rule_compliance_weight: int = 40
    trend_alignment_weight: int = 30
    structure_breakout_weight: int = 20
    volume_flow_weight: int = 10
    min_confidence_threshold: int = 70
    adx_gate_threshold: float = 20.0
    last_tuned_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tuning_generation: int = 1

class FeedbackEngine:
    """
    Continuous Feedback and Self-Learning Engine.
    Learns from live trade outcomes to dynamically adapt strategy weights and gates.
    """

    def __init__(self):
        self.outcomes: List[TradeOutcomeRecord] = []
        self.weights = AdaptiveWeights()
        self.tuning_history: List[Dict[str, Any]] = []

    def record_trade_completion(
        self,
        alert_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        stop_loss: float,
        take_profit: float,
        result: str,
        r_multiple: float,
        session: str = "LONDON",
        rvol: float = 1.2,
        adx_1h: float = 25.0,
        rsi_5m: float = 58.0,
        confidence_score: int = 80
    ):
        """Records completed trade outcome into self-learning repository."""
        # Prevent duplicate recording
        if any(o.alert_id == alert_id for o in self.outcomes):
            return

        record = TradeOutcomeRecord(
            alert_id=alert_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            result=result,
            r_multiple=r_multiple,
            session=session,
            rvol=rvol,
            adx_1h=adx_1h,
            rsi_5m=rsi_5m,
            confidence_score=confidence_score,
            created_at=datetime.now(timezone.utc).isoformat(),
            closed_at=datetime.now(timezone.utc).isoformat()
        )
        self.outcomes.append(record)
        logger.info(f"Feedback Engine recorded trade outcome for {alert_id}: {result} ({r_multiple:+.2f}R)")

        # Trigger autonomous parameter tuning
        self.auto_tune_parameters()

    def auto_tune_parameters(self) -> AdaptiveWeights:
        """
        Bayesian/Empirical parameter self-tuning based on accumulated trade history.
        """
        if len(self.outcomes) < 3:
            return self.weights

        wins = [o for o in self.outcomes if "WIN" in o.result]
        win_rate = (len(wins) / len(self.outcomes)) * 100.0

        # Feature Attribution:
        high_rvol_wins = len([o for o in wins if o.rvol >= 1.3])
        high_rvol_total = len([o for o in self.outcomes if o.rvol >= 1.3])
        rvol_win_rate = (high_rvol_wins / max(1, high_rvol_total)) * 100.0

        high_adx_wins = len([o for o in wins if o.adx_1h >= 25.0])
        high_adx_total = len([o for o in self.outcomes if o.adx_1h >= 25.0])
        adx_win_rate = (high_adx_wins / max(1, high_adx_total)) * 100.0

        # Adjust weights dynamically:
        new_vol_weight = self.weights.volume_flow_weight
        if rvol_win_rate >= 75.0 and high_rvol_total >= 2:
            new_vol_weight = min(20, new_vol_weight + 2)

        new_adx_gate = self.weights.adx_gate_threshold
        if adx_win_rate > 70.0 and len(self.outcomes) - high_adx_total >= 2:
            # High ADX outperforms -> tighten ADX gate to filter out chop
            new_adx_gate = min(25.0, new_adx_gate + 1.0)

        new_conf_thresh = self.weights.min_confidence_threshold
        if win_rate < 60.0:
            # Low overall win rate -> increase confidence bar
            new_conf_thresh = min(85, new_conf_thresh + 2)
        elif win_rate >= 80.0:
            new_conf_thresh = max(68, new_conf_thresh - 1)

        self.weights = AdaptiveWeights(
            rule_compliance_weight=40,
            trend_alignment_weight=30,
            structure_breakout_weight=100 - (40 + 30 + new_vol_weight),
            volume_flow_weight=new_vol_weight,
            min_confidence_threshold=new_conf_thresh,
            adx_gate_threshold=new_adx_gate,
            last_tuned_at=datetime.now(timezone.utc).isoformat(),
            tuning_generation=self.weights.tuning_generation + 1
        )

        self.tuning_history.append({
            "timestamp": self.weights.last_tuned_at,
            "generation": self.weights.tuning_generation,
            "win_rate": round(win_rate, 1),
            "sample_size": len(self.outcomes),
            "new_weights": self.weights.model_dump()
        })

        return self.weights

    def get_learning_stats(self) -> Dict[str, Any]:
        """Returns comprehensive analytics for the self-learning feedback dashboard."""
        total = len(self.outcomes)
        wins = [o for o in self.outcomes if "WIN" in o.result]
        losses = [o for o in self.outcomes if "LOSS" in o.result]
        win_rate = round((len(wins) / max(1, total)) * 100.0, 1) if total > 0 else 0.0

        # Session breakdown
        sessions_map = {}
        for o in self.outcomes:
            if o.session not in sessions_map:
                sessions_map[o.session] = {"total": 0, "wins": 0}
            sessions_map[o.session]["total"] += 1
            if "WIN" in o.result:
                sessions_map[o.session]["wins"] += 1

        session_stats = []
        for s_name, data in sessions_map.items():
            s_wr = round((data["wins"] / max(1, data["total"])) * 100.0, 1)
            session_stats.append({
                "session": s_name,
                "trades": data["total"],
                "win_rate": s_wr
            })

        return {
            "total_trades_analyzed": total,
            "total_wins": len(wins),
            "total_losses": len(losses),
            "overall_win_rate": win_rate,
            "active_adaptive_weights": self.weights.model_dump(),
            "session_performance": session_stats,
            "recent_outcomes": [o.model_dump() for o in self.outcomes[-10:]],
            "tuning_history": self.tuning_history[-5:]
        }

feedback_engine = FeedbackEngine()
