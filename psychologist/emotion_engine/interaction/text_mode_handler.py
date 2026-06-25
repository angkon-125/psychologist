"""
Text Mode Handler

Orchestrates the text interaction pipeline:
  User text → normalise → emotion detect → safety check →
  context analysis → memory → response → optional TTS → session save
"""

from typing import Dict, Optional, Callable
from datetime import datetime

from .interaction_models import (
    UserMessage,
    AssistantMessage,
    InputType,
)
from .safety_support_layer import SafetySupportLayer
from .session_manager import SessionManager


class TextModeHandler:
    """Handles the full text-mode interaction cycle."""

    def __init__(
        self,
        emotion_engine,
        tts_manager=None,
        safety_layer: Optional[SafetySupportLayer] = None,
        session_manager: Optional[SessionManager] = None,
        max_response_length: int = 500,
    ):
        self._emotion_engine = emotion_engine
        self._tts_manager = tts_manager
        self._safety_layer = safety_layer or SafetySupportLayer()
        self._session_manager = session_manager
        self._max_response_length = max_response_length
        self._activity_callback: Optional[Callable[[str], None]] = None

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Main processing ──────────────────────────────────────────

    def process_text(
        self,
        text: str,
        language: str = "en",
        user_mood: Optional[str] = None,
        speak_response: bool = False,
        session_id: str = "",
    ) -> Dict:
        """
        Process a text message through the full pipeline.

        Returns a dict with:
          user_message, assistant_message, emotion_result, safety_assessment
        """
        self._log_activity("Text mode active")

        # 1. Normalise text
        normalized = self._normalize_text(text)

        # 2. Safety check FIRST
        self._log_activity("Checking safety")
        safety = self._safety_layer.assess_input(normalized, language)

        # 3. Process through emotion engine
        self._log_activity("Analyzing emotional tone")
        emotion_result = self._emotion_engine.process_input(normalized)

        dominant_emotion = emotion_result.get("dominant_emotion", "neutral")
        confidence = emotion_result.get("emotional_state", {}).get("intensity", 0.0)

        # 4. Build user message
        user_msg = UserMessage(
            session_id=session_id,
            input_type=InputType.TEXT.value,
            raw_text=text,
            normalized_text=normalized,
            language=language,
            detected_emotion=dominant_emotion,
            confidence=confidence,
            user_selected_mood=user_mood,
        )

        # 5. Generate response
        self._log_activity("Preparing supportive response")

        if safety.should_escalate:
            # Crisis response — use safe template
            response_text = safety.safe_response_template
            response_type = "crisis_support"
        else:
            # Normal response from emotion engine
            response_text = emotion_result.get("response", "")
            response_type = emotion_result.get("reasoning", {}).get("mode", "supportive")

            # Apply safety filter to the response
            response_text = self._safety_layer.filter_response(response_text)

            # Use distress template if moderate risk
            if safety.risk_level == "moderate" and safety.safe_response_template:
                response_text = safety.safe_response_template

        # Truncate for text mode
        if len(response_text) > self._max_response_length:
            response_text = response_text[:self._max_response_length].rsplit(" ", 1)[0] + "..."

        # 6. Build assistant message
        assistant_msg = AssistantMessage(
            session_id=session_id,
            response_text=response_text,
            response_language=language,
            response_type=response_type,
            spoken=False,
            safety_level=safety.risk_level,
        )

        # 7. Optional TTS output
        tts_result = None
        if speak_response and self._tts_manager:
            self._log_activity("Speaking response")
            tts_result = self._tts_manager.speak(
                response_text,
                language=language,
                emotion=dominant_emotion,
            )
            if tts_result and tts_result.success:
                assistant_msg.spoken = True
                assistant_msg.audio_path = tts_result.audio_path

        # 8. Save to session
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
                "dominant_emotion": dominant_emotion,
                "confidence": confidence,
                "emotional_state": emotion_result.get("emotional_state", {}),
            },
            "safety_assessment": safety.to_dict(),
        }

    # ── Text normalisation ───────────────────────────────────────

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Basic text normalisation — strip, collapse whitespace."""
        text = text.strip()
        # Collapse multiple spaces
        import re
        text = re.sub(r"\s+", " ", text)
        return text
