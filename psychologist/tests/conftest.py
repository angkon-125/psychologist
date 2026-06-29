"""
Shared pytest fixtures for ZARA test suite.

Provides a Flask test client with an isolated temp sessions directory
and optional TTS mocking so tests run without audio hardware.
"""

import sys
import os
import json
import shutil
import tempfile
from pathlib import Path

import pytest

# Ensure the psychologist package root is importable
_PSych_DIR = str(Path(__file__).resolve().parent.parent)
if _PSych_DIR not in sys.path:
    sys.path.insert(0, _PSych_DIR)


@pytest.fixture
def temp_sessions_dir():
    """Create a throwaway directory for session JSON files."""
    d = tempfile.mkdtemp(prefix="zara_test_sessions_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def app(temp_sessions_dir):
    """Flask application with session directory patched to a temp dir."""
    import app as app_module

    # Patch session manager to use temp dir
    original_dir = app_module.session_manager._sessions_dir
    app_module.session_manager._sessions_dir = Path(temp_sessions_dir)

    # End any existing session to start clean
    if app_module.session_manager._current_session:
        app_module.session_manager.end_session()

    yield app_module.app

    # Cleanup
    if app_module.session_manager._current_session:
        app_module.session_manager.end_session()
    app_module.session_manager._sessions_dir = original_dir


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_tts():
    """Minimal mock TTS manager that records speak() calls."""

    class MockTTSResult:
        def __init__(self, text, language="en", emotion="neutral"):
            self.success = True
            self.audio_path = None
            self.text = text
            self.language = language
            self.emotion = emotion

        def to_dict(self):
            return {
                "success": self.success,
                "audio_path": self.audio_path,
                "text": self.text,
                "language": self.language,
                "emotion": self.emotion,
            }

    class MockTTSManager:
        def __init__(self):
            self.spoken = []
            self._stopped = False

        def speak(self, text, language="en", emotion=None, save=False):
            self.spoken.append({"text": text, "language": language, "emotion": emotion})
            return MockTTSResult(text, language, emotion or "neutral")

        def stop(self):
            self._stopped = True

        def replay_last(self):
            pass

        def get_voice_status(self):
            return {"active_engine": "mock", "voice_locked": True}

        def set_activity_callback(self, cb):
            pass

    return MockTTSManager()


@pytest.fixture
def sample_session_json():
    """Return a sample session dict as would be stored on disk."""
    return {
        "session_id": "test-uuid-1234",
        "active_mode": "text",
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T10:30:00",
        "last_interaction_time": "2025-01-01T10:25:00",
        "current_emotion_state": {"intensity": 0.5},
        "mood_timeline": [
            {"emotion": "sad", "confidence": 0.7, "timestamp": "2025-01-01T10:05:00", "input_type": "text"}
        ],
        "safety_flags": [],
        "user_messages": [
            {"raw_text": "I feel sad", "detected_emotion": "sad"},
            {"raw_text": "I feel better now", "detected_emotion": "happy"},
        ],
        "assistant_messages": [
            {"response_text": "I understand.", "response_type": "supportive"},
        ],
        "detected_emotions": ["sad", "happy"],
        "summary": "Session with 2 interactions.",
        "follow_up_suggestions": ["Take care of yourself."],
        "user_preference_snapshot": {},
        "language": "en",
    }
