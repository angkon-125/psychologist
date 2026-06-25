
from typing import List, Optional
from .base_tts_engine import BaseTTSEngine
from .models import TTSRequest, TTSResult
import os


class ESpeakEngine(BaseTTSEngine):
    name = "espeak"

    def __init__(self):
        super().__init__()

    def is_available(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(["espeak", "--version"], capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, ImportError, Exception):
            return False

    def initialize(self):
        self._initialized = True

    def get_available_voices(self, language: str = "en"):
        try:
            import subprocess
            result = subprocess.run(["espeak", "--voices"], capture_output=True, text=True, timeout=5)
            voices = []
            for line in result.stdout.splitlines()[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) > 1:
                        voices.append(parts[1])
            return voices
        except Exception as e:
            print(f"Failed to get eSpeak voices: {e}")
            return []

    def synthesize(self, request: TTSRequest) -> TTSResult:
        result = TTSResult(engine_name=self.name)
        try:
            import subprocess
            from pathlib import Path

            cmd = ["espeak"]

            # Set language
            lang_code = "en"
            if request.language == "bn" or request.language == "bn_bd":
                lang_code = "bn"
            cmd.extend(["-v", lang_code])

            # Set speed
            rate = int(175 * request.speed)  # eSpeak default is 175
            cmd.extend(["-s", str(rate)])

            # Set amplitude (volume)
            amplitude = int(100 * request.volume)
            cmd.extend(["-a", str(amplitude)])

            audio_path = None
            if request.save_to_file:
                output_dir = Path(__file__).parent.parent.parent.parent / "audio_outputs"
                output_dir.mkdir(exist_ok=True)
                audio_path = str(output_dir / f"tts_{len(list(output_dir.glob('*.wav'))) + 1}.wav")
                cmd.extend(["-w", audio_path])

            cmd.append(request.text)
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            result.success = True
            result.audio_path = audio_path
        except Exception as e:
            result.error_message = str(e)
        return result

    def stop(self):
        pass
