"""
Goal Tracker — Executive Brain

Tracks long-running goals across conversation turns.
Provides goal detection from text, goal state management,
and cross-session persistence via JSON storage.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import GoalState

logger = logging.getLogger("zara.executive.goal_tracker")


class GoalTracker:
    """
    Tracks user goals across conversation turns and sessions.

    Usage:
        tracker = GoalTracker(session_dir="/path/to/session")
        goal = tracker.create_goal("Complete project", tasks=["task1", "task2"])
        tracker.update_goal(goal.goal_id, completed_tasks=["task1"])
        summary = tracker.get_goal_summary(goal.goal_id)
    """

    def __init__(self, session_dir: Optional[str] = None):
        """
        Initialize goal tracker.

        Args:
            session_dir: Directory for persisting goals (JSON). If None, no persistence.
        """
        self.session_dir = Path(session_dir) if session_dir else None
        self.goals: Dict[str, GoalState] = {}
        self._load_goals()

    def create_goal(
        self,
        description: str,
        tasks: Optional[List[str]] = None,
    ) -> GoalState:
        """
        Create a new goal.

        Args:
            description: What the user wants to achieve
            tasks: List of tasks to complete the goal

        Returns:
            Created GoalState
        """
        goal = GoalState(
            goal_id=str(uuid.uuid4()),
            description=description,
            status="active",
            completed_tasks=[],
            pending_tasks=tasks or [],
            completion_pct=0.0,
        )
        self.goals[goal.goal_id] = goal
        self._save_goals()
        logger.info("Created goal: %s (id=%s)", description, goal.goal_id)
        return goal

    def update_goal(
        self,
        goal_id: str,
        completed_tasks: Optional[List[str]] = None,
        pending_tasks: Optional[List[str]] = None,
    ) -> Optional[GoalState]:
        """
        Update goal progress.

        Args:
            goal_id: Goal identifier
            completed_tasks: List of completed tasks
            pending_tasks: List of remaining tasks

        Returns:
            Updated GoalState or None if not found
        """
        goal = self.goals.get(goal_id)
        if not goal:
            logger.warning("Goal not found: %s", goal_id)
            return None

        if completed_tasks is not None:
            goal.completed_tasks = completed_tasks
        if pending_tasks is not None:
            goal.pending_tasks = pending_tasks

        # Calculate completion percentage
        total = len(goal.completed_tasks) + len(goal.pending_tasks)
        if total > 0:
            goal.completion_pct = len(goal.completed_tasks) / total
        else:
            goal.completion_pct = 0.0

        # Auto-complete if all tasks done and there were tasks to begin with
        total = len(goal.completed_tasks) + len(goal.pending_tasks)
        if total > 0 and len(goal.pending_tasks) == 0:
            goal.status = "completed"
            goal.completion_pct = 1.0

        self._save_goals()
        logger.debug(
            "Updated goal %s: %.0f%% complete", goal_id, goal.completion_pct * 100
        )
        return goal

    def get_active_goals(self) -> List[GoalState]:
        """Get all active goals."""
        return [g for g in self.goals.values() if g.status == "active"]

    def get_goal_summary(self, goal_id: str) -> Optional[Dict]:
        """
        Get a natural-language summary of a goal for conversation continuity.

        Args:
            goal_id: Goal identifier

        Returns:
            Dict with description, status, completion, and next steps
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return None

        next_steps = goal.pending_tasks[:2] if goal.pending_tasks else []
        return {
            "description": goal.description,
            "status": goal.status,
            "completion_pct": goal.completion_pct,
            "completed": len(goal.completed_tasks),
            "pending": len(goal.pending_tasks),
            "next_steps": next_steps,
        }

    def detect_goal_from_text(self, text: str) -> Optional[str]:
        """
        Detect if text references an existing goal.

        Args:
            text: User input text

        Returns:
            Goal ID if matched, None otherwise
        """
        if not text:
            return None

        text_lower = text.lower()

        # Check if any goal description appears in text
        for goal_id, goal in self.goals.items():
            if goal.status != "active":
                continue
            # Simple keyword match: if goal description words appear in text
            goal_words = set(goal.description.lower().split())
            text_words = set(text_lower.split())
            overlap = goal_words & text_words
            # If significant overlap, assume this is the goal
            if len(overlap) >= 2 or (len(overlap) == 1 and len(goal_words) <= 3):
                logger.debug("Detected goal %s from text", goal_id)
                return goal_id

        return None

    def _save_goals(self):
        """Persist goals to JSON file."""
        if not self.session_dir:
            return
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
            goals_file = self.session_dir / "goals.json"
            data = {gid: g.to_dict() for gid, g in self.goals.items()}
            goals_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("Failed to save goals: %s", e)

    def _load_goals(self):
        """Load goals from JSON file."""
        if not self.session_dir:
            return
        goals_file = self.session_dir / "goals.json"
        if not goals_file.exists():
            return
        try:
            data = json.loads(goals_file.read_text())
            self.goals = {gid: GoalState.from_dict(gdata) for gid, gdata in data.items()}
            logger.info("Loaded %d goals from session", len(self.goals))
        except Exception as e:
            logger.error("Failed to load goals: %s", e)
