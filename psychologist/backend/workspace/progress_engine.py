"""
Progress Engine — Cognitive Workspace

Calculates real progress from actual task data.
No fake percentages.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from .schemas import ProgressReport
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.progress_engine")


class ProgressEngine:
    """
    Calculates project progress from actual task data.

    Usage:
        pe = ProgressEngine(store)
        report = pe.calculate_progress(project_id)
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store

    def calculate_progress(self, project_id: str) -> ProgressReport:
        """
        Calculate progress report for a project.

        All values are computed from actual task data.
        """
        project = self.store.get_project(project_id)
        tasks = self.store.list_tasks(project_id=project_id)

        project_name = project.name if project else "Unknown"

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        blocked = sum(1 for t in tasks if t.status == "blocked")
        pending = sum(1 for t in tasks if t.status == "pending")

        # Completion percentage (real math)
        completion_pct = (completed / total * 100.0) if total > 0 else 0.0

        # Completed today (last 24h)
        now = datetime.now()
        today_start = now - timedelta(hours=24)
        completed_today = 0
        for t in tasks:
            if t.status == "completed" and t.completed_at:
                try:
                    completed_dt = datetime.fromisoformat(t.completed_at)
                    if completed_dt >= today_start:
                        completed_today += 1
                except (ValueError, TypeError):
                    pass

        # Completed this week (last 7 days)
        week_start = now - timedelta(days=7)
        completed_this_week = 0
        for t in tasks:
            if t.status == "completed" and t.completed_at:
                try:
                    completed_dt = datetime.fromisoformat(t.completed_at)
                    if completed_dt >= week_start:
                        completed_this_week += 1
                except (ValueError, TypeError):
                    pass

        # Velocity (tasks per day over last 7 days)
        velocity = completed_this_week / 7.0

        # Average completion time (hours from created_at to completed_at)
        total_hours = 0.0
        completion_count = 0
        for t in tasks:
            if t.status == "completed" and t.completed_at and t.created_at:
                try:
                    created_dt = datetime.fromisoformat(t.created_at)
                    completed_dt = datetime.fromisoformat(t.completed_at)
                    hours = (completed_dt - created_dt).total_seconds() / 3600.0
                    if hours > 0:
                        total_hours += hours
                        completion_count += 1
                except (ValueError, TypeError):
                    pass
        avg_completion_hours = (total_hours / completion_count) if completion_count > 0 else 0.0

        # Estimated completion
        estimated_completion = None
        remaining = total - completed
        if velocity > 0 and remaining > 0:
            days_remaining = remaining / velocity
            eta_date = now + timedelta(days=days_remaining)
            estimated_completion = eta_date.strftime("%Y-%m-%d")

        # Health determination
        health = self._determine_health(
            total=total,
            completed=completed,
            blocked=blocked,
            pending=pending,
            velocity=velocity,
            completed_this_week=completed_this_week,
        )

        return ProgressReport(
            project_id=project_id,
            project_name=project_name,
            total_tasks=total,
            completed_tasks=completed,
            blocked_tasks=blocked,
            pending_tasks=pending,
            completion_pct=round(completion_pct, 1),
            completed_today=completed_today,
            completed_this_week=completed_this_week,
            velocity=round(velocity, 2),
            avg_completion_hours=round(avg_completion_hours, 1),
            estimated_completion=estimated_completion,
            health=health,
        )

    def _determine_health(
        self,
        total: int,
        completed: int,
        blocked: int,
        pending: int,
        velocity: float,
        completed_this_week: int,
    ) -> str:
        """
        Determine project health.

        - "on_track": velocity > 0, no blocked tasks
        - "at_risk": some blocked tasks but velocity > 0
        - "blocked": all pending tasks are blocked
        - "stalled": no completions in 7 days
        """
        if total == 0:
            return "on_track"

        if completed == total:
            return "on_track"

        # Stalled: no completions this week and there are pending tasks
        if completed_this_week == 0 and (pending > 0 or blocked > 0):
            return "stalled"

        # Blocked: all non-completed tasks are blocked
        non_completed = total - completed
        if non_completed > 0 and blocked >= non_completed:
            return "blocked"

        # At risk: some blocked but still making progress
        if blocked > 0 and velocity > 0:
            return "at_risk"

        return "on_track"
