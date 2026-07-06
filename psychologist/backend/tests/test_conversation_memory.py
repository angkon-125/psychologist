"""
Conversation Memory tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.memory.conversation_memory import ConversationMemory


@pytest.fixture
def conv():
    return ConversationMemory(window_size=10)


def test_initial_state(conv):
    """Starts empty with no session."""
    assert conv.turn_count == 0
    assert conv.session_id == ""
    assert conv.get_recent_context() == ""


def test_start_session(conv):
    """Session initialization works."""
    conv.start_session("session_001")
    assert conv.session_id == "session_001"
    assert conv.turn_count == 0


def test_add_and_retrieve(conv):
    """Add turns and retrieve recent context."""
    conv.start_session("s1")
    conv.add_turn("user", "I feel sad")
    conv.add_turn("assistant", "I'm sorry to hear that")
    
    assert conv.turn_count == 2
    context = conv.get_recent_context()
    assert "User: I feel sad" in context
    assert "ZARA: I'm sorry" in context


def test_sliding_window(conv):
    """Window drops oldest turns when full."""
    conv.start_session("s2")
    for i in range(15):
        conv.add_turn("user", f"Message {i}")
    
    # Window size is 10
    assert conv.turn_count == 10
    context = conv.get_recent_context(limit=15)
    assert "Message 0" not in context  # oldest dropped
    assert "Message 14" in context  # newest kept


def test_get_recent_turns(conv):
    """Structured turn retrieval works."""
    conv.start_session("s3")
    conv.add_turn("user", "Hello", intent="greeting", emotion="neutral")
    conv.add_turn("assistant", "Hi there!")
    
    turns = conv.get_recent_turns(limit=5)
    assert len(turns) == 2
    assert turns[0]["intent"] == "greeting"
    assert turns[0]["role"] == "user"


def test_get_last_user_emotion(conv):
    """Retrieves last user emotion correctly."""
    conv.start_session("s4")
    conv.add_turn("user", "I'm happy", emotion="joy")
    conv.add_turn("assistant", "Great!")
    conv.add_turn("user", "Actually I'm stressed", emotion="stress")
    
    assert conv.get_last_user_emotion() == "stress"


def test_get_intent_history(conv):
    """Intent history returns recent user intents."""
    conv.start_session("s5")
    conv.add_turn("user", "Hi", intent="greeting")
    conv.add_turn("assistant", "Hello")
    conv.add_turn("user", "I feel sad", intent="emotional_support")
    conv.add_turn("user", "Help me breathe", intent="breathing")
    
    history = conv.get_intent_history()
    assert history == ["greeting", "emotional_support", "breathing"]


def test_clear(conv):
    """Clear removes all turns."""
    conv.start_session("s6")
    conv.add_turn("user", "test")
    conv.clear()
    assert conv.turn_count == 0


def test_session_switch(conv):
    """Switching sessions clears the window."""
    conv.start_session("s7")
    conv.add_turn("user", "old session")
    conv.start_session("s8")
    assert conv.turn_count == 0
    assert conv.session_id == "s8"
