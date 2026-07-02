"""
Transcript Manager

Responsible for managing live transcription accumulating segments.
"""

import logging
from typing import List

logger = logging.getLogger("zara.voice.transcript")

class TranscriptManager:
    """Manages active transcriptions, segments, and corrections."""

    def __init__(self):
        self._segments: List[str] = []

    def add_segment(self, segment: str):
        if segment and segment.strip():
            self._segments.append(segment.strip())

    def get_full_transcript(self) -> str:
        return " ".join(self._segments)

    def clear(self):
        self._segments.clear()
        logger.debug("Transcript cleared.")
