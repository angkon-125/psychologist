"""
Safety Support Layer

Detects crisis signals, blocks diagnosis/medical claims,
and provides safe response templates.

Uses keyword-based matching only — no ML, no LLM, no cloud.
"""

import os
import re
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable

import yaml

from .interaction_models import SafetyAssessment, RiskLevel

logger = logging.getLogger("zara.safety")


class SafetySupportLayer:
    """
    Safety checks for all user input before response generation.

    Risk levels:
      NONE     — no concern detected
      LOW      — mild distress language
      MODERATE — notable distress, offer support tools
      HIGH     — crisis signals detected, switch to crisis response
      CRITICAL — immediate danger, strong crisis messaging
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = (
                Path(__file__).parent.parent.parent / "config" / "safety_config.yaml"
            )
        self._config: Dict = {}
        self._crisis_keywords: Dict = {}
        self._diagnosis_patterns: List[str] = []
        self._safe_templates: Dict = {}
        self._activity_callback: Optional[Callable[[str], None]] = None
        self._load_config()

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Config loading ───────────────────────────────────────────

    def _load_config(self):
        """Load safety configuration from YAML."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError) as e:
                logger.warning("Failed to load safety config: %s", e)
                self._config = {}
            except ValueError as e:
                logger.warning("Invalid safety config format: %s", e)
                self._config = {}

        self._crisis_keywords = self._config.get("crisis_keywords", {})
        self._diagnosis_patterns = self._config.get("diagnosis_block_patterns", [])
        self._safe_templates = self._config.get("safe_response_templates", {})

    # ── Main assessment ──────────────────────────────────────────

    def assess_input(self, text: str, language: str = "en") -> SafetyAssessment:
        """
        Analyse user input for safety concerns.

        Returns a SafetyAssessment with risk level and recommended action.
        Handles None or empty input gracefully by returning a NONE assessment.
        """
        self._log_activity("Checking safety")
        
        if not text or not isinstance(text, str):
            return SafetyAssessment(
                risk_level=RiskLevel.NONE.value,
                detected_signals=[],
                recommended_response_type="supportive",
                should_escalate=False,
                safe_response_template="",
            )
        
        text_lower = text.lower().strip()

        # Check for crisis signals
        crisis_result = self._detect_crisis(text_lower, language)
        if crisis_result["detected"]:
            level = (
                RiskLevel.CRITICAL.value
                if crisis_result["severity"] == "critical"
                else RiskLevel.HIGH.value
            )
            template = self._get_crisis_template(language)
            return SafetyAssessment(
                risk_level=level,
                detected_signals=crisis_result["signals"],
                recommended_response_type="crisis_support",
                should_escalate=True,
                safe_response_template=template,
            )

        # Check for moderate distress
        distress_result = self._detect_distress(text_lower, language)
        if distress_result["detected"]:
            template = self._get_distress_template(language)
            return SafetyAssessment(
                risk_level=RiskLevel.MODERATE.value,
                detected_signals=distress_result["signals"],
                recommended_response_type="grounding",
                should_escalate=False,
                safe_response_template=template,
            )

        return SafetyAssessment(
            risk_level=RiskLevel.NONE.value,
            detected_signals=[],
            recommended_response_type="supportive",
            should_escalate=False,
            safe_response_template="",
        )

    # ── Response filtering ───────────────────────────────────────

    def filter_response(self, response_text: str) -> str:
        """
        Remove any diagnosis or medical claims from a generated response.
        Returns the filtered text or a safe replacement.
        """
        response_lower = response_text.lower()

        for pattern in self._diagnosis_patterns:
            if pattern.lower() in response_lower:
                # Replace the entire response with a safe alternative
                return (
                    "I'm here to listen and support you. "
                    "Remember, for specific guidance, a professional "
                    "counselor or therapist can help."
                )

        return response_text

    def is_safe_response(self, response_text: str) -> bool:
        """Check if a response passes safety filters."""
        response_lower = response_text.lower()
        for pattern in self._diagnosis_patterns:
            if pattern.lower() in response_lower:
                return False
        return True

    # ── Crisis detection ─────────────────────────────────────────

    def _detect_crisis(self, text: str, language: str) -> Dict:
        """Check text against crisis keyword lists."""
        signals = []

        # Choose language-specific keywords
        lang_key = "bangla" if language in ("bn", "bn_bd") else "english"
        lang_keywords = self._crisis_keywords.get(lang_key, {})

        # Also always check English keywords as a safety net
        en_keywords = self._crisis_keywords.get("english", {})

        all_categories = {}
        for cat, kws in en_keywords.items():
            all_categories.setdefault(cat, []).extend(kws)
        if lang_key != "english":
            for cat, kws in lang_keywords.items():
                all_categories.setdefault(cat, []).extend(kws)

        severity = "high"
        for category, keywords in all_categories.items():
            for kw in keywords:
                if kw.lower() in text:
                    signals.append(f"{category}: {kw}")
                    if category in ("self_harm", "medical_emergency"):
                        severity = "critical"

        return {
            "detected": len(signals) > 0,
            "signals": signals,
            "severity": severity,
        }

    def _detect_distress(self, text: str, language: str) -> Dict:
        """Detect moderate distress signals (not crisis-level)."""
        distress_keywords_en = [
            "stressed", "overwhelmed", "anxious", "worried",
            "can't sleep", "exhausted", "lonely", "helpless",
            "hopeless", "lost", "confused", "scared", "afraid",
            "miserable", "frustrated", "angry", "upset",
            "sad", "crying", "tears", "broken", "struggling",
            "suffering", "pain", "hurting", "distressed",
        ]
        distress_keywords_bn = [
            "চাপে আছি", "উদ্বিগ্ন", "চিন্তিত", "ঘুমাতে পারছি না",
            "ক্লান্ত", "একা", "অসহায়", "হতাশ", "ভয় পাচ্ছি",
            "দুঃখিত", "কাঁদছি", "ভেঙে পড়ছি", "কষ্ট",
        ]

        signals = []
        keywords = distress_keywords_en
        if language in ("bn", "bn_bd"):
            keywords = keywords + distress_keywords_bn

        for kw in keywords:
            if kw.lower() in text:
                signals.append(kw)

        return {
            "detected": len(signals) >= 1,
            "signals": signals[:5],  # limit stored signals
        }

    # ── Template retrieval ───────────────────────────────────────

    def _get_crisis_template(self, language: str) -> str:
        """Get a safe crisis response template."""
        lang_key = "bangla" if language in ("bn", "bn_bd") else "english"
        templates = (
            self._safe_templates
            .get("crisis", {})
            .get(lang_key, [])
        )
        if templates:
            return random.choice(templates)
        # Hardcoded fallback
        return (
            "I hear you, and your safety matters most right now. "
            "Please reach out to a trusted person or local emergency services. "
            "You are not alone."
        )

    def _get_distress_template(self, language: str) -> str:
        """Get a non-crisis distress support template."""
        lang_key = "bangla" if language in ("bn", "bn_bd") else "english"
        templates = (
            self._safe_templates
            .get("non_crisis_distress", {})
            .get(lang_key, [])
        )
        if templates:
            return random.choice(templates)
        return (
            "I can feel that things are heavy right now. "
            "Let's slow down together. Take a deep breath with me."
        )

    def get_professional_help_reminder(self, language: str = "en") -> str:
        """Get a professional help reminder in the correct language."""
        lang_key = "bangla" if language in ("bn", "bn_bd") else "english"
        templates = (
            self._safe_templates
            .get("professional_help_reminder", {})
            .get(lang_key, [])
        )
        if templates:
            return templates[0]
        return (
            "Remember, I'm here as a supportive companion, "
            "not a replacement for professional help."
        )

    def get_disclaimer(self, language: str = "en") -> str:
        """Get the system disclaimer in the correct language."""
        lang_key = "bangla" if language in ("bn", "bn_bd") else "english"
        return (
            self._safe_templates
            .get("disclaimer", {})
            .get(lang_key, "This is an emotional support companion, not professional care.")
        )
