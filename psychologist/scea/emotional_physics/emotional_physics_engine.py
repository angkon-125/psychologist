from scea.core.models import EmotionVector
from typing import Dict, List
import random
import math


class EmotionalPhysicsEngine:
    def __init__(self):
        self.momentum: Dict[str, float] = {}
        self.emotion_history: List[EmotionVector] = []

    def update(
        self,
        current_emotions: EmotionVector,
        triggers: Dict,
        neuro_effects: Dict,
        relationship_context: Dict = None
    ) -> EmotionVector:
        new_emotions = EmotionVector()
        new_emotions.emotions = current_emotions.emotions.copy()
        
        for trigger, details in triggers.items():
            self._apply_trigger(new_emotions, trigger, details)
        
        self._apply_momentum(new_emotions)
        self._apply_decay(new_emotions)
        self._apply_neuro_modulation(new_emotions, neuro_effects)
        
        if relationship_context:
            self._apply_contagion(new_emotions, relationship_context)
        
        self._apply_resonance(new_emotions)
        self._update_momentum(current_emotions, new_emotions)
        
        new_emotions._update_intensity_valence()
        
        self.emotion_history.append(new_emotions)
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]
        
        return new_emotions

    def _apply_trigger(self, emotions: EmotionVector, trigger: str, details: Dict):
        emotion_mappings = {
            'positive_event': {'joy': 0.3, 'trust': 0.15, 'anticipation': 0.1},
            'negative_event': {'sadness': 0.25, 'fear': 0.15, 'anger': 0.1},
            'achievement': {'joy': 0.4, 'pride': 0.3, 'trust': 0.1},
            'failure': {'sadness': 0.3, 'shame': 0.2, 'doubt': 0.15},
            'threat': {'fear': 0.4, 'anxiety': 0.3, 'anger': 0.1},
            'novelty': {'curiosity': 0.35, 'surprise': 0.25, 'anticipation': 0.15},
            'social_connection': {'trust': 0.35, 'love': 0.2, 'gratitude': 0.15},
            'loss': {'sadness': 0.4, 'fear': 0.2, 'disgust': 0.1},
            'recognition': {'pride': 0.35, 'joy': 0.25, 'trust': 0.1}
        }
        
        if trigger in emotion_mappings:
            intensity = details.get('intensity', 1.0)
            for emotion, amount in emotion_mappings[trigger].items():
                if emotion in emotions.emotions:
                    emotions.emotions[emotion] = max(-1.0, min(1.0,
                        emotions.emotions[emotion] + amount * intensity
                    ))

    def _apply_momentum(self, emotions: EmotionVector):
        for emotion, momentum in self.momentum.items():
            if emotion in emotions.emotions:
                emotions.emotions[emotion] += momentum * 0.3
                emotions.emotions[emotion] = max(-1.0, min(1.0, emotions.emotions[emotion]))

    def _apply_decay(self, emotions: EmotionVector):
        decay_factor = 0.92
        for emotion in emotions.emotions:
            emotions.emotions[emotion] *= decay_factor
            if abs(emotions.emotions[emotion]) < 0.01:
                emotions.emotions[emotion] = 0.0

    def _apply_neuro_modulation(self, emotions: EmotionVector, neuro_effects: Dict):
        if 'reward_expectation' in neuro_effects:
            boost = neuro_effects['reward_expectation'] * 0.15
            for e in ['joy', 'anticipation', 'curiosity']:
                emotions.emotions[e] = max(-1.0, min(1.0, emotions.emotions[e] + boost))
        
        if 'stress_level' in neuro_effects:
            stress = neuro_effects['stress_level'] * 0.2
            for e in ['anxiety', 'fear', 'anger']:
                emotions.emotions[e] = max(-1.0, min(1.0, emotions.emotions[e] + stress))
        
        if 'trust_formation' in neuro_effects:
            trust_boost = neuro_effects['trust_formation'] * 0.15
            for e in ['trust', 'love', 'gratitude']:
                emotions.emotions[e] = max(-1.0, min(1.0, emotions.emotions[e] + trust_boost))

    def _apply_contagion(self, emotions: EmotionVector, relationship_context: Dict):
        if 'other_emotions' in relationship_context:
            contagion_strength = 0.2
            for other_emotion, value in relationship_context['other_emotions'].items():
                if other_emotion in emotions.emotions:
                    emotions.emotions[other_emotion] = max(-1.0, min(1.0,
                        emotions.emotions[other_emotion] + value * contagion_strength
                    ))

    def _apply_resonance(self, emotions: EmotionVector):
        resonance_pairs = [
            ('joy', 'trust'),
            ('sadness', 'fear'),
            ('anger', 'disgust'),
            ('curiosity', 'anticipation'),
            ('anxiety', 'doubt'),
            ('pride', 'joy')
        ]
        
        for e1, e2 in resonance_pairs:
            if abs(emotions.emotions[e1]) > 0.3:
                boost = emotions.emotions[e1] * 0.2
                emotions.emotions[e2] = max(-1.0, min(1.0, emotions.emotions[e2] + boost))

    def _update_momentum(self, previous: EmotionVector, current: EmotionVector):
        for emotion in current.emotions:
            if emotion in previous.emotions:
                change = current.emotions[emotion] - previous.emotions[emotion]
                if emotion not in self.momentum:
                    self.momentum[emotion] = 0.0
                self.momentum[emotion] = self.momentum[emotion] * 0.8 + change * 0.2
        
        for emotion in self.momentum:
            self.momentum[emotion] *= 0.9
