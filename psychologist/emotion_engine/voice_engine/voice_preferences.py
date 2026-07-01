"""
Voice Preferences

Persists user voice settings locally as JSON.
Stores: preferred voice, speech speed, volume, language,
wake word enabled, continuous listening, push-to-talk, pause thresholds.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("zara.voice.preferences")

_DEFAULT_PREFERENCES = {
    "voice_id": "default",
    "speech_speed": 1.0,
    "volume": 0.9,
    "language": "en",
    "wake_word_enabled": False,
    "continuous_listening": False,
    "push_to_talk": True,
    "auto_return_to_listening": True,
    "pause_thresholds": {
        "short_pause_max_ms": 700,
        "thinking_pause_max_ms": 2500,
        "long_pause_max_ms": 4500,
    },
    "barge_in_enabled": True,
}


class VoicePreferences:
    """
    Load and save voice preferences to a local JSON file.

    Usage:
        prefs = VoicePreferences()
        prefs.set("speech_speed", 1.2)
        prefs.save()
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self._path = Path(config_path)
        else:
            self._path = Path(__file__).parent.parent.parent / "config" / "voice_preferences.json"

        self._prefs: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load preferences from disk, or initialize with defaults."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._prefs = {**_DEFAULT_PREFERENCES, **loaded}
                # Merge nested dicts
                if "pause_thresholds" in loaded:
                    self._prefs["pause_thresholds"] = {
                        **_DEFAULT_PREFERENCES["pause_thresholds"],
                        **loaded["pause_thresholds"],
                    }
                logger.info("Voice preferences loaded from %s", self._path)
            except Exception as e:
                logger.warning("Could not load voice preferences: %s", e)
                self._prefs = dict(_DEFAULT_PREFERENCES)
        else:
            self._prefs = dict(_DEFAULT_PREFERENCES)
            self.save()  # Write defaults

    def save(self):
        """Persist current preferences to disk."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning("Could not save voice preferences: %s", e)

    # ── Access ─────────────────────────────────────────────────────

    def get(self, key: str, default=None) -> Any:
        """Get a preference value by key (supports dotted paths)."""
        keys = key.split(".")
        value = self._prefs
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set a preference value. Call save() to persist."""
        keys = key.split(".")
        target = self._prefs
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """Return all preferences as a dict."""
        return dict(self._prefs)

    def update(self, updates: Dict[str, Any]):
        """Update multiple preferences at once."""
        for key, value in updates.items():
            self.set(key, value)

    # ── Convenience properties ─────────────────────────────────────

    @property
    def speech_speed(self) -> float:
        return float(self.get("speech_speed", 1.0))

    @speech_speed.setter
    def speech_speed(self, value: float):
        self.set("speech_speed", max(0.5, min(2.0, float(value))))

    @property
    def volume(self) -> float:
        return float(self.get("volume", 0.9))

    @volume.setter
    def volume(self, value: float):
        self.set("volume", max(0.0, min(1.0, float(value))))

    @property
    def language(self) -> str:
        return self.get("language", "en")

    @language.setter
    def language(self, value: str):
        self.set("language", value)

    @property
    def pause_thresholds(self) -> Dict[str, int]:
        return dict(self.get("pause_thresholds", _DEFAULT_PREFERENCES["pause_thresholds"]))

    @property
    def continuous_listening(self) -> bool:
        return bool(self.get("continuous_listening", False))

    @property
    def push_to_talk(self) -> bool:
        return bool(self.get("push_to_talk", True))

    @property
    def barge_in_enabled(self) -> bool:
        return bool(self.get("barge_in_enabled", True))
