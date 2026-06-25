
from typing import List, Optional
from .base_tts_engine import BaseTTSEngine
from .models import TTSRequest, TTSResult
import os


class PiperEngine(BaseTTSEngine):
    name = "piper"

    def __init__(self):
        super().__init__()
        self._voice_dir = None

    def is_available(self) -> bool:
        try:
            import piper_tts
            return True
        except ImportError:
            try:
                import subprocess
                result = subprocess.run(["piper", "--help"], capture_output=True, text=True, timeout=2)
                return result.returncode == 0
            except Exception:
                return False

    def initialize(self):
        from pathlib import Path
        self._voice_dir = Path(__file__).parent.parent.parent.parent / "models" / "tts"
        self._voice_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    def get_available_voices(self, language: str = "en"):
        voices = []
        if self._voice_dir:
            for f in self._voice_dir.glob("*.onnx"):
                voices.append(f.stem)
        return voices

    def synthesize(self, request: TTSRequest) -> TTSResult:
        result = TTSResult(engine_name=self.name)
        if not self._initialized:
            self.initialize()

        try:
            from pathlib import Path

            output_dir = Path(__file__).parent.parent.parent.parent / "audio_outputs"
            output_dir.mkdir(exist_ok=True)
            audio_path = str(output_dir / f"tts_{len(list(output_dir.glob('*.wav'))) + 1}.wav")

            # Try piper-tts library first
            try:
                from piper import PiperVoice
                voice_file = None
                if request.voice_id:
                    voice_file = str(self._voice_dir / f"{request.voice_id}.onnx")
                elif request.language in ["bn", "bn_bd"]:
                    voice_file = str(self._voice_dir / "bn_default.onnx")
                else:
                    voice_file = str(self._voice_dir / "en_default.onnx")

                if os.path.exists(voice_file):
                    voice = PiperVoice.load(voice_file)
                    wav_path = audio_path if request.save_to_file else None
                    voice.synthesize(request.text, wav_file=wav_path)
                else:
                    result.error_message = "Piper voice model not found"
                    return result
            except ImportError:
                # Try command-line piper
                import subprocess
                cmd = ["piper"]
                if request.voice_id:
                    cmd.extend(["-m", str(self._voice_dir / f"{request.voice_id}.onnx")])
                cmd.extend(["-f", audio_path, "-t", request.text])
                subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            result.success = True
            result.audio_path = audio_path
        except Exception as e:
            result.error_message = str(e)

        return result

    def stop(self):
        pass
