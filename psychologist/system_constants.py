"""
Centralized system constants for ZARA.

All magic numbers that were previously hardcoded throughout the codebase
are defined here for easy configuration and maintenance.

Import usage:
    from system_constants import EMOTION_DECAY_FACTOR, EMOTION_HISTORY_LIMIT
"""


# ── Emotion Engine ─────────────────────────────────────────────────

EMOTION_DECAY_FACTOR = 0.85
"""Factor by which emotion values decay each interaction cycle."""

EMOTION_HISTORY_LIMIT = 100
"""Maximum number of emotional states kept in history."""

REASONING_BLEND_CURRENT = 0.7
"""Weight for the current emotion value in reasoning blend."""

REASONING_BLEND_BAYESIAN = 0.3
"""Weight for the Bayesian-updated value in reasoning blend."""

SENTIMENT_BOOST_PER_KEYWORD = 0.2
"""Emotion boost per detected keyword."""

SENTIMENT_BOOST_MAX = 0.8
"""Maximum boost from keyword detection."""

SENTIMENT_INFLUENCE_FACTOR = 0.3
"""How much sentiment score directly influences happiness/sadness."""

EMOTION_HISTORY_IMPORTANCE_WEIGHT = 0.5
"""Base importance weight for memory entries (plus intensity * 0.5)."""


# ── Context Engine ─────────────────────────────────────────────────

CONVERSATION_HISTORY_LIMIT = 20
"""Maximum messages kept in conversation history."""

EMOTIONAL_TREND_LIMIT = 10
"""Maximum data points in emotional/intensity trends."""


# ── SCEA System ────────────────────────────────────────────────────

SCEA_DECISION_HISTORY_LIMIT = 100
"""Maximum number of decision records retained."""

SCEA_MEMORY_LIMIT = 500
"""Maximum number of memories retained."""

SCEA_IDENTITY_UPDATE_INTERVAL = 10
"""Number of steps between identity re-evaluations."""

SCEA_MEMORY_IMPORTANCE_WEIGHT = 0.3
"""Weight of emotion intensity in memory importance calculation."""


# ── Interaction ─────────────────────────────────────────────────────

MAX_TEXT_RESPONSE_LENGTH = 500
"""Maximum character length for text-mode responses."""

MAX_VOICE_RESPONSE_LENGTH = 200
"""Maximum character length for voice-mode responses."""

MAX_INPUT_LENGTH = 5000
"""Maximum character length for user input text."""

SESSION_HISTORY_LIMIT = 50
"""Maximum number of stored session files."""

SESSION_MAX_MINUTES = 60
"""Maximum session duration in minutes."""

SESSION_ACTIVITY_LOG_LIMIT = 20
"""Number of recent activity log entries returned by the API."""


# ── API ────────────────────────────────────────────────────────────

DEFAULT_HOST = "127.0.0.1"
"""Default Flask bind address."""

DEFAULT_PORT = 5000
"""Default Flask port."""

RATE_LIMIT_REQUESTS = 60
"""Default rate limit: requests per window."""

RATE_LIMIT_WINDOW_SECONDS = 60
"""Default rate limit: window length in seconds."""

RATE_LIMIT_STRICT_REQUESTS = 30
"""Stricter rate limit for write-heavy endpoints."""

RATE_LIMIT_STRICT_WINDOW_SECONDS = 60
"""Window for strict rate limit."""
