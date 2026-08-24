import json
import os
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("omni_preferences")

PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "omni_preferences.json")

class OmniPreferences(BaseModel):
    preferred_lot_size: float = Field(default=0.10, ge=0.01, le=100.0)
    min_profit_pips: float = Field(default=30.0, ge=5.0, le=1000.0)
    max_risk_percent: float = Field(default=2.0, ge=0.1, le=10.0)
    min_confidence_score: int = Field(default=75, ge=50, le=99)
    min_risk_reward_ratio: float = Field(default=1.5, ge=1.0, le=10.0)
    entry_preference: str = Field(default="AI_ADAPTIVE")  # "INSTANT_MARKET", "SNIPER_PULLBACK", "AI_ADAPTIVE"
    bot_active: bool = Field(default=True)
    telegram_notifications: bool = Field(default=True)
    notify_on_news_blackout: bool = Field(default=True)
    max_positions: int = Field(default=3, ge=1, le=20)
    scan_interval_seconds: int = Field(default=15, ge=5, le=300)

class OmniPreferencesStore:
    def __init__(self):
        self._preferences = OmniPreferences()
        self._load()

    def _load(self):
        try:
            if os.path.exists(PREFERENCES_FILE):
                with open(PREFERENCES_FILE, "r") as f:
                    data = json.load(f)
                    self._preferences = OmniPreferences(**data)
                logger.info(f"Loaded Omni Preferences: lot={self._preferences.preferred_lot_size}, min_pips={self._preferences.min_profit_pips}")
        except Exception as e:
            logger.warning(f"Using default preferences due to load error: {e}")

    def get_preferences(self) -> OmniPreferences:
        return self._preferences

    def update_preferences(self, new_prefs: OmniPreferences) -> OmniPreferences:
        self._preferences = new_prefs
        try:
            with open(PREFERENCES_FILE, "w") as f:
                json.dump(self._preferences.model_dump(), f, indent=2)
            logger.info("Saved updated Omni Preferences to disk.")
        except Exception as e:
            logger.error(f"Failed to persist preferences: {e}")
        return self._preferences

omni_preferences_store = OmniPreferencesStore()
