from typing import Set
from datetime import datetime, timezone

class SignalDeduplicator:
    """Prevents duplicate alerts by maintaining unique alert IDs."""

    def __init__(self):
        self._sent_alert_ids: Set[str] = set()

    def generate_alert_id(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        candle_timestamp: str
    ) -> str:
        """
        Generates unique deterministic Alert ID.
        Format: XAUUSD-5M-BUY-20260822-143500
        """
        clean_symbol = symbol.replace("/", "").upper()
        clean_tf = timeframe.upper()
        clean_dir = direction.upper()

        try:
            dt = datetime.fromisoformat(candle_timestamp.replace("Z", "+00:00"))
            ts_str = dt.strftime("%Y%m%d-%H%M%S")
        except Exception:
            ts_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

        return f"{clean_symbol}-{clean_tf}-{clean_dir}-{ts_str}"

    def is_duplicate(self, alert_id: str) -> bool:
        """Returns True if the alert ID has already been sent."""
        return alert_id in self._sent_alert_ids

    def register_alert(self, alert_id: str):
        """Registers alert ID into deduplication set."""
        self._sent_alert_ids.add(alert_id)

    def clear(self):
        """Clears cache."""
        self._sent_alert_ids.clear()

# Global deduplicator instance
deduplicator = SignalDeduplicator()
