"""
Confidence Engine — Executive Brain

Fuses confidence values from multiple sources and determines
the appropriate response strategy:
  - >0.90: respond normally
  - 0.70-0.90: respond with minor uncertainty
  - 0.40-0.70: ask one clarification question
  - <0.40: explain what information is missing
"""

import logging
from typing import Dict, List, Optional

from .schemas import ConfidenceReport

logger = logging.getLogger("zara.executive.confidence")

# Weights for confidence fusion
_WEIGHT_INTENT = 0.30
_WEIGHT_AGENT = 0.40
_WEIGHT_CONTEXT = 0.15
_WEIGHT_PLAN = 0.15

# Thresholds
_THRESHOLD_HIGH = 0.90
_THRESHOLD_MEDIUM = 0.70
_THRESHOLD_LOW = 0.40


class ConfidenceEngine:
    """
    Fuses confidence from multiple cognitive sources.

    Usage:
        engine = ConfidenceEngine()
        report = engine.fuse(
            intent_confidence=0.85,
            agent_confidence=0.90,
            context_quality=0.70,
            plan_confidence=0.80,
        )
    """

    def fuse(
        self,
        intent_confidence: float = 0.5,
        agent_confidence: float = 0.5,
        context_quality: float = 0.0,
        plan_confidence: float = 0.5,
        agent_confidences: Optional[Dict[str, float]] = None,
        missing_information: Optional[List[str]] = None,
    ) -> ConfidenceReport:
        """
        Fuse confidence from all sources into a single report.

        Args:
            intent_confidence: Confidence from intent classification (0-1)
            agent_confidence: Confidence from the primary agent response (0-1)
            context_quality: Quality of retrieved context (0-1)
            plan_confidence: Estimated confidence from the execution plan (0-1)
            agent_confidences: Per-agent confidence dict (for multi-agent)
            missing_information: List of missing information items

        Returns:
            ConfidenceReport with overall confidence and recommendation
        """
        # Clamp inputs
        intent_confidence = max(0.0, min(1.0, intent_confidence))
        agent_confidence = max(0.0, min(1.0, agent_confidence))
        context_quality = max(0.0, min(1.0, context_quality))
        plan_confidence = max(0.0, min(1.0, plan_confidence))

        # Weighted fusion
        overall = (
            intent_confidence * _WEIGHT_INTENT
            + agent_confidence * _WEIGHT_AGENT
            + context_quality * _WEIGHT_CONTEXT
            + plan_confidence * _WEIGHT_PLAN
        )
        overall = max(0.0, min(1.0, overall))

        # Determine recommendation
        recommendation = self._recommend(overall, missing_information or [])

        report = ConfidenceReport(
            overall_confidence=round(overall, 4),
            agent_confidences=agent_confidences or {"primary": agent_confidence},
            missing_information=missing_information or [],
            recommendation=recommendation,
        )

        logger.debug(
            "Confidence: overall=%.4f, intent=%.2f, agent=%.2f, "
            "context=%.2f, plan=%.2f -> %s",
            overall, intent_confidence, agent_confidence,
            context_quality, plan_confidence, recommendation,
        )
        return report

    def _recommend(self, confidence: float, missing: List[str]) -> str:
        """Determine response recommendation based on confidence level."""
        if confidence > _THRESHOLD_HIGH:
            return "respond"
        elif confidence > _THRESHOLD_MEDIUM:
            return "respond_uncertain"
        elif confidence > _THRESHOLD_LOW:
            return "clarify"
        else:
            return "explain_missing"

    def should_clarify(self, report: ConfidenceReport) -> bool:
        """Whether the executive should ask a clarification question."""
        return report.recommendation == "clarify"

    def generate_clarification_prompt(
        self, report: ConfidenceReport, original_text: str
    ) -> str:
        """
        Generate a clarification question based on missing information.

        Returns a natural-language clarification prompt.
        """
        if report.missing_information:
            items = ", ".join(report.missing_information[:3])
            return (
                f"I want to help with that. Could you clarify: {items}? "
                f"That will help me give you a better answer."
            )

        # Generic clarification based on confidence
        if report.overall_confidence < _THRESHOLD_LOW:
            return (
                "I'm not sure I fully understood your request. "
                "Could you provide a bit more detail about what you need?"
            )
        return (
            "I want to make sure I understand correctly. "
            "Could you tell me a bit more about what you're looking for?"
        )

    def generate_missing_explanation(self, report: ConfidenceReport) -> str:
        """
        Generate an explanation of what information is missing
        when confidence is too low to respond.
        """
        if not report.missing_information:
            return (
                "I don't have enough information to answer that confidently. "
                "Could you provide more context or rephrase your question?"
            )

        items = report.missing_information
        if len(items) == 1:
            return f"I need to know {items[0]} before I can help with that."
        item_str = "; ".join(items[:3])
        return (
            f"I'm missing some key information: {item_str}. "
            f"Once you share those details, I'll be able to help properly."
        )
