"""
Safety Policies

Defines what actions require confirmation, what risk levels block execution,
and what categories of content are flagged.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set


# Risk levels in ascending order of severity
RISK_NONE = "none"
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

RISK_ORDER = {
    RISK_NONE: 0,
    RISK_LOW: 1,
    RISK_MEDIUM: 2,
    RISK_HIGH: 3,
    RISK_CRITICAL: 4,
}


def compare_risk(a: str, b: str) -> int:
    """Compare two risk levels. Returns <0 if a < b, 0 if equal, >0 if a > b."""
    return RISK_ORDER.get(a, 0) - RISK_ORDER.get(b, 0)


def max_risk(a: str, b: str) -> str:
    """Return the higher of two risk levels."""
    return a if compare_risk(a, b) >= 0 else b


@dataclass
class SafetyPolicy:
    """
    Central safety policy configuration.

    Defines rules that the Safety Agent enforces:
    - Which tool risk levels require user confirmation
    - Which actions are always blocked
    - Diagnosis/therapy boundary patterns
    """

    # Tool execution: minimum risk level that requires user confirmation
    tool_confirmation_threshold: str = RISK_MEDIUM

    # Tool execution: risk level that blocks execution entirely
    tool_block_threshold: str = RISK_HIGH

    # Actions that are always blocked regardless of risk level
    blocked_actions: Set[str] = field(default_factory=lambda: {
        "delete_system_file",
        "format_disk",
        "modify_registry",
        "install_software",
        "send_email",
        "network_request",
    })

    # Patterns that indicate diagnosis / medical claims (must be filtered)
    diagnosis_block_patterns: List[str] = field(default_factory=lambda: [
        "you have",
        "you are diagnosed",
        "you suffer from",
        "your condition is",
        "i diagnose",
        "clinical diagnosis",
        "you need medication",
        "take this medicine",
        "you should take pills",
        "prescription",
    ])

    # Therapy boundary — phrases ZARA must never use
    therapy_boundary_phrases: List[str] = field(default_factory=lambda: [
        "as your therapist",
        "in my professional opinion",
        "i am a licensed",
        "clinical assessment",
        "psychological evaluation",
        "i am a psychologist",
        "i am a psychiatrist",
        "i am a counselor",
    ])

    # Privacy: fields that should never be logged
    sensitive_fields: Set[str] = field(default_factory=lambda: {
        "password",
        "secret",
        "token",
        "api_key",
        "credit_card",
        "ssn",
        "social_security",
    })

    def requires_confirmation(self, risk_level: str) -> bool:
        """Check if this risk level requires user confirmation."""
        return compare_risk(risk_level, self.tool_confirmation_threshold) >= 0

    def is_blocked(self, risk_level: str) -> bool:
        """Check if this risk level blocks execution entirely."""
        return compare_risk(risk_level, self.tool_block_threshold) >= 0

    def is_action_blocked(self, action_name: str) -> bool:
        """Check if a specific action is in the blocked list."""
        return action_name.lower() in self.blocked_actions


# Singleton policy instance
default_policy = SafetyPolicy()
