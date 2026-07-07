"""
Workspace Manager — Cognitive Workspace

Top-level orchestrator for the cognitive workspace.
Holds all sub-managers and provides pass-through access.
"""

import logging
from typing import Dict, Any, List, Optional

from .schemas import Project, Task, Milestone, ProgressReport, WorkspaceSummaryData
from .workspace_store import WorkspaceStore
from .project_manager import ProjectManager
from .task_manager import TaskManager
from .dependency_graph import DependencyGraph
from .milestone_tracker import MilestoneTracker
from .progress_engine import ProgressEngine
from .workspace_search import WorkspaceSearch
from .workspace_summary import WorkspaceSummaryBuilder

logger = logging.getLogger("zara.workspace.manager")


class WorkspaceManager:
    """
    Top-level orchestrator for the cognitive workspace.

    Usage:
        wm = WorkspaceManager(db_path="data/zara_memory.db")
        project = wm.create_project("Android App")
        task = wm.create_task(project.project_id, "Build UI")
        summary = wm.get_summary()
    """

    def __init__(self, db_path: str):
        self.store = WorkspaceStore(db_path)
        self.project_manager = ProjectManager(self.store)
        self.task_manager = TaskManager(self.store)
        self.dependency_graph = DependencyGraph(self.store)
        self.milestone_tracker = MilestoneTracker(self.store)
        self.progress_engine = ProgressEngine(self.store)
        self.workspace_search = WorkspaceSearch(self.store)
        self.summary_builder = WorkspaceSummaryBuilder(
            self.store,
            self.project_manager,
            self.task_manager,
            self.dependency_graph,
            self.progress_engine,
        )
        logger.info("WorkspaceManager initialized (db=%s)", db_path)

    # ─── Projects ─────────────────────────────────────────────────

    def create_project(self, name: str, **kwargs) -> Project:
        return self.project_manager.create_project(name, **kwargs)

    def archive_project(self, project_id: str) -> Optional[Project]:
        return self.project_manager.archive_project(project_id)

    def resume_project(self, project_id: str) -> Optional[Project]:
        return self.project_manager.resume_project(project_id)

    def rename_project(self, project_id: str, new_name: str) -> Optional[Project]:
        return self.project_manager.rename_project(project_id, new_name)

    def delete_project(self, project_id: str) -> bool:
        return self.project_manager.delete_project(project_id)

    def get_active_project(self) -> Optional[Project]:
        return self.project_manager.get_active_project()

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        return self.project_manager.list_projects(status=status)

    # ─── Tasks ────────────────────────────────────────────────────

    def create_task(self, project_id: str, title: str, **kwargs) -> Task:
        task = self.task_manager.create_task(project_id, title, **kwargs)
        self.dependency_graph.invalidate(project_id)
        return task

    def update_task(self, task_id: str, **fields) -> Optional[Task]:
        task = self.task_manager.update_task(task_id, **fields)
        if task:
            self.dependency_graph.invalidate(task.project_id)
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        task = self.task_manager.complete_task(task_id)
        if task:
            self.dependency_graph.invalidate(task.project_id)
            # Check milestone auto-completion
            for ms in self.milestone_tracker.list_milestones(task.project_id):
                if task_id in ms.task_ids:
                    self.milestone_tracker.check_auto_completion(ms.milestone_id)
        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        return self.task_manager.start_task(task_id)

    def block_task(self, task_id: str, reason: str = "") -> Optional[Task]:
        task = self.task_manager.block_task(task_id, reason=reason)
        if task:
            self.dependency_graph.invalidate(task.project_id)
        return task

    def delete_task(self, task_id: str) -> bool:
        task = self.task_manager.get_task(task_id)
        project_id = task.project_id if task else None
        result = self.task_manager.delete_task(task_id)
        if result and project_id:
            self.dependency_graph.invalidate(project_id)
        return result

    def list_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Task]:
        return self.task_manager.list_tasks(project_id=project_id, status=status)

    # ─── Milestones ───────────────────────────────────────────────

    def create_milestone(self, project_id: str, name: str, **kwargs) -> Milestone:
        return self.milestone_tracker.create_milestone(project_id, name, **kwargs)

    def list_milestones(self, project_id: Optional[str] = None) -> List[Milestone]:
        return self.milestone_tracker.list_milestones(project_id=project_id)

    # ─── Progress ─────────────────────────────────────────────────

    def calculate_progress(self, project_id: str) -> ProgressReport:
        return self.progress_engine.calculate_progress(project_id)

    # ─── Search ───────────────────────────────────────────────────

    def search(self, query: str) -> Dict[str, Any]:
        return self.workspace_search.search(query)

    # ─── Summary ──────────────────────────────────────────────────

    def get_summary(self) -> WorkspaceSummaryData:
        return self.summary_builder.get_summary()

    def get_full_workspace(self) -> Dict[str, Any]:
        """Return complete workspace state."""
        summary = self.get_summary()
        projects = self.list_projects()
        all_tasks = self.list_tasks()
        milestones = self.list_milestones()

        return {
            "summary": summary.to_dict(),
            "projects": [p.to_dict() for p in projects],
            "tasks": [t.to_dict() for t in all_tasks],
            "milestones": [m.to_dict() for m in milestones],
        }
