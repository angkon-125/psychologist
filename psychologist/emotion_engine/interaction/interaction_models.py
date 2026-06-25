"""
Interaction Data Models

All data structures used by the interaction layer:
text mode, voice mode, hybrid mode, sessions, safety, and support tools.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid


# ── Enums ────────────────────────────────────────────────────────────

class InteractionMode(Enum):
    """Supported interaction modes."""
    TEXT = "text"
    VOICE = "voice"
    HYBRID = "hybrid"


class InputType(Enum):
    """How the user submitted the message."""
    TEXT = "text"
    VOICE = "voice"


class ResponseType(Enum):
    """Category of assistant response."""
    SUPPORTIVE = "supportive"
    CALMING = "calming"
    REASSURING = "reassuring"
    ENCOURAGING = "encouraging"
    STRESS_RELIEF = "stress_relief"
    RECOVERY = "recovery"
    CRISIS_SUPPORT = "crisis_support"
    GROUNDING = "grounding"
    BREATHING_EXERCISE = "breathing_exercise"
    JOURNALING_PROMPT = "journaling_prompt"
    REFLECTION = "reflection"
    MOOD_CHECKIN = "mood_checkin"
    SESSION_SUMMARY = "session_summary"
    NEUTRAL = "neutral"


class RiskLevel(Enum):
    """Safety risk levels."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SupportActionType(Enum):
    """Types of supportive actions the system can offer."""
    CALM_DOWN = "calm_down"
    BREATHING_EXERCISE = "breathing_exercise"
    JOURNALING_PROMPT = "journaling_prompt"
    REFLECTION_QUESTIONS = "reflection_questions"
    MOOD_CHECKIN = "mood_checkin"
    SESSION_SUMMARY = "session_summary"
    GROUNDING_EXERCISE = "grounding_exercise"
    PROFESSIONAL_HELP_REMINDER = "professional_help_reminder"


# ── Interaction Mode Config ──────────────────────────────────────────

@dataclass
class InteractionModeConfig:
    """Configuration for a specific interaction mode."""
    mode_name: str = "hybrid"
    voice_input_enabled: bool = True
    text_input_enabled: bool = True
    voice_output_enabled: bool = True
    auto_listen_after_response: bool = False

    def to_dict(self) -> Dict:
        return {
            "mode_name": self.mode_name,
            "voice_input_enabled": self.voice_input_enabled,
            "text_input_enabled": self.text_input_enabled,
            "voice_output_enabled": self.voice_output_enabled,
            "auto_listen_after_response": self.auto_listen_after_response,
        }


# ── User Message ─────────────────────────────────────────────────────

@dataclass
class UserMessage:
    """A single message from the user (text or voice transcript)."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    input_type: str = "text"          # "text" or "voice"
    raw_text: str = ""
    normalized_text: str = ""
    language: str = "en"
    timestamp: datetime = field(default_factory=datetime.now)
    detected_emotion: str = ""
    confidence: float = 0.0
    user_selected_mood: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "input_type": self.input_type,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "timestamp": self.timestamp.isoformat(),
            "detected_emotion": self.detected_emotion,
            "confidence": self.confidence,
            "user_selected_mood": self.user_selected_mood,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserMessage":
        msg = cls()
        msg.message_id = data.get("message_id", msg.message_id)
        msg.session_id = data.get("session_id", "")
        msg.input_type = data.get("input_type", "text")
        msg.raw_text = data.get("raw_text", "")
        msg.normalized_text = data.get("normalized_text", "")
        msg.language = data.get("language", "en")
        ts = data.get("timestamp")
        if ts:
            try:
                msg.timestamp = datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                pass
        msg.detected_emotion = data.get("detected_emotion", "")
        msg.confidence = data.get("confidence", 0.0)
        msg.user_selected_mood = data.get("user_selected_mood")
        return msg


# ── Assistant Message ────────────────────────────────────────────────

@dataclass
class AssistantMessage:
    """A response message from the system."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    response_text: str = ""
    response_language: str = "en"
    response_type: str = "supportive"
    spoken: bool = False
    audio_path: Optional[str] = None
    safety_level: str = "none"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "response_text": self.response_text,
            "response_language": self.response_language,
            "response_type": self.response_type,
            "spoken": self.spoken,
            "audio_path": self.audio_path,
            "safety_level": self.safety_level,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AssistantMessage":
        msg = cls()
        msg.message_id = data.get("message_id", msg.message_id)
        msg.session_id = data.get("session_id", "")
        msg.response_text = data.get("response_text", "")
        msg.response_language = data.get("response_language", "en")
        msg.response_type = data.get("response_type", "supportive")
        msg.spoken = data.get("spoken", False)
        msg.audio_path = data.get("audio_path")
        msg.safety_level = data.get("safety_level", "none")
        ts = data.get("timestamp")
        if ts:
            try:
                msg.timestamp = datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                pass
        return msg


