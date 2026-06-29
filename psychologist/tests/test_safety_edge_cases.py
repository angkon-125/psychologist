"""
Edge-case tests for the safety support layer.

Covers crisis detection (self-harm, abuse, panic, medical emergency),
Bangla keywords, diagnosis block patterns, distress detection,
response filtering, and graceful handling of empty/None input.
"""

import pytest

from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
from emotion_engine.interaction.interaction_models import RiskLevel


@pytest.fixture
def safety():
    return SafetySupportLayer()


class TestCrisisDetection:
    def test_self_harm_detected(self, safety):
        result = safety.assess_input("I want to kill myself")
        assert result.should_escalate is True
        assert result.risk_level in (
            RiskLevel.CRITICAL.value,
            RiskLevel.HIGH.value,
        )
        assert result.recommended_response_type == "crisis_support"
        assert len(result.safe_response_template) > 0

    def test_self_harm_variations(self, safety):
        phrases = [
            "I want to hurt myself",
            "I want to end my life",
            "I want to die",
            "I'm suicidal",
            "I don't want to live anymore",
            "I'm better off dead",
        ]
        for phrase in phrases:
            result = safety.assess_input(phrase)
            assert result.should_escalate is True, f"Failed for: {phrase}"

    def test_harm_to_others(self, safety):
        result = safety.assess_input("I want to kill someone")
        assert result.should_escalate is True
        assert result.risk_level in (
            RiskLevel.HIGH.value,
            RiskLevel.CRITICAL.value,
        )

    def test_abuse_detected(self, safety):
        result = safety.assess_input("I'm being abused by my partner")
        assert result.should_escalate is True

    def test_panic_detected(self, safety):
        result = safety.assess_input("I can't breathe, I'm having a panic attack")
        assert result.should_escalate is True

    def test_medical_emergency(self, safety):
        result = safety.assess_input("I took too many pills")
        assert result.should_escalate is True
        assert result.risk_level == RiskLevel.CRITICAL.value

    def test_crisis_has_safe_template(self, safety):
        result = safety.assess_input("I want to end it all")
        assert len(result.safe_response_template) > 20
        assert "not alone" in result.safe_response_template.lower() or \
               "emergency" in result.safe_response_template.lower() or \
               "support" in result.safe_response_template.lower()

    def test_crisis_template_english(self, safety):
        result = safety.assess_input("I want to kill myself", language="en")
        assert len(result.safe_response_template) > 0

    def test_crisis_template_bangla(self, safety):
        result = safety.assess_input("আত্মহত্যা", language="bn")
        assert result.should_escalate is True
        assert len(result.safe_response_template) > 0


class TestDistressDetection:
    def test_moderate_distress(self, safety):
        result = safety.assess_input("I feel so stressed and overwhelmed")
        assert result.risk_level == RiskLevel.MODERATE.value
        assert result.should_escalate is False
        assert len(result.safe_response_template) > 0

    def test_anxiety_distress(self, safety):
        result = safety.assess_input("I'm very anxious and worried about everything")
        assert result.risk_level in (
            RiskLevel.MODERATE.value,
            RiskLevel.HIGH.value,
        )

    def test_loneliness_distress(self, safety):
        result = safety.assess_input("I feel so lonely and alone")
        assert result.risk_level in (
            RiskLevel.MODERATE.value,
            RiskLevel.NONE.value,
            RiskLevel.HIGH.value,
        )

    def test_no_distress_for_neutral(self, safety):
        result = safety.assess_input("I had a nice lunch today")
        assert result.risk_level == RiskLevel.NONE.value
        assert result.should_escalate is False


class TestDiagnosisBlock:
    def test_diagnosis_blocked(self, safety):
        text = "You have depression and need medication."
        filtered = safety.filter_response(text)
        assert "I'm here to listen" in filtered or "counselor" in filtered

    def test_medical_claim_blocked(self, safety):
        text = "I diagnose you with anxiety disorder."
        filtered = safety.filter_response(text)
        assert "diagnose" not in filtered.lower()

    def test_safe_response_passes(self, safety):
        text = "I'm here to support you through this."
        filtered = safety.filter_response(text)
        assert filtered == text

    def test_is_safe_response_true(self, safety):
        assert safety.is_safe_response("I understand. Tell me more.") is True

    def test_is_safe_response_false(self, safety):
        assert safety.is_safe_response("You have PTSD.") is False


class TestEmptyInput:
    def test_none_input(self, safety):
        result = safety.assess_input(None)
        assert result.risk_level == RiskLevel.NONE.value
        assert result.should_escalate is False

    def test_empty_string(self, safety):
        result = safety.assess_input("")
        assert result.risk_level == RiskLevel.NONE.value

    def test_whitespace_only(self, safety):
        result = safety.assess_input("   ")
        assert result.risk_level == RiskLevel.NONE.value

    def test_non_string_input(self, safety):
        result = safety.assess_input(12345)
        assert result.risk_level == RiskLevel.NONE.value


class TestProfessionalHelpReminder:
    def test_english(self, safety):
        text = safety.get_professional_help_reminder("en")
        assert "professional" in text.lower() or "counselor" in text.lower()

    def test_bangla(self, safety):
        text = safety.get_professional_help_reminder("bn")
        assert len(text) > 10


class TestDisclaimer:
    def test_english_disclaimer(self, safety):
        text = safety.get_disclaimer("en")
        assert "emotional support" in text.lower() or "companion" in text.lower()

    def test_bangla_disclaimer(self, safety):
        text = safety.get_disclaimer("bn")
        assert len(text) > 10
