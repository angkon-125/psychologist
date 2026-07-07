"""
Importance Engine — Episodic Memory

Scores how important a conversation is for long-term storage.
Only episodes above the threshold (0.35) are persisted.

Factors:
  - conversation_length: longer = higher (0.0-0.15)
  - emotion_intensity: strong emotions = higher (0.0-0.25)
  - intent_significance: crisis=0.95, emotional_support=0.6, etc. (0.0-0.25)
  - novelty: new topics score higher (0.0-0.15)
  - goal_relevance: if related to active goal (0.0-0.10)
  - user_request: explicit "remember this" = 1.0 override
"""

import re
import logging
from typing import Optional, Set

logger = logging.getLogger("zara.memory.episodic.importance")

# Intent significance base scores
_INTENT_SCORES = {
    "crisis": 0.95,
    "journaling": 0.70,
    "emotional_support": 0.60,
    "reflection": 0.55,
    "breathing": 0.45,
    "grounding": 0.45,
    "mood_checkin": 0.40,
    "tool_request": 0.50,
    "prediction": 0.45,
    "session_summary": 0.50,
    "voice_command": 0.20,
    "greeting": 0.05,
    "farewell": 0.10,
    "general": 0.10,
}

# Emotion intensity mapping
_EMOTION_INTENSITY = {
    "excited": 0.85,
    "ecstatic": 0.95,
    "motivated": 0.70,
    "happy": 0.60,
    "grateful": 0.55,
    "calm": 0.30,
    "neutral": 0.10,
    "bored": 0.15,
    "anxious": 0.70,
    "stressed": 0.75,
    "worried": 0.65,
    "sad": 0.70,
    "depressed": 0.85,
    "lonely": 0.75,
    "angry": 0.80,
    "frustrated": 0.70,
    "overwhelmed": 0.85,
    "scared": 0.80,
    "afraid": 0.80,
    "hopeless": 0.90,
    "relieved": 0.50,
}

# Patterns that indicate user explicitly wants to remember
_REMEMBER_PATTERNS = [
    re.compile(r"\b(remember|save|keep|store)\s+(this|that|it)\b", re.IGNORECASE),
    re.compile(r"\bdon'?t\s+forget\b", re.IGNORECASE),
    re.compile(r"\b(this\s+is\s+important|important\s+to\s+remember)\b", re.IGNORECASE),
    re.compile(r"\bplease\s+remember\b", re.IGNORECASE),
    re.compile(r"\bsave\s+(this|for\s+later|as\s+a\s+memory)\b", re.IGNORECASE),
]

# Importance threshold — only store episodes above this
IMPORTANCE_THRESHOLD = 0.35


