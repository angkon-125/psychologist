
import numpy as np
import librosa
import logging
from typing import Dict, List
from .models import VoiceEmotionFeatures

logger = logging.getLogger("zara.voice.features")


class VoiceFeatureExtractor:
    @staticmethod
    def extract_features(audio: np.ndarray, sample_rate: int) -> VoiceEmotionFeatures:
        features = VoiceEmotionFeatures()

        # Normalize audio
        audio = audio / np.max(np.abs(audio)) if np.max(np.abs(audio)) > 0 else audio

        # Pitch (using librosa)
        try:
            # Use librosa's piptrack for pitch
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sample_rate)
            pitch_values = []
            for i in range(pitches.shape[1]):
                idx = magnitudes[:, i].argmax()
                if magnitudes[idx, i] > 0.1:
                    pitch_values.append(pitches[idx, i])
            if pitch_values:
                features.pitch_mean = np.mean(pitch_values)
                features.pitch_variance = np.var(pitch_values)
        except Exception as e:
            logger.warning("Pitch extraction error: %s", e)

        # Energy
        energy = np.sum(audio**2) / len(audio)
        features.energy_mean = energy

        # Spectral centroid
        try:
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
            features.spectral_centroid = np.mean(spectral_centroids)
        except Exception as e:
            logger.warning("Spectral centroid error: %s", e)

        # MFCC summary
        try:
            mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
            features.mfcc_summary = list(np.mean(mfccs, axis=1))
        except Exception as e:
            logger.warning("MFCC error: %s", e)

        # Intensity score
        rms = librosa.feature.rms(y=audio)[0]
        features.intensity_score = np.mean(rms)

        # Simple speaking rate and silence estimates (simplified)
        features.speaking_rate = 1.0
        features.silence_ratio = 0.2

        return features

