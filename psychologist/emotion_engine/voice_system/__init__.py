"""
Offline Voice System for Synthetic Emotional Mind

STT, voice emotion detection, and audio processing components.
TTS classes are re-exported from voice_output for backward compatibility.
"""

from .models import (
    AudioInputConfig,
    SpeechRecognitionResult,
    VoiceEmotionFeatures,
    VoiceEmotionResult,
    MultimodalEmotionState,
)

# Re-export TTS classes from voice_output for backward compatibility
# (voice_system previously had its own duplicate TTS implementation)
from ..voice_output import TTSManager, TTSRequest, TTSResult, VoiceStyle

__all__ = [
    "AudioInputConfig",
    "SpeechRecognitionResult",
    "VoiceEmotionFeatures",
    "VoiceEmotionResult",
    "MultimodalEmotionState",
    # Re-exported from voice_output
    "TTSManager",
    "TTSRequest",
    "TTSResult",
    "VoiceStyle",
]

