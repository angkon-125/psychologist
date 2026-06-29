
import os
import numpy as np
import logging
from typing import Optional
from pathlib import Path
from .models import SpeechRecognitionResult
from .audio_config import AudioConfig

logger = logging.getLogger("zara.voice.whisper")


class WhisperEngine:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.model = None
        self.model_name = "tiny.en"
        self._initialized = False
        self._downloaded_models_path = str(Path(__file__).parent.parent.parent / "models" / "stt" / "whisper")

    def _ensure_model_path(self):
        os.makedirs(self._downloaded_models_path, exist_ok=True)

    def initialize(self, model_name: str = "tiny.en", device: str = "cpu"):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_name, device=device, compute_type="int8")
            self._initialized = True
        except ImportError:
            logger.info("Faster Whisper not installed. Install with: pip install faster-whisper")
            self._initialized = False
        except Exception as e:
            logger.error("Error initializing Whisper: %s", e)
            self._initialized = False

    def is_available(self) -> bool:
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False

    def transcribe_audio_file(self, audio_path: str, language: str = "en") -> SpeechRecognitionResult:
        result = SpeechRecognitionResult(
            engine_name="whisper",
            language=language,
            final=True
        )
        if not self._initialized:
            return result

        try:
            segments, info = self.model.transcribe(audio_path, language=language, beam_size=5)
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            full_text = " ".join(text_parts)
            result.raw_text = full_text
            result.normalized_text = full_text
            result.confidence = info.language_probability if hasattr(info, 'language_probability') else 0.9
        except Exception as e:
            logger.error("Whisper transcription error: %s", e)
        return result

