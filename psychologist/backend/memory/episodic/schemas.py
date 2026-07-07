"""
Episodic Memory Schemas

Data structures for the episodic memory system:
- Episode: one meaningful event (not a raw message)
- EpisodeSearchResult: search results container
- EmotionSnapshot: point-in-time emotional state linked to an episode
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Episode:
    """
    One meaningful event in the user's journey.

    An episode groups related interactions into a coherent memory,
    with importance scoring, emotional context, and goal linkage.
    """

    episode_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    summary: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime = field(default_factory=datetime.now)
    topics: List[str] = field(default_factory=list)
    importance: float = 0.0
    emotion: str = "neutral"
    emotion_intensity: float = 0.0
    outcome: str = ""
    pending_tasks: List[str] = field(default_factory=list)
    follow_up: str = ""
    related_goal_id: str = ""
    source_session_id: str = ""
    interaction_ids: List[str] = field(default_factory=list)
    locked: bool = False
    archived: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "title": self.title,
            "summary": self.summary,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "topics": self.topics,
            "importance": self.importance,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "outcome": self.outcome,
            "pending_tasks": self.pending_tasks,
            "follow_up": self.follow_up,
            "related_goal_id": self.related_goal_id,
            "source_session_id": self.source_session_id,
            "interaction_ids": self.interaction_ids,
            "locked": self.locked,
            "archived": self.archived,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        def _parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str) and val:
                try:
                    return datetime.fromisoformat(val)
                except (ValueError, TypeError):
                    pass
            return datetime.now()

        return cls(
            episode_id=data.get("episode_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            started_at=_parse_dt(data.get("started_at")),
            ended_at=_parse_dt(data.get("ended_at")),
            topics=data.get("topics", []),
            importance=float(data.get("importance", 0.0)),
            emotion=data.get("emotion", "neutral"),
            emotion_intensity=float(data.get("emotion_intensity", 0.0)),
            outcome=data.get("outcome", ""),
            pending_tasks=data.get("pending_tasks", []),
            follow_up=data.get("follow_up", ""),
            related_goal_id=data.get("related_goal_id", ""),
            source_session_id=data.get("source_session_id", ""),
            interaction_ids=data.get("interaction_ids", []),
            locked=bool(data.get("locked", False)),
            archived=bool(data.get("archived", False)),
            created_at=_parse_dt(data.get("created_at")),
        )


@dataclass
class EpisodeSearchResult:
    """Container for episode search results."""

    episodes: List[Episode] = field(default_factory=list)
    query: str = ""
    total_count: int = 0
    search_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episodes": [e.to_dict() for e in self.episodes],
            "query": self.query,
            "total_count": self.total_count,
            "search_time_ms": self.search_time_ms,
        }


@dataclass
class EmotionSnapshot:
    """Point-in-time emotional state linked to an episode."""

    timestamp: datetime = field(default_factory=datetime.now)
    emotion: str = "neutral"
    intensity: float = 0.0
    episode_id: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "emotion": self.emotion,
            "intensity": self.intensity,
            "episode_id": self.episode_id,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionSnapshot":
        ts = data.get("timestamp")
        if isinstance(ts, str) and ts:
            try:
                ts = datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                ts = datetime.now()
        elif not isinstance(ts, datetime):
            ts = datetime.now()

        return cls(
            timestamp=ts,
            emotion=data.get("emotion", "neutral"),
            intensity=float(data.get("intensity", 0.0)),
            episode_id=data.get("episode_id", ""),
            notes=data.get("notes", ""),
        )
