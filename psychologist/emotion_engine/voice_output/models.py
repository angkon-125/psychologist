
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class TTSRequest:
    text: str
    language: str = "en"
    engine_name: Optional[str] = None
    voice_id: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 0.9
    emotion_style: Optional[str] = None
    save_to_file: bool = False
    output_format: str = "wav"


@dataclass
class TTSResult:
    success: bool = False
    engine_name: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "engine_name": self.engine_name,
            "audio_path": self.audio_path,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class VoiceStyle:
    emotion_name: str
    speed_multiplier: float = 1.0
    pitch_multiplier: float = 1.0
    volume_multiplier: float = 0.9
    pause_multiplier: float = 1.0
