"""
Conversation Memory

Manages a sliding-window buffer of recent conversation turns
for fast in-memory context retrieval without hitting SQLite.

This provides the Orchestrator with immediate access to the
current session's conversation history for multi-turn coherence.
"""

import logging
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger("zara.memory.conversation")


class ConversationMemory:
    """
    In-memory sliding window of recent conversation turns.

    Provides O(1) access to the most recent context without
    requiring a database query. The SQLite store remains the
    authoritative long-term store; this is the fast short-term layer.
    """

    # Default maximum turns kept in the window
    DEFAULT_WINDOW_SIZE = 20

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        self._window_size = window_size
        self._turns: deque = deque(maxlen=window_size)
        self._session_id: str = ""

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    def start_session(self, session_id: str):
        """
        Begin a new conversation session, clearing the window.

        Args:
            session_id: Unique session identifier.
        """
        if self._session_id and self._session_id != session_id:
            logger.info(
                "Switching session: %s -> %s (discarding %d turns)",
                self._session_id, session_id, len(self._turns),
            )
        self._turns.clear()
        self._session_id = session_id
        logger.info("Conversation session started: %s", session_id)

    def add_turn(
        self,
        role: str,
        text: str,
        intent: str = "",
        emotion: str = "",
        confidence: float = 0.0,
        risk_level: str = "low",
    ):
        """
        Add a conversation turn to the sliding window.

        Args:
            role: "user" or "assistant"
            text: The message content
            intent: Classified intent name
            emotion: Detected emotion
            confidence: Intent/emotion confidence
            risk_level: Safety risk level
        """
        turn = {
            "role": role,
            "text": text,
            "intent": intent,
            "emotion": emotion,
            "confidence": confidence,
            "risk_level": risk_level,
        }
        self._turns.append(turn)
        logger.debug("Turn added: %s (%d chars)", role, len(text))

    def get_recent_context(self, limit: int = 5) -> str:
        """
        Get the most recent conversation turns as a formatted string.

        Args:
            limit: Maximum number of turns to include.

        Returns:
            Formatted multi-line context string.
        """
        if not self._turns:
            return ""

        recent = list(self._turns)[-limit:]
        lines = []
        for turn in recent:
            speaker = "User" if turn["role"] == "user" else "ZARA"
            lines.append(f"{speaker}: {turn['text']}")

        return "\n".join(lines)

    def get_recent_turns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent turns as structured dicts.

        Args:
            limit: Maximum number of turns.

        Returns:
            List of turn dicts, oldest first.
        """
        if not self._turns:
            return []
        return list(self._turns)[-limit:]

    def get_last_user_emotion(self) -> str:
        """Get the emotion from the most recent user turn."""
        for turn in reversed(self._turns):
            if turn["role"] == "user" and turn.get("emotion"):
                return turn["emotion"]
        return "neutral"

    def get_intent_history(self, limit: int = 10) -> List[str]:
        """Get the sequence of recent intents from user turns."""
        intents = []
        for turn in reversed(self._turns):
            if turn["role"] == "user" and turn.get("intent"):
                intents.append(turn["intent"])
                if len(intents) >= limit:
                    break
        return list(reversed(intents))

    def clear(self):
        """Clear all turns from the window."""
        self._turns.clear()
        logger.debug("Conversation memory cleared")
