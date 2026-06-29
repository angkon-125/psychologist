
import threading
import wave
import time
import logging
from typing import Optional

logger = logging.getLogger("zara.tts.audio_player")


try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.info("pyaudio not available, audio playback will be limited")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class AudioPlayer:
    def __init__(self):
        self._current_audio: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._is_playing = False
        self._pyaudio_instance = None
        self._pyaudio_stream = None

    def is_playing(self) -> bool:
        return self._is_playing

    def play_wav(self, file_path: str) -> bool:
        if self.is_playing():
            self.stop()

        self._stop_flag.clear()
        self._is_playing = True

        if PYAUDIO_AVAILABLE:
            self._current_audio = threading.Thread(
                target=self._play_pyaudio,
                args=(file_path,),
                daemon=True
            )
            self._current_audio.start()
            return True
        elif PYGAME_AVAILABLE:
            self._current_audio = threading.Thread(
                target=self._play_pygame,
                args=(file_path,),
                daemon=True
            )
            self._current_audio.start()
            return True
        else:
            logger.warning("No audio playback libraries available")
            self._is_playing = False
            return False

    def _play_pyaudio(self, file_path: str):
        try:
            if not self._pyaudio_instance:
                self._pyaudio_instance = pyaudio.PyAudio()

            wf = wave.open(file_path, 'rb')
            stream = self._pyaudio_instance.open(
                format=self._pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            while data and not self._stop_flag.is_set():
                stream.write(data)
                data = wf.readframes(chunk_size)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error("Pyaudio playback error: %s", e)
        finally:
            self._is_playing = False

    def _play_pygame(self, file_path: str):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop_flag.is_set():
                time.sleep(0.1)
            pygame.mixer.music.stop()
        except Exception as e:
            logger.error("Pygame playback error: %s", e)
        finally:
            self._is_playing = False

    def stop(self):
        self._stop_flag.set()
        if self._is_playing and self._current_audio:
            self._current_audio.join(timeout=2.0)
        self._is_playing = False

    def cleanup(self):
        if self._pyaudio_instance:
            self._pyaudio_instance.terminate()
