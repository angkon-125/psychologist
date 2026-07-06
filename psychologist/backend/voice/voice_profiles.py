"""
ZARA Voice Profile System

Defines curated voice profiles for different interaction contexts.
Each profile specifies speed, pitch, volume, and emotion attributes
that are applied to the active TTS engine (Piper / eSpeak / pyttsx3).

No voice cloning. No celebrity imitation. No cloud voice.
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("zara.voice.profiles")

# ── Voice Profile Definitions ─────────────────────────────────────────────

ZARA_VOICE_PROFILES: Dict[str, Dict[str, Any]] = {
    "zara_soft": {
        "label": "Zara Soft",
        "gender": "female",
        "speed": 0.92,
        "pitch": 1.05,
        "volume": 0.9,
        "emotion": "warm",
        "description": "Warm, calm female voice for support conversations",
    },
    "zara_cute": {
        "label": "Zara Cute",
        "gender": "female",
        "speed": 1.03,
        "pitch": 1.12,
        "volume": 0.95,
        "emotion": "friendly",
        "description": "Bright, cute, friendly assistant voice",
    },
    "zara_professional": {
        "label": "Zara Professional",
        "gender": "female",
        "speed": 0.96,
        "pitch": 1.0,
        "volume": 0.95,
        "emotion": "clear",
        "description": "Clear professional female voice",
    },
    "zara_night": {
        "label": "Zara Night",
        "gender": "female",
        "speed": 0.85,
        "pitch": 0.96,
        "volume": 0.65,
        "emotion": "gentle",
        "description": "Soft quiet voice for night use",
    },
}

# Default profile key
DEFAULT_VOICE_PROFILE = "zara_soft"

# Mode-to-profile auto-mapping (optional, used by frontend)
MODE_PROFILE_MAP: Dict[str, str] = {
    "psychologist": "zara_soft",
    "support": "zara_soft",
    "assistant": "zara_cute",
    "chat": "zara_cute",
    "coding": "zara_professional",
    "project": "zara_professional",
    "night": "zara_night",
    "low_volume": "zara_night",
}


def get_profile(profile_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve a voice profile by key.

    Returns the profile dict if found, otherwise falls back to default.
    Always returns a copy to prevent mutation.
    """
    if profile_key and profile_key in ZARA_VOICE_PROFILES:
        return dict(ZARA_VOICE_PROFILES[profile_key])

    if profile_key and profile_key not in ZARA_VOICE_PROFILES:
        logger.warning(
            "Unknown voice profile '%s', falling back to '%s'",
            profile_key,
            DEFAULT_VOICE_PROFILE,
        )

    return dict(ZARA_VOICE_PROFILES[DEFAULT_VOICE_PROFILE])


def get_profile_for_mode(mode: str) -> str:
    """Return the recommended profile key for a given interaction mode."""
    return MODE_PROFILE_MAP.get(mode, DEFAULT_VOICE_PROFILE)


def get_all_profiles() -> Dict[str, Dict[str, Any]]:
    """Return all available voice profiles (read-only copy)."""
    return {k: dict(v) for k, v in ZARA_VOICE_PROFILES.items()}


def get_profile_keys() -> list:
    """Return list of available profile keys."""
    return list(ZARA_VOICE_PROFILES.keys())


# ── Emotion-Aware Voice + Style Mapping ─────────────────────────────────────

EMOTION_STYLE_MAP: Dict[str, Tuple[str, str]] = {
    "support": ("zara_soft", "calm_support"),
    "psychologist": ("zara_soft", "calm_support"),
    "assistant": ("zara_cute", "friendly_assistant"),
    "chat": ("zara_cute", "friendly_assistant"),
    "coding": ("zara_professional", "professional_clear"),
    "project": ("zara_professional", "professional_clear"),
    "night": ("zara_night", "night_soft"),
    "low_volume": ("zara_night", "night_soft"),
    "crisis": ("zara_professional", "emergency_clear"),
    "safety": ("zara_professional", "emergency_clear"),
}


def resolve_emotion_voice(mode_or_emotion: str) -> Tuple[str, str]:
    """
    Resolve a mode/emotion to a (profile_key, style_key) tuple.

    Returns (DEFAULT_VOICE_PROFILE, default_style) if not recognized.
    """
    if not mode_or_emotion:
        return (DEFAULT_VOICE_PROFILE, "calm_support")

    key = mode_or_emotion.lower().strip()
    if key in EMOTION_STYLE_MAP:
        return EMOTION_STYLE_MAP[key]

    # Try to match via MODE_PROFILE_MAP for profile, default style
    from backend.voice.speaking_styles import get_style_for_emotion, DEFAULT_SPEAKING_STYLE
    profile_key = get_profile_for_mode(key)
    style_key = get_style_for_emotion(key)
    return (profile_key, style_key)


def resolve_profile_with_overrides(
    profile_key: Optional[str] = None,
    user_speed: Optional[float] = None,
    user_volume: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Resolve a voice profile, then apply user-level overrides on top.

    This allows the profile to set the baseline, while the user's
    speed slider and volume slider take precedence.
    """
    profile = get_profile(profile_key)

    # Apply user overrides where provided
    if user_speed is not None:
        profile["speed"] = max(0.5, min(2.0, float(user_speed)))
    if user_volume is not None:
        profile["volume"] = max(0.0, min(1.0, float(user_volume)))

    return profile
