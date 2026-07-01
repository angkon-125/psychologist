"""
Barge-In Detector

Monitors the microphone while ZARA is speaking (TTS playback).
If the user starts speaking, triggers an interruption so TTS
can be stopped and the engine returns to listening.

Detection is based on two signals:
  1. VAD-based: consecutive speech frames during playback
  2. Phrase-based: specific interruption keywords in partial transcript
"""

import numpy as np
from typing import Optional, List, Dict
import logging

logger = logging.getLogger("zara.voice.barge_in")

# Default interruption phrases (lowercase)
_DEFAULT_INTERRUPTION_PHRASES = [
    "stop", "wait", "hold on", "cancel", "zara",
    "that's all", "never mind", "skip",
]


class BargeInDetector:
    """
    Detects user interruptions during TTS playback.

    Usage:
        detector = BargeInDetector(min_speech_frames=3)
        detector.reset()
        # During TTS playback, feed audio frames:
        for chunk in audio_stream:
            if detector.process_audio(chunk):
                # User interrupted! Stop TTS.
                break
    """

    def __init__(
        self,
        min_speech_frames: int = 3,
        interruption_phrases: Optional[List[str]] = None,
        enabled: bool = True,
    ):
        self._min_speech_frames = min_speech_frames
        self._phrases = interruption_phrases or _DEFAULT_INTERRUPTION_PHRASES
        self._enabled = enabled

        self._consecutive_speech = 0
        self._total_speech_frames = 0
        self._interrupted = False

        # VAD
        self._vad = None
        self._init_vad()

    def _init_vad(self):
        """Initialize VAD for speech detection."""
        try:
            from ..voice_system.vad import VoiceActivityDetector
            self._vad = VoiceActivityDetector(mode=3, sample_rate=16000, frame_duration_ms=30)
        except Exception as e:
            logger.warning("Barge-in VAD not available: %s", e)

    # ── Public API ─────────────────────────────────────────────────

    def reset(self):
        """Reset detector state for a new speaking session."""
        self._consecutive_speech = 0
        self._total_speech_frames = 0
        self._interrupted = False

    @property
    def is_interrupted(self) -> bool:
        return self._interrupted

    def process_audio(self, audio: np.ndarray) -> bool:
        """
        Process one audio frame during TTS playback.

        Returns True if an interruption is detected (enough consecutive
        speech frames to confirm the user is speaking).
        """
        if not self._enabled or self._interrupted:
            return False

        is_speech = self._detect_speech(audio)

        if is_speech:
            self._consecutive_speech += 1
            self._total_speech_frames += 1
        else:
            # Reset consecutive counter on silence
            self._consecutive_speech = 0

        if self._consecutive_speech >= self._min_speech_frames:
            self._interrupted = True
            logger.info(
                "Barge-in detected: %d consecutive speech frames",
                self._consecutive_speech,
            )
            return True

        return False

    def check_phrase(self, transcript: str) -> bool:
        """
        Check if a partial/final transcript contains an interruption phrase.

        Returns True if the transcript matches an interruption keyword.
        """
        if not self._enabled or self._interrupted:
            return False

        text_lower = transcript.lower().strip()
        for phrase in self._phrases:
            if phrase in text_lower:
                self._interrupted = True
                logger.info("Barge-in phrase detected: '%s'", phrase)
                return True

        return False

    # ── Configuration ──────────────────────────────────────────────

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            self.reset()

    def update_config(self, config: Dict):
        """
        Update barge-in configuration at runtime.

        Args:
            config: dict with optional keys:
                - enabled: bool
                - min_speech_frames: int
                - interruption_phrases: list[str]
        """
        if "enabled" in config:
            self._enabled = config["enabled"]
        if "min_speech_frames" in config:
            self._min_speech_frames = max(1, int(config["min_speech_frames"]))
        if "interruption_phrases" in config:
            self._phrases = [p.lower().strip() for p in config["interruption_phrases"]]
        logger.info(
            "Barge-in config updated: enabled=%s, min_frames=%d, phrases=%d",
            self._enabled, self._min_speech_frames, len(self._phrases),
        )

    def get_config(self) -> Dict:
        """Return current configuration."""
        return {
            "enabled": self._enabled,
            "min_speech_frames": self._min_speech_frames,
            "interruption_phrases": list(self._phrases),
        }

    # ── Internal ───────────────────────────────────────────────────

    def _detect_speech(self, audio: np.ndarray) -> bool:
        """Detect speech in an audio frame."""
        if self._vad is not None:
            try:
                return self._vad.is_speech(audio)
            except Exception:
                pass
        # Energy-based fallback
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > 0.03  # slightly higher threshold during playback
