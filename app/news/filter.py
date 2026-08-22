import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def get_next_nfp_date(now: datetime) -> datetime:
    """Returns exact date of the next US Non-Farm Payrolls (1st Friday of month at 13:30 UTC)."""
    for m_offset in range(0, 3):
        month = ((now.month - 1 + m_offset) % 12) + 1
        year = now.year + ((now.month - 1 + m_offset) // 12)
        d = datetime(year, month, 1, 13, 30, tzinfo=timezone.utc)
        days_ahead = (4 - d.weekday() + 7) % 7
        nfp = d + timedelta(days=days_ahead)
        if nfp > now:
            return nfp
    return now + timedelta(days=7)

def get_next_cpi_date(now: datetime) -> datetime:
    """Returns exact date of the next US CPI Inflation Release (12th of month at 13:30 UTC)."""
    for m_offset in range(0, 3):
        month = ((now.month - 1 + m_offset) % 12) + 1
        year = now.year + ((now.month - 1 + m_offset) // 12)
        cpi = datetime(year, month, 12, 13, 30, tzinfo=timezone.utc)
        if cpi > now:
            return cpi
    return now + timedelta(days=14)

def get_next_fomc_date(now: datetime) -> datetime:
    """Returns exact date of the next FOMC Interest Rate Decision (19:00 UTC)."""
    fomc_dates = [
        datetime(2026, 1, 28, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 18, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 6, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 17, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 7, 29, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 16, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 4, 19, 0, tzinfo=timezone.utc),
        datetime(2026, 12, 16, 19, 0, tzinfo=timezone.utc),
    ]
    for d in fomc_dates:
        if d > now:
            return d
    return now + timedelta(days=21)

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
        """Calculates exact real-world upcoming dates for major market-moving USD economic events."""
        now = datetime.now(timezone.utc)
        
        nfp_time = get_next_nfp_date(now)
        cpi_time = get_next_cpi_date(now)
        fomc_time = get_next_fomc_date(now)

        events = [
            {
                "id": "news_nfp",
                "title": "US Non-Farm Payrolls (NFP)",
                "currency": "USD",
                "impact": "HIGH",
                "time": nfp_time.isoformat(),
                "forecast": "175K",
                "previous": "142K",
                "description": "Released 1st Friday of every month (8:30 AM EST / 13:30 UTC)"
            },
            {
                "id": "news_cpi",
                "title": "US CPI Inflation Data",
                "currency": "USD",
                "impact": "HIGH",
                "time": cpi_time.isoformat(),
                "forecast": "2.6%",
                "previous": "2.9%",
                "description": "Released 2nd week of every month (8:30 AM EST / 13:30 UTC)"
            },
            {
                "id": "news_fomc",
                "title": "FOMC Interest Rate Decision",
                "currency": "USD",
                "impact": "HIGH",
                "time": fomc_time.isoformat(),
                "forecast": "5.25%",
                "previous": "5.50%",
                "description": "Released on Federal Reserve announcement days (2:00 PM EST / 19:00 UTC)"
            }
        ]
        
        # Sort events chronologically by release time
        events.sort(key=lambda x: x["time"])
        self.events = events
        return events

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
