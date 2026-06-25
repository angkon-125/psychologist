
import numpy as np
import scipy.signal as signal
from typing import Optional, Tuple


class AudioPreprocessor:
    @staticmethod
    def normalize_audio(audio: np.ndarray, target_peak: float = 0.9) -> np.ndarray:
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio * (target_peak / peak)
        return audio

    @staticmethod
    def reduce_noise(audio: np.ndarray, sample_rate: int, noise_reduction: float = 0.5) -> np.ndarray:
        # Simple spectral subtraction-like noise reduction
        # Estimate noise from first 0.1 seconds (or less if shorter)
        noise_samples = min(int(sample_rate * 0.1), len(audio))
        if noise_samples > 0:
            noise_segment = audio[:noise_samples]
            noise_power = np.mean(noise_segment**2)
            noise_reduction_factor = 1 - noise_reduction
            # Subtract noise
            audio_power = audio**2
            cleaned_power = np.maximum(audio_power - noise_power * noise_reduction, 0)
            cleaned_audio = np.sign(audio) * np.sqrt(cleaned_power)
            return cleaned_audio
        return audio

    @staticmethod
    def apply_highpass_filter(audio: np.ndarray, sample_rate: int, cutoff: float = 80) -> np.ndarray:
        b, a = signal.butter(3, cutoff / (sample_rate / 2), btype='highpass')
        return signal.filtfilt(b, a, audio)

    @staticmethod
    def trim_silence(audio: np.ndarray, sample_rate: int, threshold: float = 0.02,
                     pre_pad: int = 1000, post_pad: int = 1000) -> np.ndarray:
        # Find non-silent regions
        energy = np.abs(audio)
        non_silent = np.where(energy > threshold)[0]
        if len(non_silent) == 0:
            return audio

        start = max(0, non_silent[0] - pre_pad)
        end = min(len(audio), non_silent[-1] + post_pad)
        return audio[start:end]

    @staticmethod
    def resample_audio(audio: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        if original_rate == target_rate:
            return audio
        num_samples = int(len(audio) * target_rate / original_rate)
        return signal.resample(audio, num_samples)

    @staticmethod
    def preprocess_full(audio: np.ndarray, sample_rate: int) -> np.ndarray:
        # Full preprocessing pipeline
        processed = audio.copy()
        processed = AudioPreprocessor.apply_highpass_filter(processed, sample_rate)
        processed = AudioPreprocessor.normalize_audio(processed)
        processed = AudioPreprocessor.reduce_noise(processed, sample_rate)
        processed = AudioPreprocessor.trim_silence(processed, sample_rate)
        return processed

