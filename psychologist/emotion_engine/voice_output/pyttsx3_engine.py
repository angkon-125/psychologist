
from typing import List, Optional
from .base_tts_engine import BaseTTSEngine
from .models import TTSRequest, TTSResult
import os
import wave
import numpy as np


class Pyttsx3Engine(BaseTTSEngine):
    name = "pyttsx3"

    def __init__(self):
        super().__init__()
        self.engine = None
        self._available_voices = []

    def is_available(self) -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def initialize(self):
        if self._initialized:
            return
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self._load_voices()
            self._initialized = True
        except Exception as e:
            print(f"Failed to initialize pyttsx3: {e}")
            self._initialized = False

    def _load_voices(self):
        if self.engine:
            self._available_voices = self.engine.getProperty('voices')

    def get_available_voices(self, language: str = "en"):
        if not self._initialized:
            self.initialize()
        return self._available_voices

    def synthesize(self, request: TTSRequest) -> TTSResult:
        result = TTSResult(engine_name=self.name)
        
        co_init = False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            co_init = True
        except Exception:
            pass

        try:
            import pyttsx3
            # Initialize a thread-local engine instance
            engine = pyttsx3.init()
            
            # Set properties
            rate = int(200 * request.speed)  # pyttsx3 default is ~200 wpm
            engine.setProperty('rate', rate)
            engine.setProperty('volume', request.volume)

            # Set voice based on language or voice_id
            voices = engine.getProperty('voices')
            if request.voice_id:
                for voice in voices:
                    if request.voice_id in voice.id:
                        engine.setProperty('voice', voice.id)
                        break
            else:
                if request.language in ["bn", "bn_bd"]:
                    # Try to find Bengali voice
                    for voice in voices:
                        if "bangla" in voice.name.lower() or "bengali" in voice.name.lower() or "bn" in voice.id.lower():
                            engine.setProperty('voice', voice.id)
                            break

            # Save to file if requested, otherwise play directly
            audio_path = None
            if request.save_to_file:
                from pathlib import Path
                output_dir = Path(__file__).parent.parent.parent.parent / "audio_outputs"
                output_dir.mkdir(exist_ok=True)
                audio_path = str(output_dir / f"tts_{len(list(output_dir.glob('*.wav'))) + 1}.wav")
                engine.save_to_file(request.text, audio_path)
                engine.runAndWait()
            else:
                engine.say(request.text)
                engine.runAndWait()

            result.success = True
            result.audio_path = audio_path
            result.duration_seconds = len(request.text) / 10  # rough estimate
        except Exception as e:
            result.error_message = str(e)
        finally:
            if co_init:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        return result

    def stop(self):
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
