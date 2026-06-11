from ..models import PersonalityTraits
import random
from typing import Dict


class PersonalityEngine:
    def __init__(self, traits: PersonalityTraits = None):
        self.traits = traits if traits else PersonalityTraits()

    def randomize_traits(self):
        trait_names = [
            'openness', 'conscientiousness', 'extraversion',
            'agreeableness', 'neuroticism', 'patience', 'compassion',
            'confidence', 'assertiveness', 'curiosity', 'optimism',
            'skepticism', 'creativity'
        ]
        for trait in trait_names:
            setattr(self.traits, trait, random.uniform(0.0, 1.0))

    def get_traits(self) -> Dict[str, float]:
        return self.traits.to_dict()

    def influence_emotion(self, emotion_type: str, base_value: float) -> float:
        influence_factors = {
            'happiness': self.traits.optimism,
            'sadness': self.traits.neuroticism,
            'anger': self.traits.neuroticism * (1 - self.traits.patience),
            'fear': self.traits.neuroticism * (1 - self.traits.confidence),
            'anxiety': self.traits.neuroticism * 0.7 + (1 - self.traits.confidence) * 0.3,
            'confidence': self.traits.confidence,
            'curiosity': self.traits.curiosity * self.traits.openness,
            'stress': self.traits.neuroticism * (1 - self.traits.patience),
            'trust': self.traits.agreeableness,
            'empathy': self.traits.compassion * self.traits.agreeableness
        }
        
        factor = influence_factors.get(emotion_type, 0.5)
        return base_value * (0.5 + factor * 0.5)

    def influence_emotional_state(self, emotional_state):
        from ..models import EmotionalState
        new_state = EmotionalState()
        
        for emotion, value in emotional_state.primary_emotions.items():
            new_state.primary_emotions[emotion] = self.influence_emotion(emotion, value)
        
        for emotion, value in emotional_state.secondary_emotions.items():
            new_state.secondary_emotions[emotion] = self.influence_emotion(emotion, value)
        
        for emotion, value in emotional_state.advanced_emotions.items():
            new_state.advanced_emotions[emotion] = self.influence_emotion(emotion, value)
        
        new_state.intensity = emotional_state.intensity
        return new_state

    def get_personality_summary(self) -> str:
        traits = self.traits.to_dict()
        high_traits = [k for k, v in traits.items() if v > 0.7]
        low_traits = [k for k, v in traits.items() if v < 0.3]
        
        summary_parts = []
        if high_traits:
            summary_parts.append(f"High in: {', '.join(high_traits)}")
        if low_traits:
            summary_parts.append(f"Low in: {', '.join(low_traits)}")
        
        return "; ".join(summary_parts) if summary_parts else "Balanced personality"
