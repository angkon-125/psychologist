
from typing import List, Optional
import logging
from .base_tts_engine import BaseTTSEngine
from .models import TTSRequest, TTSResult
import os
import wave
import numpy as np

logger = logging.getLogger("zara.tts.pyttsx3")


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
            logger.warning("Failed to initialize pyttsx3: %s", e)
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
            engine.setProperty('volume', max(0.0, min(1.0, request.volume)))

            # Set voice: prefer female voices for ZARA
            voices = engine.getProperty('voices')
            selected_voice_id = self._select_female_voice(voices, request)
            if selected_voice_id:
                engine.setProperty('voice', selected_voice_id)

            # Apply pitch if the engine supports it (pyttsx3 on some platforms)
            try:
                engine.setProperty('pitch', request.pitch)
            except Exception:
                # Pitch not supported on this platform — silently ignore
                pass

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

    def _select_female_voice(self, voices, request) -> str:
        """
        Select the best available female voice for ZARA.

        Priority:
        1. If voice_id is explicitly set, use it.
        2. Search for known female voice names (Zira, Hazel, Susan, Heera, etc.)
        3. Search for voices tagged with 'female' or 'woman'
        4. For Bangla, try to find a Bangla voice
        5. Fall back to default voice and log a warning
        """
        if not voices:
            return None

        # 1. Explicit voice_id
        if request.voice_id:
            for voice in voices:
                if request.voice_id in voice.id:
                    return voice.id

        # Known female voice name patterns (case-insensitive)
        female_name_patterns = [
            'zira', 'hazel', 'susan', 'heera', 'samantha',
            'karen', 'tessa', 'fiona', 'moira', 'veena',
            'microsoft zira', 'microsoft hazel', 'microsoft susan',
            'google uk english female', 'google us english',
        ]

        # 2. Search for known female voice names
        for voice in voices:
            name_lower = voice.name.lower()
            for pattern in female_name_patterns:
                if pattern in name_lower:
                    logger.info("Selected female voice: %s", voice.name)
                    return voice.id

        # 3. Search for 'female' or 'woman' in voice name/id
        for voice in voices:
            combined = (voice.name + ' ' + getattr(voice, 'id', '')).lower()
            if 'female' in combined or 'woman' in combined:
                logger.info("Selected female-tagged voice: %s", voice.name)
                return voice.id

        # 4. For Bangla, try to find a Bangla voice
        if request.language in ["bn", "bn_bd"]:
            for voice in voices:
                combined = (voice.name + ' ' + getattr(voice, 'id', '')).lower()
                if "bangla" in combined or "bengali" in combined or "bn" in combined:
                    logger.info("Selected Bangla voice: %s", voice.name)
                    return voice.id

        # 5. Fallback: use default voice
        logger.warning("No female voice found, using default pyttsx3 voice")
        return None

    def stop(self):
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass
