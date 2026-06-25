
import os
import numpy as np
from typing import Optional
from pathlib import Path
from .models import SpeechRecognitionResult
from .audio_config import AudioConfig


class VoskEngine:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.model = None
        self.rec = None
        self._initialized = False
        self._downloaded_models_path = str(Path(__file__).parent.parent.parent / "models" / "stt" / "vosk")
        self._ensure_model_path()

    def _ensure_model_path(self):
        os.makedirs(self._downloaded_models_path, exist_ok=True)

    def initialize(self, model_path: Optional[str] = None, language: str = "en"):
        try:
            import vosk
            # Try to find model
            model_dir = model_path or self._downloaded_models_path
            if not os.path.exists(model_dir) or not os.listdir(model_dir):
                print(f"Warning: No Vosk model found at {model_dir}. Using simple fallback.")
                self._initialized = False
                return

            # Initialize model
            self.model = vosk.Model(model_dir)
            self.rec = vosk.KaldiRecognizer(self.model, self.config.get("speech_recognition.sample_rate", 16000))
            self.rec.SetWords(True)
            self._initialized = True
        except ImportError:
            print("Vosk not installed. Install with: pip install vosk")
            self._initialized = False
        except Exception as e:
            print(f"Error initializing Vosk: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        try:
            import vosk
            return True
        except ImportError:
            return False

    def process_audio(self, audio: np.ndarray, language: str = "en") -> SpeechRecognitionResult:
        result = SpeechRecognitionResult(
            engine_name="vosk",
            language=language,
            final=False
        )
        if not self._initialized or not self.rec:
            return result

        try:
            import json
            audio_int16 = (audio * 32767).astype(np.int16).tobytes()
            if self.rec.AcceptWaveform(audio_int16):
                final_json = json.loads(self.rec.Result())
                text = final_json.get("text", "")
                if text:
                    result.raw_text = text
                    result.normalized_text = text.strip()
                    result.final = True
                    result.confidence = 0.8
            else:
                partial_json = json.loads(self.rec.PartialResult())
                partial = partial_json.get("partial", "")
                if partial:
                    result.raw_text = partial
                    result.partial = True
                    result.confidence = 0.5
        except Exception as e:
            print(f"Vosk processing error: {e}")
        return result

    def reset(self):
        if self.rec:
            self.rec.Reset()

