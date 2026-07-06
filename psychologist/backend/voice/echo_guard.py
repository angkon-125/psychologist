"""
Echo Guard

Detects when the microphone picks up ZARA's own TTS output,
preventing feedback loops and false transcript triggers.

Mechanism:
  - When TTS is speaking, the Echo Guard is "armed".
  - Incoming audio/transcript fragments are compared against
    the currently spoken text using similarity scoring.
  - If a fragment matches the spoken text above a threshold,
    it is classified as echo and discarded.
  - The guard is disarmed when TTS finishes.
"""

import logging
from typing import Optional

logger = logging.getLogger("zara.voice.echo_guard")


class EchoGuard:
    """
    Protects the voice pipeline from TTS echo feedback.

    Usage:
        guard = EchoGuard()
        guard.arm("Hello, how are you today?")
        is_echo = guard.is_echo("Hello how are you")  # True
        guard.disarm()
    """

    # Minimum word overlap ratio to classify as echo (0.0–1.0)
    SIMILARITY_THRESHOLD = 0.5

    # Minimum number of words in spoken text to activate guard
    MIN_WORDS_FOR_GUARD = 3

    def __init__(self):
        self._armed = False
        self._spoken_words: list[str] = []
        self._spoken_text: str = ""

    @property
    def is_armed(self) -> bool:
        return self._armed

    def arm(self, spoken_text: str):
        """
        Arm the echo guard with the text currently being spoken by TTS.

        Args:
            spoken_text: The full text being played through speakers.
        """
        if not spoken_text or not spoken_text.strip():
            return

        words = spoken_text.lower().split()
        if len(words) < self.MIN_WORDS_FOR_GUARD:
            # Too short to reliably detect echo — skip guard
            self._armed = False
            self._spoken_words = []
            self._spoken_text = ""
            logger.debug("Echo guard not armed: text too short (%d words)", len(words))
            return

        self._armed = True
        self._spoken_words = words
        self._spoken_text = spoken_text.lower().strip()
        logger.info("Echo guard armed (%d words)", len(words))

    def disarm(self):
        """Disarm the echo guard after TTS finishes."""
        self._armed = False
        self._spoken_words = []
        self._spoken_text = ""
        logger.debug("Echo guard disarmed")

    def is_echo(self, transcript_fragment: str) -> bool:
        """
        Check if a transcript fragment is likely echo from TTS output.

        Args:
            transcript_fragment: A partial or full transcript from the mic.

        Returns:
            True if the fragment is classified as echo (should be discarded).
        """
        if not self._armed or not self._spoken_words:
            return False

        if not transcript_fragment or not transcript_fragment.strip():
            return False

        fragment_words = transcript_fragment.lower().split()
        if not fragment_words:
            return False

        # Calculate word overlap ratio against spoken text
        spoken_set = set(self._spoken_words)
        fragment_set = set(fragment_words)

        if not fragment_set:
            return False

        overlap = fragment_set.intersection(spoken_set)
        ratio = len(overlap) / len(fragment_set)

        is_echo = ratio >= self.SIMILARITY_THRESHOLD

        if is_echo:
            logger.info(
                "Echo detected: overlap=%.2f, fragment='%s'",
                ratio,
                transcript_fragment[:60],
            )

        return is_echo

    def get_status(self) -> dict:
        """Return current echo guard status for diagnostics."""
        return {
            "armed": self._armed,
            "spoken_word_count": len(self._spoken_words),
            "spoken_text_preview": self._spoken_text[:80] if self._spoken_text else "",
        }
