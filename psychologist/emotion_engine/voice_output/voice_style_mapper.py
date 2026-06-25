"""
Voice Style Mapper

Maps detected emotions to voice style adjustments (speed, volume, pitch, pause).
Uses the same single voice for all emotions — only prosody parameters change.
"""

from typing import Dict
from .models import VoiceStyle
from .single_voice_config import SingleVoiceConfig


class VoiceStyleMapper:
    """
    Maps an emotion name to bounded voice-style adjustments.
    The voice identity is never changed — only speed, volume,
    pitch, and pause timing are modulated within safe limits.
    """

    def __init__(self, config: SingleVoiceConfig):
        self.config = config

    def get_style(self, emotion_name: str) -> VoiceStyle:
        """
        Return a VoiceStyle for the given emotion.

        The returned multipliers are clamped so that the delta from
        the neutral baseline never exceeds the max_*_change limits
        defined in the config.
        """
        if not self.config.emotion_style_enabled:
            return self._neutral()

        style_params = self.config.get_emotion_style(emotion_name)

        speed = self._clamp(
            style_params.get("speed", 1.0),
            1.0,
            self.config.max_speed_change,
        )
        pitch = self._clamp(
            style_params.get("pitch", 1.0),
            1.0,
            self.config.max_pitch_change,
        )
        volume = self._clamp(
            style_params.get("volume", 0.9),
            0.9,
            self.config.max_volume_change,
        )
        pause = style_params.get("pause", 1.0)

        return VoiceStyle(
            emotion_name=emotion_name,
            speed_multiplier=speed,
            pitch_multiplier=pitch,
            volume_multiplier=volume,
            pause_multiplier=pause,
        )

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float, neutral: float, max_change: float) -> float:
        """Ensure value stays within [neutral - max_change, neutral + max_change]."""
        return max(neutral - max_change, min(neutral + max_change, value))

    @staticmethod
    def _neutral() -> VoiceStyle:
        return VoiceStyle(
            emotion_name="calm",
            speed_multiplier=1.0,
            pitch_multiplier=1.0,
            volume_multiplier=0.9,
            pause_multiplier=1.0,
        )
