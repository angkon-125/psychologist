"""
Agent Schemas — Standard Data Structures

All agents communicate using these shared schemas.
Every agent response follows the same structure so the Orchestrator
can uniformly process, validate, and combine outputs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class AgentRequest:
    """Standard request passed to any agent."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    session_id: str = ""
    language: str = "en"
    input_mode: str = "text"  # "text" | "voice"
    user_mood: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "text": self.text,
            "session_id": self.session_id,
            "language": self.language,
            "input_mode": self.input_mode,
            "user_mood": self.user_mood,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentResponse:
    """
    Standard response returned by every agent.

    This is the unified schema specified by the ZARA architecture.
    The Orchestrator combines multiple AgentResponses into a final response.
    """

    success: bool = True
    agent: str = ""
    intent: str = ""
    response: str = ""
    confidence: float = 0.0
    risk_level: str = "low"  # "low" | "medium" | "high"
    requires_confirmation: bool = False
    memory_updates: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "agent": self.agent,
            "intent": self.intent,
            "response": self.response,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "requires_confirmation": self.requires_confirmation,
            "memory_updates": self.memory_updates,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @classmethod
    def error(cls, agent: str, message: str, intent: str = "") -> "AgentResponse":
        """Create an error response."""
        return cls(
            success=False,
            agent=agent,
            intent=intent,
            response=message,
            confidence=0.0,
            risk_level="low",
            errors=[message],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """Reconstruct from dict."""
        return cls(
            success=data.get("success", True),
            agent=data.get("agent", ""),
            intent=data.get("intent", ""),
            response=data.get("response", ""),
            confidence=data.get("confidence", 0.0),
            risk_level=data.get("risk_level", "low"),
            requires_confirmation=data.get("requires_confirmation", False),
            memory_updates=data.get("memory_updates", []),
            tool_calls=data.get("tool_calls", []),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryUpdate:
    """A single memory update to be persisted by the Memory Agent."""

    memory_type: str = "short_term"  # "short_term" | "long_term" | "emotional" | "preference"
    key: str = ""
    value: Any = None
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_type": self.memory_type,
            "key": self.key,
            "value": self.value,
            "importance": self.importance,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolCall:
    """A tool execution request."""

    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    requires_permission: bool = False
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "risk_level": self.risk_level,
            "requires_permission": self.requires_permission,
            "timeout": self.timeout,
        }


@dataclass
class PredictionResult:
    """Structured prediction output."""

    prediction: str = ""
    reason: str = ""
    confidence: float = 0.0
    risk_level: str = "low"
    missing_information: List[str] = field(default_factory=list)
    recommended_preparation: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": self.prediction,
            "reason": self.reason,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "missing_information": self.missing_information,
            "recommended_preparation": self.recommended_preparation,
        }
