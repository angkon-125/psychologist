"""
Voice Engine — Conversational Voice Interaction System

Provides a complete offline voice conversation pipeline:
  - Wake word detection (stub, future phase)
  - Voice Activity Detection (VAD)
  - Smart pause detection with configurable thresholds
  - Speech recognition (Whisper / Vosk)
  - Response generation (Ollama optional, EmotionEngine fallback)
  - Speech synthesis (TTS)
  - Barge-in / interruption support
  - SSE event streaming to frontend

Usage:
    from emotion_engine.voice_engine import ConversationEngine, ResponseGenerator

    engine = ConversationEngine(
        stt_manager=stt_manager,
        tts_manager=tts_manager,
        response_generator=ResponseGenerator(emotion_engine, ollama_client),
    )
    engine.start_conversation()
"""

from .conversation_state import ConversationState, ConversationStateMachine
from .pause_detector import SmartPauseDetector, PauseState
from .barge_in import BargeInDetector
from .conversation_engine import ConversationEngine
from .response_generator import ResponseGenerator
from .voice_preferences import VoicePreferences
from .wake_word import WakeWordDetector

__all__ = [
    "ConversationState",
    "ConversationStateMachine",
    "SmartPauseDetector",
    "PauseState",
    "BargeInDetector",
    "ConversationEngine",
    "ResponseGenerator",
    "VoicePreferences",
    "WakeWordDetector",
]
