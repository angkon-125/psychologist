"""
Executive Brain Schemas

Data structures for the cognitive core:
- ExecutionPlan: what the executive intends to do
- ConfidenceReport: fused confidence from all sources
- ReflectionResult: post-response self-check
- GoalState: long-running goal tracking
- DecisionRecord: debug-only decision audit trail
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class ExecutionPlan:
    """
    Internal execution plan generated before responding.

    Describes what agents, tools, and memory are needed,
    plus an estimated confidence and risk assessment.
    """

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    required_agents: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    needs_memory: bool = False
    needs_clarification: bool = False
    estimated_confidence: float = 0.0
    risk_assessment: str = "low"  # "low" | "medium" | "high"
    steps: List[str] = field(default_factory=list)
    is_multi_agent: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "required_agents": self.required_agents,
            "required_tools": self.required_tools,
            "needs_memory": self.needs_memory,
            "needs_clarification": self.needs_clarification,
            "estimated_confidence": self.estimated_confidence,
            "risk_assessment": self.risk_assessment,
            "steps": self.steps,
            "is_multi_agent": self.is_multi_agent,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConfidenceReport:
    """
    Fused confidence report from all cognitive sources.

    recommendation is one of:
      - "respond": confidence > 0.90, respond normally
      - "respond_uncertain": 0.70-0.90, respond with minor uncertainty
      - "clarify": 0.40-0.70, ask one clarification question
      - "explain_missing": < 0.40, explain what information is missing
    """

    overall_confidence: float = 0.0
    agent_confidences: Dict[str, float] = field(default_factory=dict)
    missing_information: List[str] = field(default_factory=list)
    recommendation: str = "respond"  # "respond" | "respond_uncertain" | "clarify" | "explain_missing"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_confidence": self.overall_confidence,
            "agent_confidences": self.agent_confidences,
            "missing_information": self.missing_information,
            "recommendation": self.recommendation,
        }


@dataclass
class ReflectionResult:
    """
    Post-response self-check result.

    issue_type is one of:
      - "none": no issues found
      - "misunderstood": response didn't address the request
      - "ignored_memory": memory context was available but not used
      - "forgot_tool": a tool was needed but not invoked
      - "contradiction": response contradicts earlier turns
      - "safety_violation": response may violate safety boundaries
    """

    issues_found: List[str] = field(default_factory=list)
    should_regenerate: bool = False
    issue_type: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issues_found": self.issues_found,
            "should_regenerate": self.should_regenerate,
            "issue_type": self.issue_type,
        }


@dataclass
class GoalState:
    """
    Tracks a long-running goal across conversations.

    status: "active" | "completed" | "paused" | "interrupted"
    """

    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    completion_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "completion_pct": self.completion_pct,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalState":
        return cls(
            goal_id=data.get("goal_id", str(uuid.uuid4())),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            completed_tasks=data.get("completed_tasks", []),
            pending_tasks=data.get("pending_tasks", []),
            completion_pct=data.get("completion_pct", 0.0),
        )


@dataclass
class DecisionRecord:
    """
    Debug-only audit record for every executive decision.

    Never exposed in production responses unless Debug Mode is enabled.
    """

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    intent: str = ""
    selected_agents: List[str] = field(default_factory=list)
    selected_tools: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reflection_result: str = "none"
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    fallbacks: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "intent": self.intent,
            "selected_agents": self.selected_agents,
            "selected_tools": self.selected_tools,
            "confidence": self.confidence,
            "reflection_result": self.reflection_result,
            "duration_ms": self.duration_ms,
            "errors": self.errors,
            "fallbacks": self.fallbacks,
            "timestamp": self.timestamp.isoformat(),
        }
