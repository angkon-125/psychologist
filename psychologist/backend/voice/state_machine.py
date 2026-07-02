"""
Voice State Machine

Defines the states and transitions for the voice interaction loop.
"""

from enum import Enum
from typing import Dict, Set, List, Callable
import threading
import logging

logger = logging.getLogger("zara.voice.state_machine")

class VoiceState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    USER_SPEAKING = "USER_SPEAKING"
    USER_PAUSED = "USER_PAUSED"
    FINALIZING = "FINALIZING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"

_VALID_TRANSITIONS: Dict[VoiceState, Set[VoiceState]] = {
    VoiceState.IDLE: {VoiceState.LISTENING, VoiceState.ERROR},
    VoiceState.LISTENING: {VoiceState.USER_SPEAKING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.USER_SPEAKING: {VoiceState.USER_PAUSED, VoiceState.FINALIZING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.USER_PAUSED: {VoiceState.USER_SPEAKING, VoiceState.FINALIZING, VoiceState.LISTENING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.FINALIZING: {VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.PROCESSING: {VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.SPEAKING: {VoiceState.LISTENING, VoiceState.IDLE, VoiceState.ERROR},
    VoiceState.ERROR: {VoiceState.IDLE, VoiceState.LISTENING}
}

class VoiceStateMachine:
    """Thread-safe voice state machine for multi-agent coordination."""

    def __init__(self):
        self._state = VoiceState.IDLE
        self._lock = threading.Lock()
        self._listeners: List[Callable[[VoiceState, VoiceState], None]] = []

    @property
    def state(self) -> VoiceState:
        return self._state

    def register_listener(self, callback: Callable[[VoiceState, VoiceState], None]):
        self._listeners.append(callback)

    def transition_to(self, new_state: VoiceState, reason: str = "") -> bool:
        with self._lock:
            old_state = self._state
            if new_state not in _VALID_TRANSITIONS.get(old_state, set()):
                logger.warning("Invalid Voice state transition: %s -> %s (%s)", old_state.name, new_state.name, reason)
                return False
            self._state = new_state
            logger.info("Voice state: %s -> %s (%s)", old_state.name, new_state.name, reason)
            
        for listener in self._listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                logger.error("State transition listener failed: %s", e)
        return True

    def reset(self):
        with self._lock:
            self._state = VoiceState.IDLE
