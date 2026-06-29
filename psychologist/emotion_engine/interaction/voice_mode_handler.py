"""
Voice Mode Handler

Orchestrates the voice interaction pipeline:
  User speech → mic capture → local STT → voice emotion extraction →
  text emotion analysis → emotion fusion → safety check →
  response generation → local TTS → session save

Uses existing voice_system components for STT, feature extraction,
and emotion detection. Uses existing voice_output TTSManager for TTS.
"""

from typing import Dict, Optional, Callable
from datetime import datetime
import threading

from .interaction_models import (
    UserMessage,
    AssistantMessage,
    InputType,
)
from .safety_support_layer import SafetySupportLayer
from .session_manager import SessionManager

from system_constants import MAX_VOICE_RESPONSE_LENGTH


class VoiceModeHandler:
    """Handles the full voice-mode interaction cycle."""

    def __init__(
        self,
        emotion_engine,
        stt_manager=None,
        tts_manager=None,
        voice_feature_extractor=None,
        voice_emotion_detector=None,
        emotion_fusion=None,
        safety_layer: Optional[SafetySupportLayer] = None,
        session_manager: Optional[SessionManager] = None,
        max_response_length: int = MAX_VOICE_RESPONSE_LENGTH,
    ):
        self._emotion_engine = emotion_engine
        self._stt_manager = stt_manager
        self._tts_manager = tts_manager
        self._feature_extractor = voice_feature_extractor
        self._voice_emotion_detector = voice_emotion_detector
        self._emotion_fusion = emotion_fusion
        self._safety_layer = safety_layer or SafetySupportLayer()
        self._session_manager = session_manager
        self._max_response_length = max_response_length

        self._is_listening = False
        self._is_speaking = False
        self._current_transcript = ""
        self._current_audio_level = 0.0
        self._push_to_talk = True
        self._continuous_mode = False
        self._activity_callback: Optional[Callable[[str], None]] = None

        # Wire up STT result callback
        if self._stt_manager:
            self._stt_manager.set_result_callback(self._on_stt_result)

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Listening controls ───────────────────────────────────────

    def start_listening(self) -> Dict:
        """Start microphone capture and STT."""
        if self._is_listening:
            return {"status": "already_listening"}

        if not self._stt_manager:
            return {"status": "error", "message": "STT system not available"}

        self._is_listening = True
        self._current_transcript = ""
        self._log_activity("Listening")

        try:
            self._stt_manager.start_continuous_listening()
        except Exception as e:
            self._is_listening = False
            return {"status": "error", "message": str(e)}

        return {"status": "listening"}

    def stop_listening(self) -> Dict:
        """Stop microphone capture and process the captured audio."""
        if not self._is_listening:
            return {"status": "not_listening"}

        self._is_listening = False
        self._log_activity("Processing voice input")

        if self._stt_manager:
            self._stt_manager.stop_listening()

        return {
            "status": "stopped",
            "transcript": self._current_transcript,
        }

    def is_listening(self) -> bool:
        return self._is_listening

    def is_speaking(self) -> bool:
        return self._is_speaking

    def get_audio_level(self) -> float:
        """Get current microphone audio level for the UI meter."""
        if self._stt_manager and hasattr(self._stt_manager, "microphone"):
            return self._stt_manager.microphone.get_current_level()
        return 0.0

    def get_current_transcript(self) -> str:
        return self._current_transcript

    # ── STT callback ─────────────────────────────────────────────

    def _on_stt_result(self, result):
        """Called by STTManager when transcription is ready."""
        if result and result.final:
            self._current_transcript = result.normalized_text or result.raw_text
            self._log_activity("Transcribing")

    # ── Voice settings ───────────────────────────────────────────

    def set_push_to_talk(self, enabled: bool):
        self._push_to_talk = enabled

    def set_continuous_mode(self, enabled: bool):
        self._continuous_mode = enabled

    # ── Main processing ──────────────────────────────────────────

    def process_voice_input(
        self,
        transcript: Optional[str] = None,
        language: str = "en",
        session_id: str = "",
    ) -> Dict:
        """
        Process voice input through the full pipeline.

        If transcript is not provided, uses the last captured transcript.
        """
        self._log_activity("Voice mode active")

        text = transcript or self._current_transcript
        if not text:
            return {
                "status": "no_input",
                "message": "No speech detected. Please try again.",
            }

        # 1. Safety check
        self._log_activity("Checking safety")
        safety = self._safety_layer.assess_input(text, language)

        # 2. Text emotion analysis via emotion engine
        self._log_activity("Analyzing emotional tone")
        emotion_result = self._emotion_engine.process_input(text)

        dominant_emotion = emotion_result.get("dominant_emotion", "neutral")
        confidence = emotion_result.get("emotional_state", {}).get("intensity", 0.0)

        # 3. Voice emotion analysis (if feature extractor available)
        voice_emotion = {}
        if self._feature_extractor and self._voice_emotion_detector:
            # Voice emotion features would come from the audio buffer
            # For now, use text-only emotion (voice features require
            # raw audio which is processed in the STT pipeline)
            pass

        # 4. Emotion fusion (text + voice)
        fused_emotion = dominant_emotion
        fused_confidence = confidence
        if self._emotion_fusion and voice_emotion:
            text_emotions = emotion_result.get("emotional_state", {}).get(
                "primary_emotions", {}
            )
            fused = self._emotion_fusion.fuse_emotions(
                text_emotion=text_emotions,
                voice_emotion=voice_emotion,
            )
            fused_emotion = fused.dominant_emotion or dominant_emotion
            fused_confidence = fused.confidence

        # 5. Build user message
        user_msg = UserMessage(
            session_id=session_id,
            input_type=InputType.VOICE.value,
            raw_text=text,
            normalized_text=text.strip(),
            language=language,
            detected_emotion=fused_emotion,
            confidence=fused_confidence,
        )

        # 6. Generate response
        self._log_activity("Preparing supportive response")

        if safety.should_escalate:
            response_text = safety.safe_response_template
            response_type = "crisis_support"
        else:
            response_text = emotion_result.get("response", "")
            response_type = emotion_result.get("reasoning", {}).get("mode", "supportive")
            response_text = self._safety_layer.filter_response(response_text)

            if safety.risk_level == "moderate" and safety.safe_response_template:
                response_text = safety.safe_response_template

        # Voice responses are shorter
        if len(response_text) > self._max_response_length:
            # Try to cut at sentence boundary
            truncated = response_text[:self._max_response_length]
            last_period = truncated.rfind(".")
            if last_period > self._max_response_length * 0.5:
                response_text = truncated[:last_period + 1]
            else:
                response_text = truncated.rsplit(" ", 1)[0] + "..."

        # 7. Build assistant message
        assistant_msg = AssistantMessage(
            session_id=session_id,
            response_text=response_text,
            response_language=language,
            response_type=response_type,
            spoken=False,
            safety_level=safety.risk_level,
        )

        # 8. TTS output
        tts_result = None
        if self._tts_manager:
            self._log_activity("Speaking response")
            self._is_speaking = True
            tts_result = self._tts_manager.speak(
                response_text,
                language=language,
                emotion=fused_emotion,
            )
            self._is_speaking = False
            if tts_result and tts_result.success:
                assistant_msg.spoken = True
                assistant_msg.audio_path = tts_result.audio_path

        # 9. Save to session
        if self._session_manager:
            self._session_manager.add_user_message(user_msg)
            self._session_manager.add_assistant_message(assistant_msg)
            self._session_manager.update_emotion_state(
                emotion_result.get("emotional_state", {})
            )
            self._log_activity("Session saved")

        return {
            "user_message": user_msg.to_dict(),
            "assistant_message": assistant_msg.to_dict(),
            "emotion_result": {
                "dominant_emotion": fused_emotion,
                "confidence": fused_confidence,
                "emotional_state": emotion_result.get("emotional_state", {}),
            },
            "safety_assessment": safety.to_dict(),
            "transcript": text,
        }

    # ── Status ───────────────────────────────────────────────────

    def get_status(self) -> Dict:
        return {
            "is_listening": self._is_listening,
            "is_speaking": self._is_speaking,
            "audio_level": self.get_audio_level(),
            "current_transcript": self._current_transcript,
            "push_to_talk": self._push_to_talk,
            "continuous_mode": self._continuous_mode,
            "stt_available": self._stt_manager is not None,
            "tts_available": self._tts_manager is not None,
        }

    # ── Playback controls ────────────────────────────────────────

    def stop_speaking(self):
        """Stop the TTS playback."""
        if self._tts_manager:
            self._tts_manager.stop()
        self._is_speaking = False

    def replay_last_response(self):
        """Replay the last spoken response."""
        if self._tts_manager:
            self._tts_manager.replay_last()
