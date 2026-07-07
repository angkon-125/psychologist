"""
Milestone Tracker — Cognitive Workspace

Manages milestone grouping and completion tracking.
"""

import logging
from datetime import datetime
from typing import List, Optional

from .schemas import Milestone
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.milestone_tracker")


class MilestoneTracker:
    """
    Manages milestones within projects.

    Usage:
        mt = MilestoneTracker(store)
        ms = mt.create_milestone(project_id, "Phase 1", task_ids=["t1", "t2"])
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store

    def create_milestone(
        self,
        project_id: str,
        name: str,
        description: str = "",
        task_ids: Optional[List[str]] = None,
    ) -> Milestone:
        """Create a new milestone."""
        milestone = Milestone(
            project_id=project_id,
            name=name,
            description=description,
            task_ids=task_ids or [],
        )
        self.store.save_milestone(milestone)
        logger.info("Created milestone: %s (id=%s)", name, milestone.milestone_id)
        return milestone

    def complete_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """Mark a milestone as completed."""
        milestone = self.store.get_milestone(milestone_id)
        if not milestone:
            return None
        milestone.status = "completed"
        milestone.completed_at = datetime.now().isoformat()
        self.store.save_milestone(milestone)
        logger.info("Completed milestone: %s", milestone_id)
        return milestone

    def get_milestone_progress(self, milestone_id: str) -> float:
        """
        Calculate milestone progress as % of task_ids completed.

        Returns:
            Float 0.0-100.0
        """
        milestone = self.store.get_milestone(milestone_id)
        if not milestone or not milestone.task_ids:
            return 0.0

        completed = 0
        for task_id in milestone.task_ids:
            task = self.store.get_task(task_id)
            if task and task.status == "completed":
                completed += 1

        return (completed / len(milestone.task_ids)) * 100.0

    def list_milestones(self, project_id: Optional[str] = None) -> List[Milestone]:
        """List milestones, optionally filtered by project."""
        return self.store.list_milestones(project_id=project_id)

    def get_next_milestone(self, project_id: str) -> Optional[Milestone]:
        """Get the next pending/in_progress milestone for a project."""
        milestones = self.store.list_milestones(project_id=project_id)
        for ms in milestones:
            if ms.status in ("pending", "in_progress"):
                return ms
        return None

    def check_auto_completion(self, milestone_id: str) -> bool:
        """
        Check if all tasks in a milestone are completed.
        If so, auto-complete the milestone.

        Returns:
            True if milestone was auto-completed
        """
        milestone = self.store.get_milestone(milestone_id)
        if not milestone or not milestone.task_ids:
            return False

        if milestone.status == "completed":
            return True

        all_completed = True
        for task_id in milestone.task_ids:
            task = self.store.get_task(task_id)
            if not task or task.status != "completed":
                all_completed = False
                break

        if all_completed:
            milestone.status = "completed"
            milestone.completed_at = datetime.now().isoformat()
            self.store.save_milestone(milestone)
            logger.info("Auto-completed milestone: %s", milestone_id)
            return True

        return False

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """Get a milestone by ID."""
        return self.store.get_milestone(milestone_id)
