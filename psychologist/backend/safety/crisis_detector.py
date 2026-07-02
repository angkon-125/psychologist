"""
Crisis Detector

Wraps the existing SafetySupportLayer to provide a clean interface
for the Safety Agent. Delegates all crisis/distress detection to
the battle-tested existing implementation.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("zara.safety.crisis")

# Add parent paths so we can import the existing emotion_engine modules
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class CrisisDetector:
    """
    Detects crisis and distress signals in user input.

    Delegates to the existing SafetySupportLayer for the actual detection
    logic, providing a simpler interface for the Safety Agent.
    """

    def __init__(self):
        self._safety_layer = None
        self._initialize()

    def _initialize(self):
        """Initialize by importing the existing safety layer."""
        try:
            from emotion_engine.interaction.safety_support_layer import (
                SafetySupportLayer,
            )
            self._safety_layer = SafetySupportLayer()
            logger.info("CrisisDetector initialized with existing SafetySupportLayer")
        except Exception as e:
            logger.error("Failed to initialize SafetySupportLayer: %s", e)
            self._safety_layer = None

    @property
    def available(self) -> bool:
        return self._safety_layer is not None

    def assess(self, text: str, language: str = "en") -> Dict:
        """
        Assess user input for crisis/distress signals.

        Returns:
            Dict with:
              - risk_level: "none" | "low" | "moderate" | "high" | "critical"
              - detected_signals: list of matched signals
              - should_escalate: True if crisis-level
              - recommended_response_type: "supportive" | "grounding" | "crisis_support"
              - safe_response_template: pre-written safe response (if applicable)
        """
        if not self._safety_layer:
            logger.warning("SafetySupportLayer not available — returning safe default")
            return {
                "risk_level": "none",
                "detected_signals": [],
                "should_escalate": False,
                "recommended_response_type": "supportive",
                "safe_response_template": "",
            }

        assessment = self._safety_layer.assess_input(text, language)
        return assessment.to_dict()

    def filter_response(self, response_text: str) -> str:
        """
        Filter a generated response to remove diagnosis/medical claims.

        Returns the filtered text or a safe replacement.
        """
        if not self._safety_layer:
            return response_text
        return self._safety_layer.filter_response(response_text)

    def is_safe_response(self, response_text: str) -> bool:
        """Check if a response passes safety filters."""
        if not self._safety_layer:
            return True
        return self._safety_layer.is_safe_response(response_text)

    def get_professional_help_reminder(self, language: str = "en") -> str:
        """Get a professional help reminder in the correct language."""
        if not self._safety_layer:
            return (
                "Remember, I'm here as a supportive companion, "
                "not a replacement for professional help."
            )
        return self._safety_layer.get_professional_help_reminder(language)

    def get_disclaimer(self, language: str = "en") -> str:
        """Get the system disclaimer."""
        if not self._safety_layer:
            return "This is an emotional support companion, not professional care."
        return self._safety_layer.get_disclaimer(language)
