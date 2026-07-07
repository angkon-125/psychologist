"""
Project Manager — Cognitive Workspace

Manages project lifecycle: create, archive, resume, rename, delete.
"""

import logging
from datetime import datetime
from typing import List, Optional

from .schemas import Project
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.project_manager")


class ProjectManager:
    """
    Manages workspace projects.

    Usage:
        pm = ProjectManager(store)
        project = pm.create_project("Android App", priority="high")
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store
        self._active_project_id: Optional[str] = None

    def create_project(
        self,
        name: str,
        description: str = "",
        priority: str = "medium",
        deadline: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            description=description,
            priority=priority,
            deadline=deadline,
            tags=tags or [],
        )
        self.store.save_project(project)
        self._active_project_id = project.project_id
        logger.info("Created project: %s (id=%s)", name, project.project_id)
        return project

    def archive_project(self, project_id: str) -> Optional[Project]:
        """Archive a project."""
        project = self.store.get_project(project_id)
        if not project:
            return None
        project.status = "archived"
        project.updated_at = datetime.now().isoformat()
        self.store.save_project(project)
        if self._active_project_id == project_id:
            self._active_project_id = None
        logger.info("Archived project: %s", project_id)
        return project

    def resume_project(self, project_id: str) -> Optional[Project]:
        """Resume an archived/paused project."""
        project = self.store.get_project(project_id)
        if not project:
            return None
        project.status = "active"
        project.updated_at = datetime.now().isoformat()
        self.store.save_project(project)
        self._active_project_id = project_id
        logger.info("Resumed project: %s", project_id)
        return project

    def rename_project(self, project_id: str, new_name: str) -> Optional[Project]:
        """Rename a project."""
        project = self.store.get_project(project_id)
        if not project:
            return None
        project.name = new_name
        project.updated_at = datetime.now().isoformat()
        self.store.save_project(project)
        logger.info("Renamed project %s to: %s", project_id, new_name)
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project and its tasks/milestones."""
        result = self.store.delete_project(project_id)
        if result and self._active_project_id == project_id:
            self._active_project_id = None
        logger.info("Deleted project: %s (success=%s)", project_id, result)
        return result

    def get_active_project(self) -> Optional[Project]:
        """Get the most recently active project."""
        if self._active_project_id:
            project = self.store.get_project(self._active_project_id)
            if project and project.status == "active":
                return project
        # Fallback: most recently updated active project
        active_projects = self.store.list_projects(status="active")
        if active_projects:
            self._active_project_id = active_projects[0].project_id
            return active_projects[0]
        return None

    def set_active_project(self, project_id: str) -> None:
        """Set the active project."""
        self._active_project_id = project_id

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """List projects with optional status filter."""
        return self.store.list_projects(status=status)

    def complete_project(self, project_id: str) -> Optional[Project]:
        """Mark a project as completed."""
        project = self.store.get_project(project_id)
        if not project:
            return None
        project.status = "completed"
        project.updated_at = datetime.now().isoformat()
        self.store.save_project(project)
        logger.info("Completed project: %s", project_id)
        return project

    def pause_project(self, project_id: str) -> Optional[Project]:
        """Pause a project."""
        project = self.store.get_project(project_id)
        if not project:
            return None
        project.status = "paused"
        project.updated_at = datetime.now().isoformat()
        self.store.save_project(project)
        if self._active_project_id == project_id:
            self._active_project_id = None
        logger.info("Paused project: %s", project_id)
        return project
