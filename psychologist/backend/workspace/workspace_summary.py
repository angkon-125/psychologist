"""
Workspace Summary — Cognitive Workspace

Dashboard widget data: active project, next task, progress, health.
"""

import logging
from typing import Optional, Dict, Any

from .schemas import WorkspaceSummaryData
from .workspace_store import WorkspaceStore
from .project_manager import ProjectManager
from .task_manager import TaskManager
from .dependency_graph import DependencyGraph
from .progress_engine import ProgressEngine

logger = logging.getLogger("zara.workspace.summary")


class WorkspaceSummaryBuilder:
    """
    Builds workspace summary for the dashboard widget.

    Usage:
        builder = WorkspaceSummaryBuilder(store, pm, tm, dg, pe)
        summary = builder.get_summary()
    """

    def __init__(
        self,
        store: WorkspaceStore,
        project_manager: ProjectManager,
        task_manager: TaskManager,
        dependency_graph: DependencyGraph,
        progress_engine: ProgressEngine,
    ):
        self.store = store
        self.pm = project_manager
        self.tm = task_manager
        self.dg = dependency_graph
        self.pe = progress_engine

    def get_summary(self) -> WorkspaceSummaryData:
        """Build a workspace summary."""
        active_project = self.pm.get_active_project()
        active_project_dict = None
        progress_pct = 0.0

        if active_project:
            report = self.pe.calculate_progress(active_project.project_id)
            progress_pct = report.completion_pct
            active_project_dict = {
                "project_id": active_project.project_id,
                "name": active_project.name,
                "progress_pct": report.completion_pct,
                "health": report.health,
                "total_tasks": report.total_tasks,
                "completed_tasks": report.completed_tasks,
                "estimated_completion": report.estimated_completion,
            }

        # Count active projects
        all_active = self.pm.list_projects(status="active")
        total_active_projects = len(all_active)

        # Count active tasks across all active projects
        total_active_tasks = 0
        total_blocked_tasks = 0
        completed_today = 0

        for proj in all_active:
            tasks = self.tm.list_tasks(project_id=proj.project_id)
            total_active_tasks += sum(1 for t in tasks if t.status in ("pending", "in_progress"))
            total_blocked_tasks += sum(1 for t in tasks if t.status == "blocked")

        # Completed today across all projects
        all_tasks = self.tm.list_tasks(status="completed")
        from datetime import datetime, timedelta
        today_start = datetime.now() - timedelta(hours=24)
        for t in all_tasks:
            if t.completed_at:
                try:
                    completed_dt = datetime.fromisoformat(t.completed_at)
                    if completed_dt >= today_start:
                        completed_today += 1
                except (ValueError, TypeError):
                    pass

        # Next recommended task (first ready task from active project)
        next_task_dict = None
        if active_project:
            ready = self.dg.get_ready_tasks(active_project.project_id)
            if ready:
                next = ready[0]
                next_task_dict = {
                    "task_id": next.task_id,
                    "title": next.title,
                    "priority": next.priority,
                    "estimated_effort": next.estimated_effort,
                }

        return WorkspaceSummaryData(
            active_project=active_project_dict,
            total_active_projects=total_active_projects,
            total_active_tasks=total_active_tasks,
            total_blocked_tasks=total_blocked_tasks,
            next_task=next_task_dict,
            completed_today=completed_today,
            progress_pct=progress_pct,
        )
