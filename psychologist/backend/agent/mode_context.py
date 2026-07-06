"""
Mode Context — Agent Mode Definitions and Resolution

Defines the valid agent modes for ZARA and provides mappings between
frontend mode selection, backend intent routing, and voice/emotion context.

Modes:
- assistant: General chat assistant (default)
- psychologist: Emotional support, therapy-style conversations
- coding: Programming help, project tasks
- project: Project management, file operations
- prediction: Future predictions, risk assessment
- safety: Crisis intervention, safety-first responses
- night: Late-night calm support mode
"""

from typing import Dict, Optional, Tuple

# ── Valid Agent Modes ──────────────────────────────────────────────

VALID_MODES = {"assistant", "psychologist", "coding", "project", "prediction", "safety", "night"}
DEFAULT_MODE = "assistant"

# ── Mode Labels (for UI display) ──────────────────────────────────

MODE_LABELS: Dict[str, str] = {
    "assistant": "Assistant",
    "psychologist": "Support",
    "coding": "Coding",
    "project": "Project",
    "prediction": "Prediction",
    "safety": "Safety",
    "night": "Night",
}

# ── Intent → Mode Mapping ─────────────────────────────────────────
# When the router detects a specific intent, it may override the frontend mode.

INTENT_TO_MODE: Dict[str, str] = {
    "crisis": "safety",
    "emotional_support": "psychologist",
    "journaling": "psychologist",
    "breathing": "psychologist",
    "reflection": "psychologist",
    "mood_checkin": "psychologist",
    "grounding": "psychologist",
    "tool_request": "project",
    "voice_command": "assistant",
    "greeting": "assistant",
    "farewell": "assistant",
    "prediction": "prediction",
    "session_summary": "psychologist",
    "general": "assistant",
}

# ── Mode → Voice Profile + Speaking Style ─────────────────────────

MODE_TO_VOICE_CONTEXT: Dict[str, Tuple[str, str]] = {
    "assistant": ("zara_cute", "friendly_assistant"),
    "psychologist": ("zara_soft", "calm_support"),
    "coding": ("zara_professional", "professional_clear"),
    "project": ("zara_professional", "professional_clear"),
    "prediction": ("zara_professional", "professional_clear"),
    "safety": ("zara_professional", "emergency_clear"),
    "night": ("zara_night", "night_soft"),
}


def get_mode_label(mode: str) -> str:
    """Get display label for a mode."""
    return MODE_LABELS.get(mode, mode.title() if mode else "Assistant")


def is_valid_mode(mode: str) -> bool:
    """Check if a mode string is valid."""
    return mode in VALID_MODES


def resolve_mode_from_intent(intent: str) -> str:
    """Resolve agent mode from router intent."""
    return INTENT_TO_MODE.get(intent, DEFAULT_MODE)


def get_voice_context_for_mode(mode: str) -> Tuple[str, str]:
    """Get (voice_profile, speaking_style) for a given mode."""
    return MODE_TO_VOICE_CONTEXT.get(mode, MODE_TO_VOICE_CONTEXT[DEFAULT_MODE])


def resolve_final_mode(
    frontend_mode: Optional[str],
    intent: str,
    safety_override: bool = False
) -> str:
    """
    Resolve the final agent mode considering:
    - Frontend requested mode
    - Intent-based correction (safety/crisis always wins)
    - Intent-based overrides for specific intents

    Args:
        frontend_mode: Mode requested by frontend (may be None)
        intent: Intent classified by router
        safety_override: If True, force safety mode (crisis detected)

    Returns:
        Resolved mode string
    """
    # Safety/crisis always overrides
    if safety_override or intent == "crisis":
        return "safety"

    # Normalize frontend mode
    base_mode = frontend_mode if is_valid_mode(frontend_mode or "") else DEFAULT_MODE

    # Intent-based correction: if intent strongly suggests a different mode
    intent_mode = resolve_mode_from_intent(intent)

    # Priority: safety > intent-based > frontend mode
    # But only override if intent is specific (not general/greeting/farewell)
    if intent in ("emotional_support", "journaling", "breathing", "reflection",
                  "mood_checkin", "grounding", "session_summary"):
        return "psychologist"
    if intent == "tool_request":
        return "project"
    if intent == "prediction":
        return "prediction"

    return base_mode


def get_emotion_context_for_mode(mode: str) -> str:
    """
    Get the emotion_context string for TTS based on resolved mode.
    This maps to the EMOTION_TO_STYLE mapping in speaking_styles.py.
    """
    mode_to_emotion = {
        "assistant": "chat",
        "psychologist": "support",
        "coding": "coding",
        "project": "coding",
        "prediction": "coding",
        "safety": "crisis",
        "night": "night",
    }
    return mode_to_emotion.get(mode, "chat")
