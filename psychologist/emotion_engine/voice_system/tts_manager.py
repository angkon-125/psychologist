
from typing import Optional, Callable
from queue import Queue
import threading
from .models import TTSRequest, TTSResult
from .espeak_engine import ESpeakEngine
from .audio_config import AudioConfig


class TTSManager:
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.espeak_engine = ESpeakEngine()
        self._queue = Queue()
        self._worker_thread = None
        self._is_speaking = False
        self._stop_requested = False
        self._result_callback: Optional[Callable[[TTSResult], None]] = None
        self._activity_callback: Optional[Callable[[str], None]] = None

    def initialize_engines(self):
        self.espeak_engine.initialize()

    def set_result_callback(self, callback: Optional[Callable[[TTSResult], None]]):
        self._result_callback = callback

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    def queue_speech(self, request: TTSRequest):
        self._queue.put(request)
        if not self._worker_thread or not self._worker_thread.is_alive():
            self._stop_requested = False
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

    def speak(self, text: str, language: str = "en", emotion_style: Optional[str] = None, save: bool = False):
        request = TTSRequest(
            text=text,
            language=language,
            speed=self.config.get("tts.speed", 1.0),
            pitch=self.config.get("tts.pitch", 1.0),
            volume=self.config.get("tts.volume", 0.9),
            emotion_style=emotion_style,
            save_to_file=save
        )
        self.queue_speech(request)

    def stop(self):
        self._stop_requested = True
        self.espeak_engine.stop()
        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Exception:
                pass

    def replay_last(self):
        # Replay not implemented yet, placeholder
        pass

    def _worker_loop(self):
        while not self._stop_requested:
            try:
                request = self._queue.get(timeout=0.5)
                self._is_speaking = True
                self._log_activity("Generating voice output")
                # Try engines in order of preference
                result = None
                if self.config.tts_default_engine == "espeak" and self.espeak_engine.is_available():
                    result = self.espeak_engine.synthesize(request)
                else:
                    # Fallback to espeak
                    if self.espeak_engine.is_available():
                        result = self.espeak_engine.synthesize(request)
                if result and self._result_callback:
                    self._result_callback(result)
                self._log_activity("Speaking response")
            except Exception as e:
                print(f"TTS worker error: {e}")
            finally:
                self._is_speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

