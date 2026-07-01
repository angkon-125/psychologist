"""
Conversation State Machine

Defines the states and valid transitions for the voice conversation pipeline.
Thread-safe state management with enter/exit callbacks.
"""

from enum import Enum
from typing import Dict, Optional, Callable, List
import threading
import logging

logger = logging.getLogger("zara.voice.conversation_state")


class ConversationState(Enum):
    """All possible states in the voice conversation lifecycle."""
    IDLE = "idle"
    LISTENING = "listening"
    PAUSE_ANALYSIS = "pause_analysis"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


# Map of state -> set of valid next states
_VALID_TRANSITIONS: Dict[ConversationState, set] = {
    ConversationState.IDLE: {
        ConversationState.LISTENING,
        ConversationState.ERROR,
    },
    ConversationState.LISTENING: {
        ConversationState.PAUSE_ANALYSIS,
        ConversationState.IDLE,
        ConversationState.ERROR,
    },
    ConversationState.PAUSE_ANALYSIS: {
        ConversationState.LISTENING,       # pause too short, keep listening
        ConversationState.THINKING,        # user finished speaking
        ConversationState.IDLE,            # cancelled
        ConversationState.ERROR,
    },
    ConversationState.THINKING: {
        ConversationState.SPEAKING,
        ConversationState.IDLE,            # cancelled
        ConversationState.ERROR,
    },
    ConversationState.SPEAKING: {
        ConversationState.LISTENING,       # barge-in or auto-return
        ConversationState.IDLE,            # finished or cancelled
        ConversationState.ERROR,
    },
    ConversationState.ERROR: {
        ConversationState.IDLE,
        ConversationState.LISTENING,
    },
}


# Human-readable messages emitted on state entry
_STATE_MESSAGES: Dict[ConversationState, str] = {
    ConversationState.IDLE: "Voice mode ready. Tap the mic to speak.",
    ConversationState.LISTENING: "I'm listening...",
    ConversationState.PAUSE_ANALYSIS: "I'm listening...",
    ConversationState.THINKING: "Thinking locally...",
    ConversationState.SPEAKING: "Speaking...",
    ConversationState.ERROR: "Something went wrong. Please try again.",
}


class ConversationStateMachine:
    """
    Thread-safe conversation state machine.

    Usage:
        sm = ConversationStateMachine()
        sm.on_enter(ConversationState.LISTENING, my_callback)
        sm.transition_to(ConversationState.LISTENING)
    """

    def __init__(self):
        self._state = ConversationState.IDLE
        self._lock = threading.Lock()
        self._enter_callbacks: Dict[ConversationState, List[Callable]] = {}
        self._exit_callbacks: Dict[ConversationState, List[Callable]] = {}
        self._global_listeners: List[Callable] = []  # called on every transition

    # ── Properties ─────────────────────────────────────────────────

    @property
    def state(self) -> ConversationState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.value

    @property
    def message(self) -> str:
        return _STATE_MESSAGES.get(self._state, "")

    # ── Transition ─────────────────────────────────────────────────

    def transition_to(self, new_state: ConversationState, reason: str = "") -> bool:
        """
        Attempt a state transition.

        Returns True if the transition was valid and executed.
        Returns False if the transition is not allowed from the current state.
        """
        with self._lock:
            old_state = self._state

            if new_state not in _VALID_TRANSITIONS.get(old_state, set()):
                logger.warning(
                    "Invalid transition: %s -> %s (reason: %s)",
                    old_state.value, new_state.value, reason,
                )
                return False

            # Fire exit callbacks for old state
            for cb in self._exit_callbacks.get(old_state, []):
                try:
                    cb(old_state, new_state)
                except Exception as e:
                    logger.error("Exit callback error: %s", e)

            self._state = new_state
            logger.info(
                "State: %s -> %s%s",
                old_state.value, new_state.value,
                f" ({reason})" if reason else "",
            )

            # Fire enter callbacks for new state
            for cb in self._enter_callbacks.get(new_state, []):
                try:
                    cb(old_state, new_state)
                except Exception as e:
                    logger.error("Enter callback error: %s", e)

            # Fire global listeners
            for cb in self._global_listeners:
                try:
                    cb(old_state, new_state)
                except Exception as e:
                    logger.error("Global listener error: %s", e)

            return True

    def force_to(self, new_state: ConversationState):
        """Force a state transition without validation (use sparingly)."""
        with self._lock:
            old_state = self._state
            self._state = new_state
            logger.warning("Forced state: %s -> %s", old_state.value, new_state.value)

    # ── Callbacks ──────────────────────────────────────────────────

    def on_enter(self, state: ConversationState, callback: Callable):
        """Register a callback for when *state* is entered."""
        self._enter_callbacks.setdefault(state, []).append(callback)

    def on_exit(self, state: ConversationState, callback: Callable):
        """Register a callback for when *state* is exited."""
        self._exit_callbacks.setdefault(state, []).append(callback)

    def on_any_transition(self, callback: Callable):
        """Register a callback for every transition: callback(old, new)."""
        self._global_listeners.append(callback)

    # ── Queries ────────────────────────────────────────────────────

    def can_transition_to(self, state: ConversationState) -> bool:
        """Check whether a transition to *state* is currently valid."""
        return state in _VALID_TRANSITIONS.get(self._state, set())

    def is_active(self) -> bool:
        """True if the machine is not in IDLE or ERROR."""
        return self._state not in (ConversationState.IDLE, ConversationState.ERROR)

    def reset(self):
        """Reset to IDLE state."""
        with self._lock:
            self._state = ConversationState.IDLE
