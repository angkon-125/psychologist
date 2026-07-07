"""
Workspace Schemas — Cognitive Workspace

Data structures for the persistent cognitive workspace.
Projects, Tasks, Milestones, Progress Reports, and Summaries.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Project:
    """
    A workspace project.

    status: "active" | "paused" | "completed" | "archived"
    priority: "low" | "medium" | "high" | "critical"
    """

    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: str = "active"
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deadline": self.deadline,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            project_id=data.get("project_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            deadline=data.get("deadline"),
            tags=data.get("tags", []),
        )


@dataclass
class Task:
    """
    A workspace task within a project.

    status: "pending" | "in_progress" | "blocked" | "completed" | "cancelled"
    priority: "low" | "medium" | "high" | "critical"
    estimated_effort: "small" | "medium" | "large"
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    title: str = ""
    description: str = ""
    status: str = "pending"
    priority: str = "medium"
    depends_on: List[str] = field(default_factory=list)
    estimated_effort: str = "medium"
    assigned_agents: List[str] = field(default_factory=list)
    related_episode_ids: List[str] = field(default_factory=list)
    related_memory_keys: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "estimated_effort": self.estimated_effort,
            "assigned_agents": self.assigned_agents,
            "related_episode_ids": self.related_episode_ids,
            "related_memory_keys": self.related_memory_keys,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            project_id=data.get("project_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
            depends_on=data.get("depends_on", []),
            estimated_effort=data.get("estimated_effort", "medium"),
            assigned_agents=data.get("assigned_agents", []),
            related_episode_ids=data.get("related_episode_ids", []),
            related_memory_keys=data.get("related_memory_keys", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            tags=data.get("tags", []),
        )


@dataclass
class Milestone:
    """
    A milestone grouping tasks within a project.

    status: "pending" | "in_progress" | "completed"
    """

    milestone_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    name: str = ""
    description: str = ""
    task_ids: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "task_ids": self.task_ids,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Milestone":
        return cls(
            milestone_id=data.get("milestone_id", str(uuid.uuid4())),
            project_id=data.get("project_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            task_ids=data.get("task_ids", []),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
        )


@dataclass
class ProgressReport:
    """Progress report for a project — calculated from actual task data."""

    project_id: str = ""
    project_name: str = ""
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    pending_tasks: int = 0
    completion_pct: float = 0.0
    completed_today: int = 0
    completed_this_week: int = 0
    velocity: float = 0.0
    avg_completion_hours: float = 0.0
    estimated_completion: Optional[str] = None
    health: str = "on_track"  # "on_track" | "at_risk" | "blocked" | "stalled"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "blocked_tasks": self.blocked_tasks,
            "pending_tasks": self.pending_tasks,
            "completion_pct": self.completion_pct,
            "completed_today": self.completed_today,
            "completed_this_week": self.completed_this_week,
            "velocity": self.velocity,
            "avg_completion_hours": self.avg_completion_hours,
            "estimated_completion": self.estimated_completion,
            "health": self.health,
        }


@dataclass
class WorkspaceSummaryData:
    """Summary data for the dashboard widget."""

    active_project: Optional[Dict[str, Any]] = None
    total_active_projects: int = 0
    total_active_tasks: int = 0
    total_blocked_tasks: int = 0
    next_task: Optional[Dict[str, Any]] = None
    completed_today: int = 0
    progress_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_project": self.active_project,
            "total_active_projects": self.total_active_projects,
            "total_active_tasks": self.total_active_tasks,
            "total_blocked_tasks": self.total_blocked_tasks,
            "next_task": self.next_task,
            "completed_today": self.completed_today,
            "progress_pct": self.progress_pct,
        }
