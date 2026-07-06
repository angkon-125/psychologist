"""
ZARA Speaking Style Presets

Defines speaking style presets that control text-level behavior:
  - speed_factor: multiplier applied on top of voice profile speed
  - pause_after_sentence: whether to add pause markers between sentences
  - max_sentence_chars: max characters per spoken chunk
  - chunk_mode: "sentence" or "short" (affects chunking strategy)

These are separate from voice profiles (which control TTS engine params).
Speaking styles control how text is prepared before it reaches the engine.

No voice cloning. No celebrity imitation. No cloud voice.
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("zara.voice.styles")

# ── Speaking Style Definitions ─────────────────────────────────────────────

SPEAKING_STYLES: Dict[str, Dict[str, Any]] = {
    "calm_support": {
        "label": "Calm Support",
        "speed_factor": 0.95,
        "pause_after_sentence": True,
        "max_sentence_chars": 120,
        "chunk_mode": "sentence",
        "description": "Warm, patient speaking style for emotional support",
    },
    "friendly_assistant": {
        "label": "Friendly Assistant",
        "speed_factor": 1.0,
        "pause_after_sentence": False,
        "max_sentence_chars": 150,
        "chunk_mode": "sentence",
        "description": "Bright, natural speaking style for everyday assistance",
    },
    "professional_clear": {
        "label": "Professional Clear",
        "speed_factor": 0.98,
        "pause_after_sentence": True,
        "max_sentence_chars": 100,
        "chunk_mode": "sentence",
        "description": "Clear, precise speaking style for focused tasks",
    },
    "night_soft": {
        "label": "Night Soft",
        "speed_factor": 0.88,
        "pause_after_sentence": True,
        "max_sentence_chars": 80,
        "chunk_mode": "short",
        "description": "Gentle, quiet speaking style for late-night use",
    },
    "emergency_clear": {
        "label": "Emergency Clear",
        "speed_factor": 1.05,
        "pause_after_sentence": False,
        "max_sentence_chars": 80,
        "chunk_mode": "short",
        "description": "Direct, clear speaking style for crisis situations",
    },
}

DEFAULT_SPEAKING_STYLE = "calm_support"

# ── Emotion-to-Style Mapping ───────────────────────────────────────────────

EMOTION_TO_STYLE: Dict[str, str] = {
    # Emotional support keywords
    "support": "calm_support",
    "warm": "calm_support",
    "calm": "calm_support",
    "comfort": "calm_support",
    "empathy": "calm_support",
    # Friendly/assistant keywords
    "friendly": "friendly_assistant",
    "happy": "friendly_assistant",
    "cheerful": "friendly_assistant",
    "assistant": "friendly_assistant",
    # Focused/professional keywords
    "focused": "professional_clear",
    "clear": "professional_clear",
    "professional": "professional_clear",
    "coding": "professional_clear",
    "project": "professional_clear",
    # Night/gentle keywords
    "gentle": "night_soft",
    "night": "night_soft",
    "quiet": "night_soft",
    "sleepy": "night_soft",
    # Crisis/emergency keywords
    "crisis": "emergency_clear",
    "fear": "emergency_clear",
    "distress": "emergency_clear",
    "panic": "emergency_clear",
    "emergency": "emergency_clear",
    "safety": "emergency_clear",
}


def get_style(style_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve a speaking style by key.

    Returns the style dict if found, otherwise falls back to default.
    Always returns a copy to prevent mutation.
    """
    if style_key and style_key in SPEAKING_STYLES:
        return dict(SPEAKING_STYLES[style_key])

    if style_key and style_key not in SPEAKING_STYLES:
        logger.warning(
            "Unknown speaking style '%s', falling back to '%s'",
            style_key,
            DEFAULT_SPEAKING_STYLE,
        )

    return dict(SPEAKING_STYLES[DEFAULT_SPEAKING_STYLE])


def get_default_style() -> str:
    """Return the default speaking style key."""
    return DEFAULT_SPEAKING_STYLE


def get_style_for_emotion(emotion: str) -> str:
    """
    Return the recommended speaking style key for a given emotion or mode.

    Falls back to default if emotion is not recognized.
    """
    if not emotion:
        return DEFAULT_SPEAKING_STYLE

    emotion_lower = emotion.lower().strip()
    return EMOTION_TO_STYLE.get(emotion_lower, DEFAULT_SPEAKING_STYLE)


def get_all_styles() -> Dict[str, Dict[str, Any]]:
    """Return all available speaking styles (read-only copy)."""
    return {k: dict(v) for k, v in SPEAKING_STYLES.items()}


def get_style_keys() -> list:
    """Return list of available style keys."""
    return list(SPEAKING_STYLES.keys())
