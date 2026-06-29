"""
Tests for session lifecycle, persistence, and query methods.

Covers:
  - Session create / save / load / end
  - Summary generation
  - Follow-up suggestion logic
  - Recurring emotion analysis
  - Preferred mode detection
  - Old session cleanup
"""

import json
import time
from pathlib import Path

import pytest

from emotion_engine.interaction.session_manager import SessionManager
from emotion_engine.interaction.interaction_models import (
    UserMessage,
    AssistantMessage,
    SessionState,
)


@pytest.fixture
def manager(temp_sessions_dir):
    """SessionManager backed by a temp directory."""
    return SessionManager(
        sessions_dir=temp_sessions_dir,
        max_stored_sessions=5,
        auto_save=True,
    )


class TestSessionLifecycle:
    def test_start_session_returns_state(self, manager):
        session = manager.start_session(mode="text", language="en")
        assert session.session_id
        assert session.active_mode == "text"
        assert session.language == "en"
        assert manager.has_active_session() is True

    def test_start_ends_previous_session(self, manager):
        first = manager.start_session(mode="text")
        first_id = first.session_id
        second = manager.start_session(mode="hybrid")
        assert second.session_id != first_id
        assert manager.get_current_session().session_id == second.session_id

    def test_end_session_clears_current(self, manager):
        manager.start_session(mode="text")
        result = manager.end_session()
        assert result is not None
        assert "summary" in result
        assert manager.has_active_session() is False

    def test_end_session_without_active(self, manager):
        result = manager.end_session()
        assert result is None

    def test_get_current_session(self, manager):
        session = manager.start_session(mode="voice")
        current = manager.get_current_session()
        assert current is not None
        assert current.session_id == session.session_id


class TestMessageRecording:
    def test_add_user_message(self, manager):
        manager.start_session(mode="text")
        msg = UserMessage(raw_text="Hello world", detected_emotion="happy", confidence=0.8)
        manager.add_user_message(msg)

        session = manager.get_current_session()
        assert len(session.user_messages) == 1
        assert session.user_messages[0]["raw_text"] == "Hello world"
        assert session.detected_emotions == ["happy"]
        assert len(session.mood_timeline) == 1

    def test_add_assistant_message(self, manager):
        manager.start_session(mode="text")
        msg = AssistantMessage(response_text="Hi there", response_type="supportive")
        manager.add_assistant_message(msg)

        session = manager.get_current_session()
        assert len(session.assistant_messages) == 1
        assert session.assistant_messages[0]["response_text"] == "Hi there"

    def test_safety_flags_recorded(self, manager):
        manager.start_session(mode="text")
        msg = AssistantMessage(
            response_text="Crisis support",
            response_type="crisis_support",
            safety_level="high",
        )
        manager.add_assistant_message(msg)

        session = manager.get_current_session()
        assert "high" in session.safety_flags

    def test_update_emotion_state(self, manager):
        manager.start_session(mode="text")
        manager.update_emotion_state({"intensity": 0.7, "dominant": "sadness"})
        session = manager.get_current_session()
        assert session.current_emotion_state["dominant"] == "sadness"

    def test_update_mode(self, manager):
        manager.start_session(mode="text")
        manager.update_mode("voice")
        assert manager.get_current_session().active_mode == "voice"

    def test_update_preferences(self, manager):
        manager.start_session(mode="text")
        manager.update_preferences({"language": "bn"})
        assert manager.get_current_session().user_preference_snapshot["language"] == "bn"


