"""
Wake Word Detector (Stub)

Placeholder for OpenWakeWord integration (future phase).
Currently returns False for all detections and reports as unavailable.

When OpenWakeWord is integrated, only this file needs to change.
The ConversationEngine already references this class.
"""

import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger("zara.voice.wake_word")


class WakeWordDetector:
    """
    Placeholder for wake word detection.

    Future implementation will use OpenWakeWord to detect:
      - "Zara"
      - "Hey Zara"
      - "Okay Zara"
      - "Hello Zara"
    """

    def __init__(self):
        self._available = False
        self._enabled = False
        self._wake_phrases = ["zara", "hey zara", "okay zara", "hello zara"]
        logger.info("Wake word detector: stub (not yet available)")

    def is_available(self) -> bool:
        """Whether the wake word engine is loaded and ready."""
        return self._available

    def set_enabled(self, enabled: bool):
        """Enable or disable wake word detection."""
        self._enabled = enabled and self._available

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self):
        """Start wake word detection loop. No-op in stub."""
        if not self._available:
            logger.debug("Wake word detector not available, start() is no-op")

    def stop(self):
        """Stop wake word detection. No-op in stub."""
        pass

    def detect(self, audio: np.ndarray) -> bool:
        """
        Check if the audio contains a wake word.

        Always returns False in the stub implementation.
        """
        return False

    def get_config(self) -> Dict:
        """Return wake word configuration."""
        return {
            "available": self._available,
            "enabled": self._enabled,
            "wake_phrases": list(self._wake_phrases),
        }
