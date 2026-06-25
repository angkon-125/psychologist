"""
Interaction Package — Dual-Mode (Text/Voice/Hybrid) Interaction Layer

Provides the interaction layer for the offline emotional support system.
All processing is local — no cloud APIs, no LLMs, no external services.
"""

from .interaction_models import (
    InteractionMode,
    InteractionModeConfig,
    UserMessage,
    AssistantMessage,
    SessionState,
    SupportAction,
    SafetyAssessment,
    RiskLevel,
    SupportActionType,
    InputType,
    ResponseType,
)

__all__ = [
    "InteractionMode",
    "InteractionModeConfig",
    "UserMessage",
    "AssistantMessage",
    "SessionState",
    "SupportAction",
    "SafetyAssessment",
    "RiskLevel",
    "SupportActionType",
    "InputType",
    "ResponseType",
]
