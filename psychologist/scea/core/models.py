from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class EmotionType(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    CURIOSITY = "curiosity"
    ANXIETY = "anxiety"
    PRIDE = "pride"
    SHAME = "shame"
    GRATITUDE = "gratitude"
    EMPATHY = "empathy"
    HOPE = "hope"
    DOUBT = "doubt"
    LOVE = "love"


@dataclass
class NeurochemicalState:
    dopamine: float = 0.5
    serotonin: float = 0.5
    oxytocin: float = 0.5
    cortisol: float = 0.3
    adrenaline: float = 0.2


@dataclass
class EmotionVector:
    emotions: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    intensity: float = 0.0
    valence: float = 0.0

    def __post_init__(self):
        for emotion in EmotionType:
            if emotion.value not in self.emotions:
                self.emotions[emotion.value] = 0.0
        self._update_intensity_valence()

    def _update_intensity_valence(self):
        total = sum(abs(v) for v in self.emotions.values())
        self.intensity = min(1.0, total / len(self.emotions))
        positive = sum(self.emotions[e] for e in ["joy", "trust", "anticipation", "curiosity", "pride", "gratitude", "empathy", "hope", "love"])
        negative = sum(self.emotions[e] for e in ["sadness", "anger", "fear", "disgust", "anxiety", "shame", "doubt"])
        self.valence = (positive - negative) / max(0.0001, positive + negative) if (positive + negative) > 0 else 0.0

    def get_dominant_emotion(self) -> Optional[str]:
        return max(self.emotions.items(), key=lambda x: abs(x[1]))[0] if self.emotions else None


@dataclass
class Need:
    name: str
    satisfaction: float = 0.5
    priority: float = 0.5
    deprivation: float = 0.0
    history: List[float] = field(default_factory=list)
    description: str = ""


@dataclass
class Belief:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject: str = ""
    predicate: str = ""
    object: Any = None
    confidence: float = 0.5
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    evidence: List[str] = field(default_factory=list)


@dataclass
class Goal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: float = 0.5
    progress: float = 0.0
    deadline: Optional[datetime] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    subgoals: List[str] = field(default_factory=list)


@dataclass
class Memory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    emotional_state: EmotionVector = field(default_factory=EmotionVector)
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    entity_id: str
    trust: float = 0.5
    familiarity: float = 0.0
    attachment: float = 0.0
    respect: float = 0.5
    reliability: float = 0.5
    interaction_history: List[Dict] = field(default_factory=list)
    emotional_associations: Dict[str, float] = field(default_factory=dict)


@dataclass
class Value:
    name: str
    importance: float = 0.5
    consistency: float = 0.8
    history: List[float] = field(default_factory=list)


@dataclass
class Identity:
    self_image: Dict[str, float] = field(default_factory=dict)
    self_confidence: float = 0.5
    values: List[Value] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    consistency_score: float = 0.8


@dataclass
class DecisionRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    emotional_state: EmotionVector = field(default_factory=EmotionVector)
    outcome: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    evaluation_score: Optional[float] = None


@dataclass
class SCEAState:
    step: int = 0
    time: datetime = field(default_factory=datetime.now)
    neurochemistry: NeurochemicalState = field(default_factory=NeurochemicalState)
    emotions: EmotionVector = field(default_factory=EmotionVector)
    needs: Dict[str, Need] = field(default_factory=dict)
    beliefs: List[Belief] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    memories: List[Memory] = field(default_factory=list)
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    identity: Identity = field(default_factory=Identity)
    cognitive_dissonance: float = 0.0
    attention_focus: Optional[str] = None
    active_thoughts: List[str] = field(default_factory=list)
    decision_history: List[DecisionRecord] = field(default_factory=list)
