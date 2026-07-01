
import threading
import wave
import time
import struct
import logging
import numpy as np
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
        self._pause_event = threading.Event()  # set = running, clear = paused
        self._pause_event.set()
        self._is_playing = False
        self._is_paused = False
        self._pyaudio_instance = None
        self._pyaudio_stream = None
        self._volume = 1.0       # 0.0 - 1.0
        self._speed = 1.0        # playback speed multiplier
        self._total_frames = 0
        self._frames_played = 0

    def is_playing(self) -> bool:
        return self._is_playing

    def is_paused(self) -> bool:
        return self._is_paused

    def set_volume(self, volume: float):
        """Set playback volume (0.0 - 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def set_speed(self, speed: float):
        """Set playback speed multiplier (0.5 - 2.0)."""
        self._speed = max(0.5, min(2.0, speed))

    def get_progress(self) -> float:
        """Return playback progress as 0.0 - 1.0."""
        if self._total_frames <= 0:
            return 0.0
        return min(1.0, self._frames_played / self._total_frames)

    def play_wav(self, file_path: str) -> bool:
        if self.is_playing():
            self.stop()

        self._stop_flag.clear()
        self._pause_event.set()
        self._is_playing = True
        self._is_paused = False
        self._frames_played = 0
        self._total_frames = 0

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

    def _apply_volume(self, data: bytes, sampwidth: int) -> bytes:
        """Apply volume scaling to audio data."""
        if self._volume >= 1.0:
            return data
        if sampwidth == 2:
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            samples *= self._volume
            return (samples.astype(np.int16)).tobytes()
        elif sampwidth == 1:
            samples = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
            samples = (samples - 128) * self._volume + 128
            return samples.astype(np.uint8).tobytes()
        return data

    def _play_pyaudio(self, file_path: str):
        try:
            if not self._pyaudio_instance:
                self._pyaudio_instance = pyaudio.PyAudio()

            wf = wave.open(file_path, 'rb')
            total_frames = wf.getnframes()
            self._total_frames = total_frames
            sample_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()

            stream = self._pyaudio_instance.open(
                format=self._pyaudio_instance.get_format_from_width(sampwidth),
                channels=wf.getnchannels(),
                rate=int(sample_rate * self._speed),
                output=True
            )
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            while data and not self._stop_flag.is_set():
                # Handle pause
                if not self._pause_event.is_set():
                    self._is_paused = True
                    self._pause_event.wait(timeout=0.2)
                    continue
                self._is_paused = False

                # Apply volume
                data = self._apply_volume(data, sampwidth)

                stream.write(data)
                self._frames_played += chunk_size
                data = wf.readframes(chunk_size)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.error("Pyaudio playback error: %s", e)
        finally:
            self._is_playing = False
            self._is_paused = False

    def _play_pygame(self, file_path: str):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self._stop_flag.is_set():
                # Handle pause
                if not self._pause_event.is_set():
                    pygame.mixer.music.pause()
                    self._is_paused = True
                    self._pause_event.wait(timeout=0.2)
                    continue
                if self._is_paused:
                    pygame.mixer.music.unpause()
                    self._is_paused = False
                pygame.mixer.music.set_volume(self._volume)
                time.sleep(0.1)
            pygame.mixer.music.stop()
        except Exception as e:
            logger.error("Pygame playback error: %s", e)
        finally:
            self._is_playing = False
            self._is_paused = False

    def pause(self):
        """Pause playback."""
        if self._is_playing and not self._is_paused:
            self._pause_event.clear()

    def resume(self):
        """Resume paused playback."""
        if self._is_playing and self._is_paused:
            self._pause_event.set()

    def fade_out(self, duration_ms: int = 300):
        """Gradually reduce volume then stop."""
        if not self._is_playing:
            return
        steps = max(1, duration_ms // 50)
        original_vol = self._volume
        for i in range(steps):
            self._volume = original_vol * (1.0 - (i + 1) / steps)
            time.sleep(0.05)
        self.stop()
        self._volume = original_vol  # restore for next playback

    def stop(self):
        self._stop_flag.set()
        self._pause_event.set()  # unblock if paused
        if self._is_playing and self._current_audio:
            self._current_audio.join(timeout=2.0)
        self._is_playing = False
        self._is_paused = False

    def cleanup(self):
        if self._pyaudio_instance:
            self._pyaudio_instance.terminate()
