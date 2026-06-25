"""
Voice Output Module

Single-voice local TTS system with voice locking, emotion style
adjustments, and offline-only operation.
"""

from .models import TTSRequest, TTSResult, VoiceStyle
from .single_voice_config import SingleVoiceConfig
from .voice_config import TTSConfig
from .voice_lock import VoiceLock
from .voice_style_mapper import VoiceStyleMapper
from .audio_player import AudioPlayer
from .tts_manager import TTSManager

__all__ = [
    "TTSRequest",
    "TTSResult",
    "VoiceStyle",
    "SingleVoiceConfig",
    "TTSConfig",
    "VoiceLock",
    "VoiceStyleMapper",
    "AudioPlayer",
    "TTSManager",
]