class TestPersistence:
    def test_session_saved_to_disk(self, manager, temp_sessions_dir):
        manager.start_session(mode="text")
        msg = UserMessage(raw_text="Persist me", detected_emotion="neutral")
        manager.add_user_message(msg)

        files = list(Path(temp_sessions_dir).glob("session_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["user_messages"][0]["raw_text"] == "Persist me"

    def test_end_session_writes_summary(self, manager, temp_sessions_dir):
        manager.start_session(mode="text")
        msg = UserMessage(raw_text="I feel sad", detected_emotion="sad")
        manager.add_user_message(msg)
        result = manager.end_session()

        files = list(Path(temp_sessions_dir).glob("session_*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["summary"] == result["summary"]
        assert "sad" in data["detected_emotions"]

    def test_auto_save_disabled(self, temp_sessions_dir):
        mgr = SessionManager(sessions_dir=temp_sessions_dir, auto_save=False)
        mgr.start_session(mode="text")
        msg = UserMessage(raw_text="No auto save")
        mgr.add_user_message(msg)

        files = list(Path(temp_sessions_dir).glob("session_*.json"))
        assert len(files) == 0

    def test_session_history(self, manager, temp_sessions_dir):
        # Create and end three sessions
        for i in range(3):
            manager.start_session(mode="text")
            msg = UserMessage(raw_text=f"Message {i}", detected_emotion="happy" if i % 2 == 0 else "sad")
            manager.add_user_message(msg)
            manager.end_session()

        history = manager.get_session_history(limit=10)
        assert len(history) == 3
        assert "session_id" in history[0]
        assert "message_count" in history[0]
        assert history[0]["message_count"] == 1


class TestSummaryGeneration:
    def test_summary_includes_message_count(self, manager):
        manager.start_session(mode="text")
        for i in range(3):
            msg = UserMessage(raw_text=f"Msg {i}", detected_emotion="happy")
            manager.add_user_message(msg)
        result = manager.end_session()
        assert "3 interactions" in result["summary"]

    def test_summary_dominant_emotion(self, manager):
        manager.start_session(mode="text")
        emotions = ["sad", "sad", "happy"]
        for e in emotions:
            msg = UserMessage(raw_text="test", detected_emotion=e)
            manager.add_user_message(msg)
        result = manager.end_session()
        assert "sad" in result["summary"]

    def test_summary_safety_note(self, manager):
        manager.start_session(mode="text")
        msg = AssistantMessage(response_text="crisis help", safety_level="high")
        manager.add_assistant_message(msg)
        result = manager.end_session()
        assert "Safety support" in result["summary"]

    def test_summary_empty_session(self, manager):
        manager.start_session(mode="text")
        result = manager.end_session()
        assert "0 interactions" in result["summary"]
        assert "neutral" in result["summary"]


class TestFollowUpSuggestions:
    def test_distress_triggers_breathing_suggestion(self, manager):
        manager.start_session(mode="text")
        for e in ["sad", "anger", "fear"]:
            msg = UserMessage(raw_text="test", detected_emotion=e)
            manager.add_user_message(msg)
        result = manager.end_session()
        suggestions = result["follow_up_suggestions"]
        assert any("breathing" in s.lower() or "grounding" in s.lower() for s in suggestions)

    def test_stress_triggers_break_suggestion(self, manager):
        manager.start_session(mode="text")
        msg = UserMessage(raw_text="stressed", detected_emotion="stress")
        manager.add_user_message(msg)
        result = manager.end_session()
        suggestions = result["follow_up_suggestions"]
        assert any("break" in s.lower() or "enjoy" in s.lower() for s in suggestions)

    def test_always_has_professional_help(self, manager):
        manager.start_session(mode="text")
        msg = UserMessage(raw_text="hi", detected_emotion="happy")
        manager.add_user_message(msg)
        result = manager.end_session()
        suggestions = result["follow_up_suggestions"]
        assert any("professional" in s.lower() or "trusted" in s.lower() for s in suggestions)

    def test_no_emotions_still_has_reminder(self, manager):
        manager.start_session(mode="text")
        result = manager.end_session()
        assert len(result["follow_up_suggestions"]) >= 1


class TestRecurringEmotions:
    def test_recurring_emotions(self, manager, temp_sessions_dir):
        for emotion in ["happy", "happy", "sad"]:
            manager.start_session(mode="text")
            msg = UserMessage(raw_text="test", detected_emotion=emotion)
            manager.add_user_message(msg)
            manager.end_session()

        recurring = manager.get_recurring_emotions()
        assert recurring.get("happy", 0) == 2
        assert recurring.get("sad", 0) == 1

    def test_recurring_empty(self, manager):
        recurring = manager.get_recurring_emotions()
        assert recurring == {}


class TestPreferredMode:
    def test_preferred_mode(self, manager):
        for mode in ["text", "text", "voice"]:
            manager.start_session(mode=mode)
            manager.end_session()
        assert manager.get_preferred_mode() == "text"

    def test_preferred_mode_default(self, manager):
        assert manager.get_preferred_mode() == "hybrid"


class TestCleanupOldSessions:
    def test_cleanup_removes_oldest(self, temp_sessions_dir):
        mgr = SessionManager(
            sessions_dir=temp_sessions_dir,
            max_stored_sessions=3,
        )
        for i in range(5):
            mgr.start_session(mode="text")
            mgr.add_user_message(UserMessage(raw_text=f"msg {i}"))
            mgr.end_session()
            time.sleep(0.01)  # Ensure different mtimes

        files = list(Path(temp_sessions_dir).glob("session_*.json"))
        assert len(files) == 3

    def test_cleanup_preserves_newest(self, temp_sessions_dir):
        mgr = SessionManager(
            sessions_dir=temp_sessions_dir,
            max_stored_sessions=2,
        )
        # Create sessions
        for i in range(4):
            mgr.start_session(mode="text")
            mgr.add_user_message(UserMessage(raw_text=f"msg {i}"))
            mgr.end_session()
            time.sleep(0.01)

        history = mgr.get_session_history(limit=10)
        assert len(history) == 2
