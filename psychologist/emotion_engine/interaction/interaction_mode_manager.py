"""
Interaction Mode Manager

Manages the current interaction mode (TEXT / VOICE / HYBRID),
validates mode switching, and provides mode-specific configuration.
"""

from typing import Optional, Callable, List
from datetime import datetime

from .interaction_models import (
    InteractionMode,
    InteractionModeConfig,
)


class InteractionModeManager:
    """Manages interaction mode state and transitions."""

    # Pre-built configs for each mode
    MODE_CONFIGS = {
        InteractionMode.TEXT: InteractionModeConfig(
            mode_name="text",
            voice_input_enabled=False,
            text_input_enabled=True,
            voice_output_enabled=True,   # optional TTS readout
            auto_listen_after_response=False,
        ),
        InteractionMode.VOICE: InteractionModeConfig(
            mode_name="voice",
            voice_input_enabled=True,
            text_input_enabled=False,
            voice_output_enabled=True,
            auto_listen_after_response=False,
        ),
        InteractionMode.HYBRID: InteractionModeConfig(
            mode_name="hybrid",
            voice_input_enabled=True,
            text_input_enabled=True,
            voice_output_enabled=True,
            auto_listen_after_response=False,
        ),
    }

    def __init__(self, default_mode: str = "hybrid"):
        self._current_mode = self._parse_mode(default_mode)
        self._mode_history: List[dict] = []
        self._activity_callback: Optional[Callable[[str], None]] = None
        self._allowed_modes = {
            InteractionMode.TEXT,
            InteractionMode.VOICE,
            InteractionMode.HYBRID,
        }

    # ── Mode access ──────────────────────────────────────────────

    @property
    def current_mode(self) -> InteractionMode:
        return self._current_mode

    @property
    def current_config(self) -> InteractionModeConfig:
        return self.MODE_CONFIGS[self._current_mode]

    def get_mode_name(self) -> str:
        return self._current_mode.value

    # ── Mode switching ───────────────────────────────────────────

    def switch_mode(self, mode_name: str) -> dict:
        """
        Switch to a new interaction mode.
        Returns a status dict with success flag and the new mode config.
        """
        new_mode = self._parse_mode(mode_name)

        if new_mode not in self._allowed_modes:
            return {
                "success": False,
                "error": f"Mode '{mode_name}' is not allowed.",
                "current_mode": self._current_mode.value,
            }

        old_mode = self._current_mode
        self._current_mode = new_mode

        self._mode_history.append({
            "from_mode": old_mode.value,
            "to_mode": new_mode.value,
            "timestamp": datetime.now().isoformat(),
        })

        activity_text = f"Switched to {new_mode.value} mode"
        self._log_activity(activity_text)

        return {
            "success": True,
            "previous_mode": old_mode.value,
            "current_mode": new_mode.value,
            "config": self.current_config.to_dict(),
        }

    def set_allowed_modes(
        self,
        allow_text: bool = True,
        allow_voice: bool = True,
        allow_hybrid: bool = True,
    ):
        """Update which modes are available based on config."""
        self._allowed_modes = set()
        if allow_text:
            self._allowed_modes.add(InteractionMode.TEXT)
        if allow_voice:
            self._allowed_modes.add(InteractionMode.VOICE)
        if allow_hybrid:
            self._allowed_modes.add(InteractionMode.HYBRID)

    # ── Query helpers ────────────────────────────────────────────

    def is_text_input_enabled(self) -> bool:
        return self.current_config.text_input_enabled

    def is_voice_input_enabled(self) -> bool:
        return self.current_config.voice_input_enabled

    def is_voice_output_enabled(self) -> bool:
        return self.current_config.voice_output_enabled

    def should_auto_listen(self) -> bool:
        return self.current_config.auto_listen_after_response

    def get_max_response_length(self, is_voice: bool = False) -> int:
        """Voice responses should be shorter than text responses."""
        if is_voice or self._current_mode == InteractionMode.VOICE:
            return 200
        return 500

    def get_status(self) -> dict:
        return {
            "current_mode": self._current_mode.value,
            "config": self.current_config.to_dict(),
            "allowed_modes": [m.value for m in self._allowed_modes],
            "mode_history_count": len(self._mode_history),
        }

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Internal ─────────────────────────────────────────────────

    @staticmethod
    def _parse_mode(mode_name: str) -> InteractionMode:
        mode_name = mode_name.strip().lower()
        mode_map = {
            "text": InteractionMode.TEXT,
            "voice": InteractionMode.VOICE,
            "hybrid": InteractionMode.HYBRID,
        }
        return mode_map.get(mode_name, InteractionMode.HYBRID)
