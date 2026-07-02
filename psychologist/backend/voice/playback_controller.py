"""
Playback Controller

Controls the TTS engines, play/pause state, and registers barge-in callbacks.
"""

import sys
from pathlib import Path
import logging

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

logger = logging.getLogger("zara.voice.playback")

class PlaybackController:
    """Controls TTS speaking and playback interruptions."""

    def __init__(self):
        self._tts_manager = None
        self._initialize()

    def _initialize(self):
        try:
            from emotion_engine.voice_output.tts_manager import TTSManager
            from emotion_engine.voice_output.single_voice_config import SingleVoiceConfig
            
            config = SingleVoiceConfig()
            self._tts_manager = TTSManager(config)
            logger.info("PlaybackController TTSManager initialized.")
        except Exception as e:
            logger.warning("TTS system not available in PlaybackController: %s", e)
            self._tts_manager = None

    def speak(self, text: str, language: str = "en") -> bool:
        if not self._tts_manager:
            return False
        try:
            self._tts_manager.speak(text, language=language)
            return True
        except Exception as e:
            logger.error("TTS playback failed: %s", e)
            return False

    def stop(self):
        if self._tts_manager:
            self._tts_manager.stop()
            logger.info("Playback stopped.")

    def pause(self):
        if self._tts_manager and hasattr(self._tts_manager, "pause"):
            self._tts_manager.pause()

    def resume(self):
        if self._tts_manager and hasattr(self._tts_manager, "resume"):
            self._tts_manager.resume()
            
    def is_speaking(self) -> bool:
        if self._tts_manager and hasattr(self._tts_manager, "is_speaking"):
            return self._tts_manager.is_speaking()
        return False
