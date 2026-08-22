from datetime import datetime, time, timezone
from typing import List, Dict, Any, Optional, Tuple

# Default blackout windows (UTC times: (start_hour, start_min), (end_hour, end_min))
DEFAULT_BLACKOUT_WINDOWS = [
    {"start": time(13, 25), "end": time(13, 45), "description": "US High-Impact Economic News Release"},
    {"start": time(18, 55), "end": time(19, 15), "description": "FOMC Rate Decision Window"}
]

def get_utc_trading_session(dt: Optional[datetime] = None) -> str:
    """
    Categorizes datetime into global trading session based on UTC hour:
      - ASIAN: 00:00 to 08:00 UTC
      - LONDON: 08:00 to 13:00 UTC
      - NEW_YORK: 13:00 to 22:00 UTC
      - OFF_HOURS: 22:00 to 24:00 UTC
    """
    check_dt = dt or datetime.now(timezone.utc)
    hour = check_dt.hour

    if 0 <= hour < 8:
        return "ASIAN"
    elif 8 <= hour < 13:
        return "LONDON"
    elif 13 <= hour < 22:
        return "NEW_YORK"
    else:
        return "OFF_HOURS"

def is_blackout_active(
    dt: Optional[datetime] = None,
    blackout_windows: Optional[List[Dict[str, Any]]] = None
) -> Tuple[bool, str]:
    """
    Checks if given UTC timestamp falls inside a news/volatility blackout window.
    Returns: (is_blackout: bool, reason: str)
    """
    check_dt = dt or datetime.now(timezone.utc)
    check_time = check_dt.time()

    windows = blackout_windows or DEFAULT_BLACKOUT_WINDOWS
    for w in windows:
        start_t = w.get("start")
        end_t = w.get("end")
        if start_t and end_t and start_t <= check_time <= end_t:
            return True, w.get("description", "High-Impact News Blackout Window")

    return False, "Clear Trading Session"
