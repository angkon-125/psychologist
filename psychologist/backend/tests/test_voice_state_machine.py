"""
Voice state machine tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.voice.state_machine import VoiceStateMachine, VoiceState

def test_state_transitions():
    sm = VoiceStateMachine()
    
    assert sm.state == VoiceState.IDLE
    
    # Valid transitions
    assert sm.transition_to(VoiceState.LISTENING) is True
    assert sm.state == VoiceState.LISTENING
    
    assert sm.transition_to(VoiceState.USER_SPEAKING) is True
    assert sm.state == VoiceState.USER_SPEAKING
    
    assert sm.transition_to(VoiceState.USER_PAUSED) is True
    
    # Invalid transition
    assert sm.transition_to(VoiceState.SPEAKING) is False # Can't go directly to SPEAKING from USER_PAUSED
    
    # Finalizing and processing
    assert sm.transition_to(VoiceState.FINALIZING) is True
    assert sm.transition_to(VoiceState.PROCESSING) is True
    assert sm.transition_to(VoiceState.SPEAKING) is True
