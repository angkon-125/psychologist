
from typing import Optional
from pathlib import Path
from .models import TTSRequest, TTSResult
import os


class ESpeakEngine:
    def __init__(self):
        self.engine = None
        self._initialized = False

    def initialize(self):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self._initialized = True
        except ImportError:
            print("pyttsx3 not installed. Install with: pip install pyttsx3")
            self._initialized = False
        except Exception as e:
            print(f"Error initializing pyttsx3: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        return self._initialized

    def synthesize(self, request: TTSRequest) -> TTSResult:
        result = TTSResult(
            engine_name="espeak",
            success=False
        )
        if not self._initialized or not self.engine:
            result.error_message = "TTS engine not initialized"
            return result

        try:
            # Set properties
            self.engine.setProperty('rate', int(200 * request.speed))
            self.engine.setProperty('volume', request.volume)
            # Get voices
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to match language
                lang_prefix = request.language.split('-')[0]
                matched = None
                for voice in voices:
                    if lang_prefix in voice.id.lower() or lang_prefix in voice.languages or request.language in str(voice.languages):
                        matched = voice.id
                        break
                if not matched:
                    matched = voices[0].id
                self.engine.setProperty('voice', matched)
            # Save to file if requested
            if request.save_to_file:
                save_dir = Path(__file__).parent.parent.parent / "audio_outputs"
                save_dir.mkdir(exist_ok=True)
                filename = f"tts_{len(list(save_dir.glob('*.wav')))}.wav"
                save_path = save_dir / filename
                self.engine.save_to_file(request.text, str(save_path))
                result.audio_path = str(save_path)
            # Speak
            self.engine.say(request.text)
            self.engine.runAndWait()
            result.success = True
        except Exception as e:
            result.error_message = str(e)
            print(f"ESpeak error: {e}")
        return result

    def stop(self):
        if self._initialized and self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

