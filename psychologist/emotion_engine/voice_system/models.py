
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum


@dataclass
class AudioInputConfig:
    device_id: Optional[int] = None
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 4096
    vad_enabled: bool = True
    silence_threshold: float = 0.02
    language: str = "en"


@dataclass
class SpeechRecognitionResult:
    raw_text: str = ""
    normalized_text: str = ""
    language: str = "en"
    confidence: float = 0.0
    partial: bool = False
    final: bool = True
    engine_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "confidence": self.confidence,
            "partial": self.partial,
            "final": self.final,
            "engine_name": self.engine_name,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class VoiceEmotionFeatures:
    pitch_mean: float = 0.0
    pitch_variance: float = 0.0
    energy_mean: float = 0.0
    speaking_rate: float = 0.0
    pause_count: int = 0
    silence_ratio: float = 0.0
    spectral_centroid: float = 0.0
    mfcc_summary: List[float] = field(default_factory=list)
    intensity_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "pitch_mean": self.pitch_mean,
            "pitch_variance": self.pitch_variance,
            "energy_mean": self.energy_mean,
            "speaking_rate": self.speaking_rate,
            "pause_count": self.pause_count,
            "silence_ratio": self.silence_ratio,
            "spectral_centroid": self.spectral_centroid,
            "mfcc_summary": self.mfcc_summary,
            "intensity_score": self.intensity_score,
        }


@dataclass
class VoiceEmotionResult:
    emotion_probabilities: Dict[str, float] = field(default_factory=dict)
    dominant_emotion: Optional[str] = None
    confidence: float = 0.0
    feature_source: VoiceEmotionFeatures = field(default_factory=VoiceEmotionFeatures)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "emotion_probabilities": self.emotion_probabilities,
            "dominant_emotion": self.dominant_emotion,
            "confidence": self.confidence,
            "feature_source": self.feature_source.to_dict(),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MultimodalEmotionState:
    text_emotion: Dict[str, float] = field(default_factory=dict)
    voice_emotion: Dict[str, float] = field(default_factory=dict)
    memory_emotion: Dict[str, float] = field(default_factory=dict)
    fused_emotion: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    explanation_summary: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "text_emotion": self.text_emotion,
            "voice_emotion": self.voice_emotion,
            "memory_emotion": self.memory_emotion,
            "fused_emotion": self.fused_emotion,
            "confidence": self.confidence,
            "explanation_summary": self.explanation_summary,
            "timestamp": self.timestamp.isoformat(),
        }

