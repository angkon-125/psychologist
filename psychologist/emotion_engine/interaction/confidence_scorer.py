"""
Confidence Scorer

Computes five confidence scores for every interaction:
  - transcript_confidence   (STT quality or 1.0 for text input)
  - intent_confidence       (emotion engine intensity)
  - response_confidence     (based on response source)
  - safety_confidence       (inverse of risk level)
  - tool_confidence         (tool execution success)

Provides overall weighted confidence and low-confidence flag.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger("zara.confidence")

# Weights for overall confidence calculation
_WEIGHTS = {
    "transcript": 0.15,
    "intent": 0.20,
    "response": 0.25,
    "safety": 0.25,
    "tool": 0.15,
}

# Thresholds
LOW_CONFIDENCE_THRESHOLD = 0.5
SKIP_TOOL_THRESHOLD = 0.4

# Risk level → safety confidence mapping
_RISK_SAFETY_MAP = {
    "none": 1.0,
    "low": 0.85,
    "moderate": 0.6,
    "high": 0.3,
    "critical": 0.1,
}

# Source → response confidence mapping
_SOURCE_CONFIDENCE_MAP = {
    "ollama": 0.8,
    "emotion_engine": 0.6,
    "fallback": 0.2,
    "crisis_template": 0.7,
    "text_mode": 0.6,
}


class ConfidenceScorer:
    """
    Computes confidence scores for a single interaction.

    Usage:
        scorer = ConfidenceScorer()
        scores = scorer.score(
            transcript="I feel anxious",
            emotion_result={"dominant_emotion": "fear", "emotional_state": {"intensity": 0.7}},
            safety_result={"risk_level": "low", "should_escalate": False},
            response_text="I understand anxiety can be overwhelming...",
            source="emotion_engine",
        )
    """

    def score(
        self,
        transcript: str = "",
        emotion_result: Optional[Dict] = None,
        safety_result: Optional[Dict] = None,
        response_text: str = "",
        source: str = "emotion_engine",
        input_mode: str = "text",
        stt_confidence: float = 1.0,
        tool_result: Optional[Dict] = None,
    ) -> Dict:
        """
        Compute confidence scores for an interaction.

        Returns:
            Dict with keys:
                transcript_confidence, intent_confidence, response_confidence,
                safety_confidence, tool_confidence, overall_confidence,
                is_low_confidence, needs_clarification
        """
        emotion_result = emotion_result or {}
        safety_result = safety_result or {}

        # 1. Transcript confidence
        if input_mode == "text":
            transcript_conf = 1.0
        else:
            transcript_conf = self._compute_transcript_confidence(
                transcript, stt_confidence
            )

        # 2. Intent confidence (from emotion engine intensity)
        intent_conf = self._compute_intent_confidence(emotion_result)

        # 3. Response confidence (based on source)
        response_conf = self._compute_response_confidence(source, response_text)

        # 4. Safety confidence
        safety_conf = self._compute_safety_confidence(safety_result)

        # 5. Tool confidence
        tool_conf = self._compute_tool_confidence(tool_result)

        # Overall weighted average
        overall = (
            _WEIGHTS["transcript"] * transcript_conf
            + _WEIGHTS["intent"] * intent_conf
            + _WEIGHTS["response"] * response_conf
            + _WEIGHTS["safety"] * safety_conf
            + _WEIGHTS["tool"] * tool_conf
        )
        overall = round(max(0.0, min(1.0, overall)), 3)

        is_low = overall < LOW_CONFIDENCE_THRESHOLD
        skip_tools = tool_conf < SKIP_TOOL_THRESHOLD

        return {
            "transcript_confidence": round(transcript_conf, 3),
            "intent_confidence": round(intent_conf, 3),
            "response_confidence": round(response_conf, 3),
            "safety_confidence": round(safety_conf, 3),
            "tool_confidence": round(tool_conf, 3),
            "overall_confidence": overall,
            "is_low_confidence": is_low,
            "needs_clarification": is_low,
            "skip_tool_execution": skip_tools,
        }

    # ── Internal scoring methods ─────────────────────────────────

    @staticmethod
    def _compute_transcript_confidence(transcript: str, stt_confidence: float) -> float:
        """Estimate transcript quality based on length and STT confidence."""
        if not transcript or not transcript.strip():
            return 0.0

        # Penalize very short transcripts (likely incomplete)
        word_count = len(transcript.split())
        if word_count == 1:
            length_factor = 0.5
        elif word_count <= 3:
            length_factor = 0.75
        else:
            length_factor = 1.0

        return stt_confidence * length_factor

    @staticmethod
    def _compute_intent_confidence(emotion_result: Dict) -> float:
        """Extract intent confidence from emotion engine result."""
        if not emotion_result:
            return 0.1

        # Use emotional state intensity as proxy for intent confidence
        emotional_state = emotion_result.get("emotional_state", {})
        intensity = emotional_state.get("intensity", 0.0)

        # If we have a dominant emotion with some intensity, confidence is decent
        dominant = emotion_result.get("dominant_emotion", "")
        if not dominant or dominant == "neutral":
            return max(0.1, intensity * 0.5)

        return max(0.2, min(1.0, intensity))

    @staticmethod
    def _compute_response_confidence(source: str, response_text: str) -> float:
        """Confidence based on response source and content."""
        if not response_text or not response_text.strip():
            return 0.0

        base = _SOURCE_CONFIDENCE_MAP.get(source, 0.4)

        # Penalize very short responses (might be fallback)
        if len(response_text) < 20:
            base *= 0.7

        return min(1.0, base)

    @staticmethod
    def _compute_safety_confidence(safety_result: Dict) -> float:
        """Map risk level to safety confidence."""
        if not safety_result:
            return 0.9  # No safety check = assume safe

        risk_level = safety_result.get("risk_level", "none")
        return _RISK_SAFETY_MAP.get(risk_level, 0.5)

    @staticmethod
    def _compute_tool_confidence(tool_result: Optional[Dict]) -> float:
        """Confidence in tool execution."""
        if tool_result is None:
            return 1.0  # No tool needed

        if tool_result.get("success", False):
            return 0.9
        return 0.2
