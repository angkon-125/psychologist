"""
Correction Detector

Detects user correction phrases (e.g. "No, I meant...", "Wrong",
"That's not correct") and stores correction events for analysis.

Correction events are persisted to config/corrections.jsonl and can
be used to improve intent detection, pause thresholds, response style,
and mode routing.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("zara.correction")

# Correction phrases (English + Bangla)
_CORRECTION_PHRASES_EN = [
    "no, i meant",
    "no i meant",
    "wrong",
    "that's not correct",
    "thats not correct",
    "that is not correct",
    "you misunderstood",
    "you misunderstood me",
    "not that",
    "no, i said",
    "no i said",
    "i didn't say that",
    "i didnt say that",
    "i meant",
    "stop",
    "no, stop",
    "you got it wrong",
    "that's wrong",
    "thats wrong",
    "not what i meant",
    "i didn't mean that",
    "i didnt mean that",
    "let me rephrase",
    "what i actually meant",
]

_CORRECTION_PHRASES_BN = [
    "না",
    "ভুল",
    "আমি সেটা বলিনি",
    "আমি তা বলিনি",
    "ভুল বুঝেছো",
    "ঠিক না",
    "সেটা না",
    "আমার কথা হলো",
]

# Correction types
_TYPE_CORRECTION = "correction"
_TYPE_CLARIFICATION = "clarification"
_TYPE_REJECTION = "rejection"
_TYPE_REPHRASE = "rephrase"


class CorrectionDetector:
    """
    Detects user corrections in text input.

    Usage:
        detector = CorrectionDetector()
        result = detector.detect("No, I meant I'm anxious, not angry")
        # result = {"is_correction": True, "correction_type": "correction", ...}
    """

    def __init__(self, corrections_path: Optional[str] = None):
        if corrections_path:
            self._path = Path(corrections_path)
        else:
            self._path = Path(__file__).parent.parent.parent / "config" / "corrections.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Build regex patterns for fast matching
        self._patterns_en = [
            re.compile(re.escape(phrase), re.IGNORECASE)
            for phrase in _CORRECTION_PHRASES_EN
        ]
        self._patterns_bn = [
            re.compile(re.escape(phrase))
            for phrase in _CORRECTION_PHRASES_BN
        ]

    def detect(self, text: str, language: str = "en") -> Dict:
        """
        Check if the input text is a correction.

        Returns:
            Dict with keys:
                is_correction: bool
                correction_type: str or None
                original_phrase: str or None
                confidence: float (0-1)
        """
        if not text or not text.strip():
            return self._no_correction()

        text_lower = text.strip().lower()

        # Check English patterns
        if language in ("en", "hybrid"):
            for phrase, pattern in zip(_CORRECTION_PHRASES_EN, self._patterns_en):
                if pattern.search(text_lower):
                    ctype = self._classify_type(text_lower, phrase)
                    return {
                        "is_correction": True,
                        "correction_type": ctype,
                        "original_phrase": phrase,
                        "confidence": self._phrase_confidence(phrase),
                    }

        # Check Bangla patterns
        if language in ("bn", "bn_bd", "hybrid"):
            for phrase, pattern in zip(_CORRECTION_PHRASES_BN, self._patterns_bn):
                if pattern.search(text):
                    return {
                        "is_correction": True,
                        "correction_type": _TYPE_CORRECTION,
                        "original_phrase": phrase,
                        "confidence": 0.7,
                    }

        return self._no_correction()

    def store_correction(
        self,
        text: str,
        detection_result: Dict,
        detected_intent: str = "",
        context: Optional[str] = None,
    ):
        """Store a correction event to the corrections log file."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "original_input": text,
            "correction_type": detection_result.get("correction_type", "unknown"),
            "matched_phrase": detection_result.get("original_phrase", ""),
            "detected_intent": detected_intent,
            "confidence": detection_result.get("confidence", 0.0),
            "context": context or "",
        }
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            logger.info("Stored correction event: %s", detection_result.get("correction_type"))
        except Exception as e:
            logger.warning("Failed to store correction: %s", e)

    def get_correction_count(self) -> int:
        """Return the total number of stored corrections."""
        try:
            if not self._path.exists():
                return 0
            count = 0
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except Exception:
            return 0

    def get_recent_corrections(self, n: int = 10) -> List[Dict]:
        """Return the last N correction events."""
        try:
            if not self._path.exists():
                return []
            lines = []
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            lines.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            return lines[-n:]
        except Exception:
            return []

    # ── Internal helpers ─────────────────────────────────────────

    @staticmethod
    def _no_correction() -> Dict:
        return {
            "is_correction": False,
            "correction_type": None,
            "original_phrase": None,
            "confidence": 0.0,
        }

    @staticmethod
    def _classify_type(text: str, matched_phrase: str) -> str:
        """Classify the type of correction."""
        if any(w in text for w in ["i meant", "let me rephrase", "what i actually"]):
            return _TYPE_REPHRASE
        if any(w in text for w in ["stop", "no, stop"]):
            return _TYPE_REJECTION
        if any(w in text for w in ["not what i meant", "you got it wrong", "wrong", "not correct", "misunderstood"]):
            return _TYPE_CORRECTION
        return _TYPE_CLARIFICATION

    @staticmethod
    def _phrase_confidence(phrase: str) -> float:
        """Assign confidence based on how specific the matched phrase is."""
        # Longer, more specific phrases get higher confidence
        if len(phrase) > 15:
            return 0.95
        elif len(phrase) > 8:
            return 0.85
        elif phrase in ("wrong", "stop", "not that"):
            return 0.6  # Short phrases could be ambiguous
        return 0.7
