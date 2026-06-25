
from abc import ABC, abstractmethod
from .models import TTSRequest, TTSResult


class BaseTTSEngine(ABC):
    name: str = "base"

    def __init__(self):
        self._initialized = False

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available on this system"""
        pass

    @abstractmethod
    def initialize(self):
        """Initialize the TTS engine"""
        pass

    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """Synthesize speech from text"""
        pass

    @abstractmethod
    def stop(self):
        """Stop any currently playing speech"""
        pass

    @abstractmethod
    def get_available_voices(self, language: str = "en"):
        """Get list of available voices for the engine"""
        pass
