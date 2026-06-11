from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class PrimaryEmotion(Enum):
    HAPPINESS = "happiness"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"


class SecondaryEmotion(Enum):
    EXCITEMENT = "excitement"
    ANXIETY = "anxiety"
    FRUSTRATION = "frustration"
    CURIOSITY = "curiosity"
    HOPE = "hope"
    CONFIDENCE = "confidence"
    EMBARRASSMENT = "embarrassment"
    PRIDE = "pride"
    JEALOUSY = "jealousy"
    GRATITUDE = "gratitude"
    SYMPATHY = "sympathy"
    EMPATHY = "empathy"


class AdvancedEmotion(Enum):
    BURNOUT = "burnout"
    MOTIVATION = "motivation"
    STRESS = "stress"
    LONELINESS = "loneliness"
    TRUST = "trust"
    DISTRUST = "distrust"
    ATTACHMENT = "attachment"
    NOSTALGIA = "nostalgia"
    EMOTIONAL_FATIGUE = "emotional_fatigue"
    EMOTIONAL_RECOVERY = "emotional_recovery"


@dataclass
class EmotionalState:
    timestamp: datetime = field(default_factory=datetime.now)
    primary_emotions: Dict[str, float] = field(default_factory=dict)
    secondary_emotions: Dict[str, float] = field(default_factory=dict)
    advanced_emotions: Dict[str, float] = field(default_factory=dict)
    intensity: float = 0.0

    def __post_init__(self):
        for emotion in PrimaryEmotion:
            if emotion.value not in self.primary_emotions:
                self.primary_emotions[emotion.value] = 0.0
        for emotion in SecondaryEmotion:
            if emotion.value not in self.secondary_emotions:
                self.secondary_emotions[emotion.value] = 0.0
        for emotion in AdvancedEmotion:
            if emotion.value not in self.advanced_emotions:
                self.advanced_emotions[emotion.value] = 0.0

    def get_dominant_emotion(self) -> Optional[str]:
        all_emotions = {**self.primary_emotions, **self.secondary_emotions, **self.advanced_emotions}
        if not all_emotions:
            return None
        return max(all_emotions.items(), key=lambda x: x[1])[0]

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'primary_emotions': self.primary_emotions,
            'secondary_emotions': self.secondary_emotions,
            'advanced_emotions': self.advanced_emotions,
            'intensity': self.intensity
        }


@dataclass
class PersonalityTraits:
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5
    patience: float = 0.5
    compassion: float = 0.5
    confidence: float = 0.5
    assertiveness: float = 0.5
    curiosity: float = 0.5
    optimism: float = 0.5
    skepticism: float = 0.5
    creativity: float = 0.5

    def to_dict(self) -> Dict:
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism,
            'patience': self.patience,
            'compassion': self.compassion,
            'confidence': self.confidence,
            'assertiveness': self.assertiveness,
            'curiosity': self.curiosity,
            'optimism': self.optimism,
            'skepticism': self.skepticism,
            'creativity': self.creativity
        }


@dataclass
class MemoryEntry:
    timestamp: datetime = field(default_factory=datetime.now)
    interaction: str = ""
    emotional_state: EmotionalState = field(default_factory=EmotionalState)
    context: Dict = field(default_factory=dict)
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'interaction': self.interaction,
            'emotional_state': self.emotional_state.to_dict(),
            'context': self.context,
            'importance': self.importance,
            'tags': self.tags
        }


@dataclass
class ConversationContext:
    topic: Optional[str] = None
    sentiment: float = 0.0
    emotional_trend: List[float] = field(default_factory=list)
    intensity_trend: List[float] = field(default_factory=list)
    repeated_patterns: List[str] = field(default_factory=list)
    conflict_level: float = 0.0
    motivation_opportunity: float = 0.0
    current_topic_keywords: List[str] = field(default_factory=list)