class ImportanceEngine:
    """
    Scores conversation importance for episodic storage decisions.

    Usage:
        engine = ImportanceEngine()
        score = engine.score(
            text="I finished the architecture design today!",
            intent="general",
            emotion="excited",
            context_length=15,
            has_goal=True,
            user_requested_remember=False,
        )
        # score ≈ 0.75
    """

    def score(
        self,
        text: str = "",
        intent: str = "general",
        emotion: str = "neutral",
        context_length: int = 0,
        has_goal: bool = False,
        user_requested_remember: bool = False,
        known_topics: Optional[Set[str]] = None,
    ) -> float:
        """
        Calculate importance score for a conversation.

        Args:
            text: User's input text
            intent: Classified intent
            emotion: Detected emotion
            context_length: Number of turns in the conversation
            has_goal: Whether this relates to an active goal
            user_requested_remember: Whether user explicitly asked to remember
            known_topics: Set of already-known topics (for novelty scoring)

        Returns:
            Importance score 0.0-1.0
        """
        # User explicit request overrides everything
        if user_requested_remember or self._user_requested_remember(text):
            return 1.0

        # Factor 1: Conversation length (0.0 - 0.15)
        length_score = self._conversation_length_score(context_length)

        # Factor 2: Emotion intensity (0.0 - 0.25)
        emotion_score = self._emotion_score(emotion)

        # Factor 3: Intent significance (0.0 - 0.25)
        intent_score = self._intent_score(intent)

        # Factor 4: Novelty (0.0 - 0.15)
        novelty_score = self._novelty_score(text, known_topics)

        # Factor 5: Goal relevance (0.0 - 0.10)
        goal_score = 0.10 if has_goal else 0.0

        # Factor 6: Text content signals
        content_score = self._content_signals(text)

        # Combine: weighted sum
        total = (
            length_score
            + emotion_score
            + intent_score
            + novelty_score
            + goal_score
            + content_score
        )

        # Clamp to 0-1
        total = max(0.0, min(1.0, total))

        logger.debug(
            "Importance: %.3f (len=%.2f, emo=%.2f, int=%.2f, nov=%.2f, goal=%.2f, content=%.2f)",
            total, length_score, emotion_score, intent_score,
            novelty_score, goal_score, content_score,
        )
        return round(total, 4)

    def should_store(self, score: float) -> bool:
        """Whether an episode with this score should be persisted."""
        return score >= IMPORTANCE_THRESHOLD

    def _user_requested_remember(self, text: str) -> bool:
        """Check if user explicitly asked to remember."""
        if not text:
            return False
        return any(p.search(text) for p in _REMEMBER_PATTERNS)

    def _conversation_length_score(self, context_length: int) -> float:
        """Longer conversations are more important (0.0-0.15)."""
        if context_length >= 20:
            return 0.15
        elif context_length >= 10:
            return 0.10
        elif context_length >= 5:
            return 0.06
        elif context_length >= 2:
            return 0.03
        return 0.0

    def _emotion_score(self, emotion: str) -> float:
        """Strong emotions are more important (0.0-0.25)."""
        intensity = _EMOTION_INTENSITY.get(emotion.lower().strip(), 0.10)
        return intensity * 0.25  # Scale to max 0.25

    def _intent_score(self, intent: str) -> float:
        """Some intents are inherently more significant (0.0-0.25)."""
        base = _INTENT_SCORES.get(intent, 0.10)
        return base * 0.25  # Scale: crisis=0.24, general=0.025

    def _novelty_score(self, text: str, known_topics: Optional[set] = None) -> float:
        """New topics are more important (0.0-0.15)."""
        if not text or not known_topics:
            return 0.10  # Assume novel if we can't check

        # Extract key words from text
        words = set(re.findall(r'\b\w{4,}\b', text.lower()))
        stop_words = {"this", "that", "with", "have", "from", "they", "been",
                      "would", "could", "should", "their", "there", "about"}
        words -= stop_words

        if not words:
            return 0.05

        # How many words are new (not in known topics)?
        known_lower = {t.lower() for t in known_topics}
        new_words = words - known_lower
        novelty_ratio = len(new_words) / max(len(words), 1)
        return novelty_ratio * 0.15

    def _content_signals(self, text: str) -> float:
        """Additional content-based importance signals (0.0-0.10)."""
        if not text:
            return 0.0
        text_lower = text.lower()
        score = 0.0

        # Achievement/completion signals
        achievement_patterns = [
            r"\b(finished|completed|done|built|created|implemented|deployed|released)\b",
            r"\b(milestone|breakthrough|success|accomplished|achieved)\b",
            r"\b(started|began|launched|initiated)\b.*\b(project|goal|plan)\b",
        ]
        if any(re.search(p, text_lower) for p in achievement_patterns):
            score += 0.05

        # Decision signals
        decision_patterns = [
            r"\b(decided|decision|chose|choose|going\s+to)\b",
            r"\b(will\s+use|will\s+build|plan\s+to)\b",
        ]
        if any(re.search(p, text_lower) for p in decision_patterns):
            score += 0.03

        # Personal significance
        personal_patterns = [
            r"\b(my\s+(birthday|anniversary|wedding|graduation))\b",
            r"\b(i\s+(quit|resigned|got\s+the\s+job|was\s+promoted))\b",
        ]
        if any(re.search(p, text_lower) for p in personal_patterns):
            score += 0.05

        return min(0.10, score)
