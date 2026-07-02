"""
Conversation State — Orchestrator-level state tracking.

Tracks the current session, turn history, and agent dispatch log
for the Orchestrator to make informed routing decisions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("zara.agent.state")


@dataclass
class TurnRecord:
    """Record of a single turn (request + response) in the conversation."""

    turn_id: int = 0
    request_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    user_text: str = ""
    intent: str = ""
    intent_confidence: float = 0.0
    dispatched_agent: str = ""
    response_text: str = ""
    response_confidence: float = 0.0
    risk_level: str = "low"
    latency_ms: float = 0.0
    fallback_used: bool = False
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "user_text": self.user_text,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "dispatched_agent": self.dispatched_agent,
            "response_text": self.response_text,
            "response_confidence": self.response_confidence,
            "risk_level": self.risk_level,
            "latency_ms": self.latency_ms,
            "fallback_used": self.fallback_used,
            "errors": self.errors,
        }


class ConversationStateManager:
    """
    Manages orchestrator-level conversation state.

    Tracks:
      - Current session ID
      - Turn history (limited to last N turns)
      - Accumulated risk level
      - Agent dispatch log
    """

    MAX_TURN_HISTORY = 100

    def __init__(self):
        self._session_id: str = str(uuid.uuid4())
        self._turns: List[TurnRecord] = []
        self._turn_counter: int = 0
        self._session_start: datetime = datetime.now()
        self._current_risk_level: str = "low"
        self._active: bool = True

    # ── Session management ────────────────────────────────────────

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def turn_count(self) -> int:
        return self._turn_counter

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def current_risk_level(self) -> str:
        return self._current_risk_level

    def new_session(self) -> str:
        """Start a fresh session, clearing turn history."""
        self._session_id = str(uuid.uuid4())
        self._turns.clear()
        self._turn_counter = 0
        self._session_start = datetime.now()
        self._current_risk_level = "low"
        self._active = True
        logger.info("New session: %s", self._session_id)
        return self._session_id

    def end_session(self) -> Dict[str, Any]:
        """End the current session and return summary."""
        self._active = False
        summary = {
            "session_id": self._session_id,
            "start_time": self._session_start.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_turns": self._turn_counter,
            "final_risk_level": self._current_risk_level,
        }
        logger.info("Session ended: %s (%d turns)", self._session_id, self._turn_counter)
        return summary

    # ── Turn management ───────────────────────────────────────────

    def record_turn(
        self,
        request_id: str,
        user_text: str,
        intent: str,
        intent_confidence: float,
        dispatched_agent: str,
        response_text: str,
        response_confidence: float,
        risk_level: str,
        latency_ms: float,
        fallback_used: bool = False,
        errors: Optional[List[str]] = None,
    ) -> TurnRecord:
        """Record a completed turn."""
        self._turn_counter += 1
        turn = TurnRecord(
            turn_id=self._turn_counter,
            request_id=request_id,
            user_text=user_text,
            intent=intent,
            intent_confidence=intent_confidence,
            dispatched_agent=dispatched_agent,
            response_text=response_text,
            response_confidence=response_confidence,
            risk_level=risk_level,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            errors=errors or [],
        )
        self._turns.append(turn)

        # Trim history
        if len(self._turns) > self.MAX_TURN_HISTORY:
            self._turns = self._turns[-self.MAX_TURN_HISTORY:]

        # Update risk level (escalate only, never downgrade automatically)
        risk_priority = {"low": 0, "medium": 1, "high": 2}
        if risk_priority.get(risk_level, 0) > risk_priority.get(self._current_risk_level, 0):
            self._current_risk_level = risk_level
            logger.warning("Risk level escalated to: %s", risk_level)

        return turn

    def get_recent_turns(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the last N turns as dicts."""
        return [t.to_dict() for t in self._turns[-n:]]

    def get_recent_context(self, n: int = 5) -> str:
        """Get recent conversation as a plain text context string."""
        recent = self._turns[-n:]
        lines = []
        for t in recent:
            lines.append(f"User: {t.user_text}")
            lines.append(f"ZARA: {t.response_text}")
        return "\n".join(lines)

    def get_state_summary(self) -> Dict[str, Any]:
        """Get current state summary for the Orchestrator."""
        return {
            "session_id": self._session_id,
            "turn_count": self._turn_counter,
            "active": self._active,
            "current_risk_level": self._current_risk_level,
            "session_duration_seconds": (
                datetime.now() - self._session_start
            ).total_seconds(),
        }