# ── Session State ────────────────────────────────────────────────────

@dataclass
class SessionState:
    """Complete state of a user session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    active_mode: str = "hybrid"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    last_interaction_time: Optional[datetime] = None
    current_emotion_state: Dict = field(default_factory=dict)
    mood_timeline: List[Dict] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)
    user_messages: List[Dict] = field(default_factory=list)
    assistant_messages: List[Dict] = field(default_factory=list)
    detected_emotions: List[str] = field(default_factory=list)
    summary: str = ""
    follow_up_suggestions: List[str] = field(default_factory=list)
    user_preference_snapshot: Dict = field(default_factory=dict)
    language: str = "en"

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "active_mode": self.active_mode,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_interaction_time": self.last_interaction_time.isoformat() if self.last_interaction_time else None,
            "current_emotion_state": self.current_emotion_state,
            "mood_timeline": self.mood_timeline,
            "safety_flags": self.safety_flags,
            "user_messages": self.user_messages,
            "assistant_messages": self.assistant_messages,
            "detected_emotions": self.detected_emotions,
            "summary": self.summary,
            "follow_up_suggestions": self.follow_up_suggestions,
            "user_preference_snapshot": self.user_preference_snapshot,
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionState":
        s = cls()
        s.session_id = data.get("session_id", s.session_id)
        s.active_mode = data.get("active_mode", "hybrid")
        st = data.get("start_time")
        if st:
            try:
                s.start_time = datetime.fromisoformat(st)
            except (ValueError, TypeError):
                pass
        et = data.get("end_time")
        if et:
            try:
                s.end_time = datetime.fromisoformat(et)
            except (ValueError, TypeError):
                pass
        lit = data.get("last_interaction_time")
        if lit:
            try:
                s.last_interaction_time = datetime.fromisoformat(lit)
            except (ValueError, TypeError):
                pass
        s.current_emotion_state = data.get("current_emotion_state", {})
        s.mood_timeline = data.get("mood_timeline", [])
        s.safety_flags = data.get("safety_flags", [])
        s.user_messages = data.get("user_messages", [])
        s.assistant_messages = data.get("assistant_messages", [])
        s.detected_emotions = data.get("detected_emotions", [])
        s.summary = data.get("summary", "")
        s.follow_up_suggestions = data.get("follow_up_suggestions", [])
        s.user_preference_snapshot = data.get("user_preference_snapshot", {})
        s.language = data.get("language", "en")
        return s


# ── Support Action ───────────────────────────────────────────────────

@dataclass
class SupportAction:
    """A supportive action triggered by the system."""
    action_type: str = "calm_down"
    trigger_reason: str = ""
    script_key: str = ""
    language: str = "en"
    completed: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""

    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type,
            "trigger_reason": self.trigger_reason,
            "script_key": self.script_key,
            "language": self.language,
            "completed": self.completed,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
        }


# ── Safety Assessment ────────────────────────────────────────────────

@dataclass
class SafetyAssessment:
    """Result of safety analysis on user input."""
    risk_level: str = "none"
    detected_signals: List[str] = field(default_factory=list)
    recommended_response_type: str = "supportive"
    should_escalate: bool = False
    safe_response_template: str = ""

    def to_dict(self) -> Dict:
        return {
            "risk_level": self.risk_level,
            "detected_signals": self.detected_signals,
            "recommended_response_type": self.recommended_response_type,
            "should_escalate": self.should_escalate,
            "safe_response_template": self.safe_response_template,
        }
