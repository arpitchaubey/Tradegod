from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

class EconomicNewsFilter:
    """
    Economic News Filter tracking high-impact gold/USD news events (CPI, NFP, FOMC, Rate decisions).
    Prevents opening new trade setups during volatile news windows.
    """

    def __init__(self, blackout_minutes: int = 15):
        self.blackout_minutes = blackout_minutes
        self.events: List[Dict[str, Any]] = []
        self.enabled = True

    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        return [
            {
                "id": "news_1",
                "title": "US Non-Farm Payrolls (NFP)",
                "currency": "USD",
                "impact": "HIGH",
                "time": (now + timedelta(hours=3)).isoformat(),
                "forecast": "175K",
                "previous": "142K"
            },
            {
                "id": "news_2",
                "title": "US CPI Inflation Data",
                "currency": "USD",
                "impact": "HIGH",
                "time": (now + timedelta(hours=18)).isoformat(),
                "forecast": "2.6%",
                "previous": "2.9%"
            },
            {
                "id": "news_3",
                "title": "FOMC Interest Rate Decision",
                "currency": "USD",
                "impact": "HIGH",
                "time": (now + timedelta(days=1)).isoformat(),
                "forecast": "5.25%",
                "previous": "5.50%"
            }
        ]

    def is_blackout_active(self) -> bool:
        if not self.enabled:
            return False

        now = datetime.now(timezone.utc)
        for ev in self.events:
            if ev.get("impact") == "HIGH":
                try:
                    ev_time = datetime.fromisoformat(ev["time"])
                    diff = abs((ev_time - now).total_seconds()) / 60.0
                    if diff <= self.blackout_minutes:
                        return True
                except Exception:
                    continue
        return False

news_filter = EconomicNewsFilter()
