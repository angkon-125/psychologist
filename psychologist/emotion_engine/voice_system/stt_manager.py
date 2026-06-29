
import numpy as np
import wave
import threading
import logging
from pathlib import Path
from typing import Optional, Callable
from .models import AudioInputConfig, SpeechRecognitionResult
from .whisper_engine import WhisperEngine
from .audio_config import AudioConfig
from .microphone import Microphone
from .audio_preprocessor import AudioPreprocessor

logger = logging.getLogger("zara.voice.stt")


class STTManager:
    def __init__(self, config: Optional[AudioInputConfig] = None):
        self.config = config or AudioInputConfig()
        self.audio_config = AudioConfig()
        self.whisper_engine = WhisperEngine()
        self.microphone = Microphone()
        self.preprocessor = AudioPreprocessor()
        self.is_listening = False
        self._listen_thread = None
        self._result_callback: Optional[Callable[[SpeechRecognitionResult], None]] = None
        self._activity_callback: Optional[Callable[[str], None]] = None
        self._current_language = "en"

    def initialize_engines(self):
        if self.whisper_engine.is_available():
            self.whisper_engine.initialize()

    def set_result_callback(self, callback: Optional[Callable[[SpeechRecognitionResult], None]]):
        self._result_callback = callback

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    def start_continuous_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def _listen_loop(self):
        audio_buffer = []
        try:
            self.microphone.clear_queue()
            self.microphone.start_recording()
            while self.is_listening:
                chunk = self.microphone.get_audio_chunk(timeout=0.1)
                if chunk is not None:
                    audio_buffer.append(chunk)
        except Exception as e:
            logger.error("Listening loop error: %s", e)
        finally:
            self.is_listening = False
            self.microphone.stop_recording()
            if audio_buffer:
                full_audio = np.concatenate(audio_buffer)
                self._process_audio(full_audio)

    def stop_listening(self):
        self.is_listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=2.0)
        self.microphone.stop_recording()

    def _process_audio(self, audio: np.ndarray):
        self._log_activity("Transcribing audio")
        # Preprocess
        processed = self.preprocessor.preprocess_full(audio, self.microphone.config.sample_rate)
        # Choose engine
        result = SpeechRecognitionResult(
            engine_name="dummy",
            language=self._current_language,
            final=True
        )
        if self.whisper_engine._initialized:
            temp_path = Path(__file__).parent.parent.parent / "logs" / "temp_audio.wav"
            temp_path.parent.mkdir(exist_ok=True)
            self._save_wav(temp_path, processed, self.microphone.config.sample_rate)
            result = self.whisper_engine.transcribe_audio_file(str(temp_path), self._current_language)
        if result.final and self._result_callback:
            self._result_callback(result)

    def _save_wav(self, path: Path, audio: np.ndarray, sample_rate: int):
        wav_file = wave.open(str(path), 'wb')
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        audio_int16 = (audio * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())
        wav_file.close()

    def set_language(self, language: str):
        self._current_language = language
