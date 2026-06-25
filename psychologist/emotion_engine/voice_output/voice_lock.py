"""
Voice Lock System

Prevents voice identity changes at runtime.
Once locked, the voice cannot be changed by user commands,
emotion changes, or UI actions unless developer mode is enabled.
"""

import threading
from typing import Optional


class VoiceLock:
    """
    Guards the active voice identity so that it cannot be replaced
    after startup.  Only developer-mode unlock allows mutation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._locked: bool = False
        self._voice_id: str = "default_local_voice"
        self._engine_name: str = "piper"
        self._developer_mode: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────

    def lock(self, voice_id: str, engine_name: str) -> None:
        """Lock the voice to a specific identity. Called once at startup."""
        with self._lock:
            self._voice_id = voice_id
            self._engine_name = engine_name
            self._locked = True

    def unlock_developer(self) -> None:
        """Unlock only for developer/debug purposes."""
        with self._lock:
            self._developer_mode = True

    def lock_developer(self) -> None:
        """Re-lock after developer operations."""
        with self._lock:
            self._developer_mode = False

    # ── Query ─────────────────────────────────────────────────────

    @property
    def is_locked(self) -> bool:
        return self._locked and not self._developer_mode

    @property
    def voice_id(self) -> str:
        return self._voice_id

    @property
    def engine_name(self) -> str:
        return self._engine_name

    @property
    def developer_mode(self) -> bool:
        return self._developer_mode

    # ── Validation ────────────────────────────────────────────────

    def validate_voice_change(self, requested_voice_id: Optional[str] = None,
                               requested_engine: Optional[str] = None) -> bool:
        """
        Return True if the requested change is allowed.
        When locked, only the current voice_id/engine are valid.
        """
        if not self._locked or self._developer_mode:
            return True

        if requested_voice_id is not None and requested_voice_id != self._voice_id:
            return False

        if requested_engine is not None and requested_engine != self._engine_name:
            return False

        return True

    def validate_emotion_change(self, emotion_name: str) -> bool:
        """
        Emotion changes are always allowed — they affect style
        (speed/volume/pacing) but never the voice identity.
        """
        return True

    def get_status(self) -> dict:
        return {
            "locked": self._locked,
            "voice_id": self._voice_id,
            "engine_name": self._engine_name,
            "developer_mode": self._developer_mode,
            "label": "Local Voice Locked" if self.is_locked else "Voice Unlocked",
        }
