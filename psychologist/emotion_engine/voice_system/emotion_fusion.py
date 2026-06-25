
from typing import Dict
from .models import MultimodalEmotionState
from .audio_config import AudioConfig


class EmotionFusion:
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()

    def fuse_emotions(self, text_emotion: Dict[str, float],
                      voice_emotion: Dict[str, float],
                      memory_emotion: Dict[str, float] = None) -> MultimodalEmotionState:
        memory_emotion = memory_emotion or {}
        text_weight = self.config.get("voice_emotion.text_weight", 0.55)
        voice_weight = self.config.get("voice_emotion.voice_weight", 0.35)
        memory_weight = self.config.get("voice_emotion.memory_weight", 0.10)

        # Collect all unique emotion keys
        all_emotions = set(list(text_emotion.keys()) + list(voice_emotion.keys()) + list(memory_emotion.keys()))
        fused_scores = {}

        for emotion in all_emotions:
            t = text_emotion.get(emotion, 0.0)
            v = voice_emotion.get(emotion, 0.0)
            m = memory_emotion.get(emotion, 0.0)
            fused_scores[emotion] = t * text_weight + v * voice_weight + m * memory_weight

        # Normalize
        total = sum(fused_scores.values())
        if total > 0:
            fused_scores = {k: v / total for k, v in fused_scores.items()}
        else:
            # If no scores, set neutral
            fused_scores = {"neutral": 1.0}

        # Find dominant
        dominant = max(fused_scores, key=fused_scores.get)

        return MultimodalEmotionState(
            text_emotion=text_emotion,
            voice_emotion=voice_emotion,
            memory_emotion=memory_emotion,
            fused_emotion=fused_scores,
            confidence=fused_scores[dominant],
            explanation_summary=f"Emotion fused with text weight {text_weight}, voice weight {voice_weight}"
        )

