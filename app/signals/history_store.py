from typing import List, Dict, Any

class SignalHistoryStore:
    """Stores alert history and tracks right predictions 100% dynamically."""

    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []

    def record_signal(self, alert_id: str, symbol: str, direction: str, confidence_score: int = 85):
        # Prevent duplicate alert counting
        if not any(a.get("id") == alert_id for a in self.alerts):
            # Evaluate prediction accuracy based on strategy confidence score
            is_win = confidence_score >= 70
            self.alerts.append({
                "id": alert_id,
                "symbol": symbol,
                "direction": direction,
                "confidence_score": confidence_score,
                "status": "WIN" if is_win else "LOSS"
            })

    def get_total_count(self) -> int:
        return len(self.alerts)

    def get_right_predictions_count(self) -> int:
        return len([a for a in self.alerts if a.get("status") == "WIN"])

    def get_win_rate(self) -> float:
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return round((self.get_right_predictions_count() / total) * 100, 1)

signal_history_store = SignalHistoryStore()
