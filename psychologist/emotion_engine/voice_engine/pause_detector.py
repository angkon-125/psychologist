"""
Smart Pause Detector

Classifies silence duration during listening into meaningful categories:
  - SPEECH:          user is actively speaking
  - SHORT_PAUSE:     brief pause (0–1000 ms), keep listening silently
  - THINKING_PAUSE:  normal thinking pause (1000–3500 ms), show "Take your time"
  - LONG_PAUSE:      long pause (3500–6000 ms), prepare to finish
  - FINISHED:        user has finished speaking (>6000 ms silence)

All thresholds are configurable via voice_config.yaml.
"""

import time
import numpy as np
from enum import Enum
from typing import Optional, Dict
import logging

logger = logging.getLogger("zara.voice.pause_detector")


class PauseState(Enum):
    """Result of analyzing the current audio frame."""
    SPEECH = "speech"
    SHORT_PAUSE = "short_pause"
    THINKING_PAUSE = "thinking_pause"
    LONG_PAUSE = "long_pause"
    FINISHED = "finished"


# Default thresholds in milliseconds
_DEFAULT_THRESHOLDS = {
    "short_pause_max_ms": 1000,
    "thinking_pause_max_ms": 3500,
    "long_pause_max_ms": 6000,
    "noise_threshold": 0.02,
}

# Messages shown to the user for each pause state
_PAUSE_MESSAGES: Dict[PauseState, str] = {
    PauseState.SPEECH: "",
    PauseState.SHORT_PAUSE: "I'm listening...",
    PauseState.THINKING_PAUSE: "Take your time.",
    PauseState.LONG_PAUSE: "I'm still here. Let me know when you're ready.",
    PauseState.FINISHED: "",
}


class SmartPauseDetector:
    """
    Wraps a VAD (VoiceActivityDetector) with time-based pause classification.

    Usage:
        detector = SmartPauseDetector(thresholds={...})
        detector.reset()
        for audio_chunk in audio_stream:
            state = detector.process_frame(audio_chunk, sample_rate=16000)
            if state == PauseState.FINISHED:
                # user finished speaking
    """

    def __init__(self, thresholds: Optional[Dict[str, int]] = None):
        cfg = {**_DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._short_max_s = cfg["short_pause_max_ms"] / 1000.0
        self._thinking_max_s = cfg["thinking_pause_max_ms"] / 1000.0
        self._long_max_s = cfg["long_pause_max_ms"] / 1000.0

        # Noise threshold for energy-based speech detection
        self._noise_threshold = cfg.get("noise_threshold", 0.02)

        # Internal tracking
        self._speech_detected = False
        self._silence_start: Optional[float] = None
        self._total_speech_frames = 0
        self._total_silence_frames = 0

        # Lazy-import VAD
        self._vad = None
        self._init_vad()

    def _init_vad(self):
        """Initialize the underlying VAD (webrtcvad)."""
        try:
            from ..voice_system.vad import VoiceActivityDetector
            self._vad = VoiceActivityDetector(mode=3, sample_rate=16000, frame_duration_ms=30)
        except Exception as e:
            logger.warning("VAD not available, using energy-based fallback: %s", e)
            self._vad = None

    # ── Public API ─────────────────────────────────────────────────

    def reset(self):
        """Reset all internal state for a new listening session."""
        self._speech_detected = False
        self._silence_start = None
        self._total_speech_frames = 0
        self._total_silence_frames = 0

    def process_frame(self, audio: np.ndarray, sample_rate: int = 16000) -> PauseState:
        """
        Process one audio frame and return the current pause state.

        This method should be called for each audio chunk captured from
        the microphone (typically every 20–100 ms).
        """
        is_speech = self._detect_speech(audio, sample_rate)

        if is_speech:
            self._on_speech()
            return PauseState.SPEECH
        else:
            return self._on_silence()

    @property
    def silence_duration_ms(self) -> float:
        """Current silence duration in milliseconds (0 if not in silence)."""
        if self._silence_start is None:
            return 0.0
        return (time.monotonic() - self._silence_start) * 1000.0

    @property
    def message(self) -> str:
        """Human-readable message for the current pause state."""
        dur_s = self.silence_duration_ms / 1000.0
        if dur_s < self._short_max_s:
            return _PAUSE_MESSAGES[PauseState.SHORT_PAUSE]
        elif dur_s < self._thinking_max_s:
            return _PAUSE_MESSAGES[PauseState.THINKING_PAUSE]
        elif dur_s < self._long_max_s:
            return _PAUSE_MESSAGES[PauseState.LONG_PAUSE]
        return ""

    # ── Internal ───────────────────────────────────────────────────

    def _detect_speech(self, audio: np.ndarray, sample_rate: int) -> bool:
        """Detect whether the audio frame contains speech."""
        if self._vad is not None:
            try:
                return self._vad.is_speech(audio)
            except Exception:
                pass
        # Energy-based fallback
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > self._noise_threshold  # configurable energy threshold

    def _on_speech(self):
        """Called when speech is detected in the current frame."""
        self._speech_detected = True
        self._silence_start = None
        self._total_speech_frames += 1

    def _on_silence(self) -> PauseState:
        """Called when silence is detected; classify the pause duration."""
        self._total_silence_frames += 1

        # If no speech was ever detected, just keep waiting
        if not self._speech_detected:
            return PauseState.SHORT_PAUSE

        # Start tracking silence
        if self._silence_start is None:
            self._silence_start = time.monotonic()

        dur_s = time.monotonic() - self._silence_start

        if dur_s < self._short_max_s:
            return PauseState.SHORT_PAUSE
        elif dur_s < self._thinking_max_s:
            return PauseState.THINKING_PAUSE
        elif dur_s < self._long_max_s:
            return PauseState.LONG_PAUSE
        else:
            return PauseState.FINISHED

    # ── Configuration ──────────────────────────────────────────────

    def update_thresholds(self, thresholds: Dict[str, int]):
        """
        Update pause thresholds at runtime.

        Args:
            thresholds: dict with keys like 'short_pause_max_ms', etc.
        """
        if "short_pause_max_ms" in thresholds:
            self._short_max_s = thresholds["short_pause_max_ms"] / 1000.0
        if "thinking_pause_max_ms" in thresholds:
            self._thinking_max_s = thresholds["thinking_pause_max_ms"] / 1000.0
        if "long_pause_max_ms" in thresholds:
            self._long_max_s = thresholds["long_pause_max_ms"] / 1000.0
        logger.info(
            "Pause thresholds updated: short=%.1fs, thinking=%.1fs, long=%.1fs",
            self._short_max_s, self._thinking_max_s, self._long_max_s,
        )

    def get_thresholds(self) -> Dict[str, int]:
        """Return current thresholds in milliseconds."""
        return {
            "short_pause_max_ms": int(self._short_max_s * 1000),
            "thinking_pause_max_ms": int(self._thinking_max_s * 1000),
            "long_pause_max_ms": int(self._long_max_s * 1000),
        }
