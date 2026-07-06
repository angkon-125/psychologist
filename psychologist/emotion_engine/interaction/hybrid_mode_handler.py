"""
Hybrid Mode Handler

Allows the user to switch between text and voice input
within the same session, preserving emotional context
and conversation memory.
"""

from typing import Dict, Optional, Callable

from .interaction_models import InteractionMode
from .text_mode_handler import TextModeHandler
from .voice_mode_handler import VoiceModeHandler
from .session_manager import SessionManager
from .safety_support_layer import SafetySupportLayer


class HybridModeHandler:
    """
    Delegates to TextModeHandler or VoiceModeHandler
    based on input type, keeping a single session.
    """

    def __init__(
        self,
        text_handler: TextModeHandler,
        voice_handler: VoiceModeHandler,
        session_manager: Optional[SessionManager] = None,
    ):
        self._text_handler = text_handler
        self._voice_handler = voice_handler
        self._session_manager = session_manager
        self._activity_callback: Optional[Callable[[str], None]] = None

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback
        self._text_handler.set_activity_callback(callback)
        self._voice_handler.set_activity_callback(callback)

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Text input in hybrid mode ────────────────────────────────

    def process_text(
        self,
        text: str,
        language: str = "en",
        user_mood: Optional[str] = None,
        speak_response: bool = False,
        session_id: str = "",
        agent_mode: str = "assistant",
    ) -> Dict:
        """Process text input while preserving hybrid session context."""
        self._log_activity("Text input in hybrid mode")
        if self._session_manager:
            self._session_manager.update_mode("hybrid")

        return self._text_handler.process_text(
            text=text,
            language=language,
            user_mood=user_mood,
            speak_response=speak_response,
            session_id=session_id,
            agent_mode=agent_mode,
        )

    # ── Voice input in hybrid mode ───────────────────────────────

    def start_listening(self) -> Dict:
        """Start voice input capture."""
        self._log_activity("Voice input in hybrid mode")
        return self._voice_handler.start_listening()

    def stop_listening(self) -> Dict:
        """Stop voice capture."""
        return self._voice_handler.stop_listening()

    def process_voice_input(
        self,
        transcript: Optional[str] = None,
        language: str = "en",
        session_id: str = "",
    ) -> Dict:
        """Process voice input while preserving hybrid session context."""
        if self._session_manager:
            self._session_manager.update_mode("hybrid")

        return self._voice_handler.process_voice_input(
            transcript=transcript,
            language=language,
            session_id=session_id,
        )

    # ── Status ───────────────────────────────────────────────────

    def is_listening(self) -> bool:
        return self._voice_handler.is_listening()

    def is_speaking(self) -> bool:
        return self._voice_handler.is_speaking()

    def get_audio_level(self) -> float:
        return self._voice_handler.get_audio_level()

    def get_current_transcript(self) -> str:
        return self._voice_handler.get_current_transcript()

    def stop_speaking(self):
        self._voice_handler.stop_speaking()

    def replay_last_response(self):
        self._voice_handler.replay_last_response()

    def get_status(self) -> Dict:
        voice_status = self._voice_handler.get_status()
        voice_status["mode"] = "hybrid"
        return voice_status
