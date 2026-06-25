
import numpy as np
import webrtcvad
from typing import Optional, List, Tuple


class VoiceActivityDetector:
    def __init__(self, mode: int = 3, sample_rate: int = 16000, frame_duration_ms: int = 30):
        self.vad = webrtcvad.Vad(mode)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)

    def is_speech(self, audio: np.ndarray) -> bool:
        # Convert to int16 for webrtcvad
        audio_int16 = (audio * 32767).astype(np.int16)
        # Pad/truncate to frame size
        if len(audio_int16) < self.frame_size:
            padding = np.zeros(self.frame_size - len(audio_int16), dtype=np.int16)
            audio_int16 = np.concatenate([audio_int16, padding])
        elif len(audio_int16) > self.frame_size:
            audio_int16 = audio_int16[:self.frame_size]
        try:
            return self.vad.is_speech(audio_int16.tobytes(), self.sample_rate)
        except Exception:
            return False

    def detect_speech_regions(self, audio: np.ndarray, sample_rate: int = None) -> List[Tuple[int, int]]:
        sr = sample_rate or self.sample_rate
        regions = []
        is_speech_flag = False
        start_idx = 0
        # Frame-wise processing
        step = self.frame_size
        for i in range(0, len(audio), step):
            frame = audio[i:i+step]
            if len(frame) < step:
                break
            current_is_speech = self.is_speech(frame)
            if current_is_speech and not is_speech_flag:
                start_idx = i
                is_speech_flag = True
            elif not current_is_speech and is_speech_flag:
                regions.append((start_idx, i))
                is_speech_flag = False
        if is_speech_flag:
            regions.append((start_idx, len(audio)))
        return regions

