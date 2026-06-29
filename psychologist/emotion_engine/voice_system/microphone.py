
import sounddevice as sd
import numpy as np
import threading
import queue
import logging
from typing import Optional, List, Callable, Dict
from .models import AudioInputConfig
from datetime import datetime

logger = logging.getLogger("zara.voice.microphone")


class Microphone:
    def __init__(self, config: Optional[AudioInputConfig] = None):
        self.config = config or AudioInputConfig()
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.current_level = 0.0
        self._level_callback: Optional[Callable[[float], None]] = None

    @staticmethod
    def list_devices() -> List[Dict]:
        devices = sd.query_devices()
        device_list = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                device_list.append({
                    "id": i,
                    "name": dev['name'],
                    "channels": dev['max_input_channels'],
                    "sample_rate": dev['default_samplerate']
                })
        return device_list

    def set_level_callback(self, callback: Optional[Callable[[float], None]]):
        self._level_callback = callback

    def start_recording(self, on_audio_chunk: Optional[Callable[[np.ndarray, int], None]] = None):
        if self.is_recording:
            return

        try:
            self.stream = sd.InputStream(
                device=self.config.device_id,
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                blocksize=self.config.chunk_size,
                dtype='float32',
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_recording = True
        except Exception as e:
            logger.error("Error starting microphone: %s", e)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.debug("Audio status: %s", status)
        # Compute audio level
        audio_np = indata.copy().flatten()
        level = np.sqrt(np.mean(audio_np**2))
        self.current_level = level
        if self._level_callback:
            self._level_callback(level)
        self.audio_queue.put(audio_np)

    def stop_recording(self):
        if not self.is_recording:
            return
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_recording = False
        self.current_level = 0.0

    def get_current_level(self) -> float:
        return self.current_level

    def get_audio_chunk(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

