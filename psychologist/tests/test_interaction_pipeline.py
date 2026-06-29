"""
Integration tests for the text-mode interaction pipeline.

Exercises the full flow:
  User text → normalise → safety check → emotion detect →
  response generation → optional TTS → session save

Tests cover normal input, crisis override, distress handling,
response filtering, TTS integration, and session recording.
"""

import pytest

from emotion_engine import EmotionEngine
from emotion_engine.interaction.text_mode_handler import TextModeHandler
from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
from emotion_engine.interaction.session_manager import SessionManager
from emotion_engine.interaction.interaction_models import InputType


@pytest.fixture
def pipeline(temp_sessions_dir, mock_tts):
    """Wire up a full text-mode pipeline with mock TTS."""
    emotion_engine = EmotionEngine()
    safety = SafetySupportLayer()
    sessions = SessionManager(sessions_dir=temp_sessions_dir)
    handler = TextModeHandler(
        emotion_engine=emotion_engine,
        tts_manager=mock_tts,
        safety_layer=safety,
        session_manager=sessions,
    )
    sessions.start_session(mode="text")
    session_id = sessions._current_session.session_id
    return handler, sessions, session_id, mock_tts


class TestNormalTextProcessing:
    def test_returns_all_keys(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I had a wonderful day!",
            session_id=session_id,
        )
        assert "user_message" in result
        assert "assistant_message" in result
        assert "emotion_result" in result
        assert "safety_assessment" in result

    def test_user_message_captured(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I'm feeling great",
            session_id=session_id,
        )
        user_msg = result["user_message"]
        assert user_msg["raw_text"] == "I'm feeling great"
        assert user_msg["input_type"] == InputType.TEXT.value
        assert user_msg["session_id"] == session_id

    def test_assistant_response_generated(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="Hello there",
            session_id=session_id,
        )
        assistant_msg = result["assistant_message"]
        assert len(assistant_msg["response_text"]) > 0
        assert assistant_msg["session_id"] == session_id

    def test_emotion_result_populated(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I am so happy and excited!",
            session_id=session_id,
        )
        emotion = result["emotion_result"]
        assert "dominant_emotion" in emotion
        assert "confidence" in emotion
        assert "emotional_state" in emotion

    def test_safety_none_for_neutral(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="The weather is nice today",
            session_id=session_id,
        )
        assert result["safety_assessment"]["risk_level"] == "none"
        assert result["safety_assessment"]["should_escalate"] is False


class TestCrisisOverride:
    def test_crisis_uses_safe_template(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I want to kill myself",
            session_id=session_id,
        )
        assert result["safety_assessment"]["should_escalate"] is True
        assert result["safety_assessment"]["risk_level"] in ("high", "critical")
        assert result["assistant_message"]["response_type"] == "crisis_support"

    def test_crisis_response_is_safe_template(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I want to end my life",
            session_id=session_id,
        )
        response_text = result["assistant_message"]["response_text"]
        safety = result["safety_assessment"]["safe_response_template"]
        assert response_text == safety
        assert len(response_text) > 20

    def test_crisis_overrides_emotion_response(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I'm so happy but I want to die",
            session_id=session_id,
        )
        assert result["safety_assessment"]["should_escalate"] is True
        assert result["assistant_message"]["response_type"] == "crisis_support"


class TestDistressHandling:
    def test_distress_detected(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I feel so stressed and overwhelmed",
            session_id=session_id,
        )
        assert result["safety_assessment"]["risk_level"] == "moderate"
        assert result["safety_assessment"]["should_escalate"] is False
        assert len(result["safety_assessment"]["safe_response_template"]) > 0

    def test_distress_uses_template_when_moderate(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="I'm very anxious and worried",
            session_id=session_id,
        )
        if result["safety_assessment"]["risk_level"] == "moderate":
            response = result["assistant_message"]["response_text"]
            template = result["safety_assessment"]["safe_response_template"]
            assert response == template


class TestResponseFiltering:
    def test_diagnosis_filtered_from_response(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="Tell me what I have, do I have depression?",
            session_id=session_id,
        )
        response = result["assistant_message"]["response_text"]
        # The response should not contain unfiltered diagnosis language
        assert "you have depression" not in response.lower()


class TestTextNormalization:
    def test_whitespace_collapsed(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="  Hello    world   ",
            session_id=session_id,
        )
        normalized = result["user_message"]["normalized_text"]
        assert normalized == "Hello world"
        assert "  " not in normalized

    def test_strips_leading_trailing(self, pipeline):
        handler, _, session_id, _ = pipeline
        result = handler.process_text(
            text="   Hello   ",
            session_id=session_id,
        )
        normalized = result["user_message"]["normalized_text"]
        assert normalized == "Hello"


class TestTTSIntegration:
    def test_speak_response_false(self, pipeline):
        handler, _, session_id, mock = pipeline
        result = handler.process_text(
            text="Hello",
            session_id=session_id,
            speak_response=False,
        )
        assert result["assistant_message"]["spoken"] is False
        assert len(mock.spoken) == 0

    def test_speak_response_true(self, pipeline):
        handler, _, session_id, mock = pipeline
        result = handler.process_text(
            text="Hello there",
            session_id=session_id,
            speak_response=True,
        )
        assert result["assistant_message"]["spoken"] is True
        assert len(mock.spoken) == 1
        assert mock.spoken[0]["text"] == result["assistant_message"]["response_text"]


class TestSessionRecording:
    def test_messages_saved_to_session(self, pipeline):
        handler, sessions, session_id, _ = pipeline
        handler.process_text(
            text="I feel happy",
            session_id=session_id,
        )
        session = sessions.get_current_session()
        assert len(session.user_messages) == 1
        assert len(session.assistant_messages) == 1
        assert session.detected_emotions == [
            session.user_messages[0]["detected_emotion"]
        ]

    def test_emotion_state_updated(self, pipeline):
        handler, sessions, session_id, _ = pipeline
        handler.process_text(
            text="I'm feeling great today",
            session_id=session_id,
        )
        session = sessions.get_current_session()
        assert len(session.current_emotion_state) > 0

    def test_multiple_interactions_accumulate(self, pipeline):
        handler, sessions, session_id, _ = pipeline
        for i in range(3):
            handler.process_text(
                text=f"Message number {i}",
                session_id=session_id,
            )
        session = sessions.get_current_session()
        assert len(session.user_messages) == 3
        assert len(session.assistant_messages) == 3

    def test_safety_flag_recorded_on_crisis(self, pipeline):
        handler, sessions, session_id, _ = pipeline
        handler.process_text(
            text="I want to kill myself",
            session_id=session_id,
        )
        session = sessions.get_current_session()
        assert len(session.safety_flags) >= 1


class TestResponseTruncation:
    def test_long_response_truncated(self, temp_sessions_dir):
        """Responses exceeding max_response_length get truncated."""
        emotion_engine = EmotionEngine()
        safety = SafetySupportLayer()
        sessions = SessionManager(sessions_dir=temp_sessions_dir)
        handler = TextModeHandler(
            emotion_engine=emotion_engine,
            tts_manager=None,
            safety_layer=safety,
            session_manager=sessions,
            max_response_length=50,
        )
        sessions.start_session(mode="text")
        session_id = sessions._current_session.session_id

        result = handler.process_text(
            text="I am feeling extremely happy and wonderful and amazing today",
            session_id=session_id,
        )
        response = result["assistant_message"]["response_text"]
        assert len(response) <= 53  # 50 + "..." (truncated at word boundary)
