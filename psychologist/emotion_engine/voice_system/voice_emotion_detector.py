
from typing import Dict
from .models import VoiceEmotionFeatures, VoiceEmotionResult


class VoiceEmotionDetector:
    @staticmethod
    def detect_emotion(features: VoiceEmotionFeatures) -> VoiceEmotionResult:
        result = VoiceEmotionResult()
        result.feature_source = features
        emotions = {}

        # Rule-based emotion scoring
        pitch_mean = features.pitch_mean
        pitch_var = features.pitch_variance
        energy = features.energy_mean
        intensity = features.intensity_score

        # Happy: high pitch mean, high variance, high energy
        happy_score = min(1.0, (pitch_mean / 300.0) * 0.4 + (pitch_var / 10000.0) * 0.3 + (energy * 2) * 0.3)

        # Sad: low pitch mean, low variance, low energy
        sad_score = min(1.0, (300 - pitch_mean) / 300 * 0.35 + (10000 - pitch_var) / 10000 * 0.35 + (1 - energy) * 0.3)

        # Angry: high pitch mean, high pitch variance, high energy
        angry_score = min(1.0, (pitch_mean / 350) * 0.4 + (pitch_var / 12000) * 0.3 + (energy * 2.5) * 0.3)

        # Fearful: high pitch, high variance, variable energy
        fearful_score = min(1.0, (pitch_mean / 320) * 0.35 + (pitch_var / 11000) * 0.35 + (energy * 2) * 0.3)

        # Calm: low pitch, low variance, moderate energy
        calm_score = min(1.0, (350 - pitch_mean)/350 * 0.3 + (12000 - pitch_var)/12000 *0.4 + 0.3)

        emotions = {
            "happy": happy_score,
            "sad": sad_score,
            "angry": angry_score,
            "fearful": fearful_score,
            "calm": calm_score
        }

        # Normalize
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v / total for k, v in emotions.items()}
            result.dominant_emotion = max(emotions, key=emotions.get)
            result.confidence = emotions[result.dominant_emotion]

        result.emotion_probabilities = emotions

        return result

