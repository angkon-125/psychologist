"""
Task Manager — Cognitive Workspace

Manages task lifecycle: create, start, complete, block, delete.
"""

import logging
from datetime import datetime
from typing import List, Optional

from .schemas import Task
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.task_manager")


class TaskManager:
    """
    Manages workspace tasks.

    Usage:
        tm = TaskManager(store)
        task = tm.create_task(project_id, "Build UI", priority="high")
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store

    def create_task(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        depends_on: Optional[List[str]] = None,
        estimated_effort: str = "medium",
        assigned_agents: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            depends_on=depends_on or [],
            estimated_effort=estimated_effort,
            assigned_agents=assigned_agents or [],
            tags=tags or [],
        )
        self.store.save_task(task)
        logger.info("Created task: %s (id=%s, project=%s)", title, task.task_id, project_id)
        return task

    def update_task(self, task_id: str, **fields) -> Optional[Task]:
        """Update task fields."""
        task = self.store.get_task(task_id)
        if not task:
            return None

        for key, value in fields.items():
            if hasattr(task, key):
                setattr(task, key, value)

        self.store.save_task(task)
        logger.debug("Updated task: %s", task_id)
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        task = self.store.get_task(task_id)
        if not task:
            return None
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        self.store.save_task(task)
        logger.info("Completed task: %s (%s)", task.title, task_id)
        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress."""
        task = self.store.get_task(task_id)
        if not task:
            return None
        task.status = "in_progress"
        self.store.save_task(task)
        logger.info("Started task: %s (%s)", task.title, task_id)
        return task

    def block_task(self, task_id: str, reason: str = "") -> Optional[Task]:
        """Mark a task as blocked."""
        task = self.store.get_task(task_id)
        if not task:
            return None
        task.status = "blocked"
        if reason:
            task.description = (task.description + "\n[Blocked: " + reason + "]").strip()
        self.store.save_task(task)
        logger.info("Blocked task: %s (%s)", task.title, task_id)
        return task

    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task."""
        task = self.store.get_task(task_id)
        if not task:
            return None
        task.status = "cancelled"
        self.store.save_task(task)
        logger.info("Cancelled task: %s (%s)", task.title, task_id)
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        result = self.store.delete_task(task_id)
        logger.info("Deleted task: %s (success=%s)", task_id, result)
        return result

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        return self.store.list_tasks(project_id=project_id, status=status)

    def get_tasks_for_agent(self, agent_name: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        all_tasks = self.store.list_tasks()
        return [t for t in all_tasks if agent_name in t.assigned_agents]

    def get_related_tasks(self, episode_id: str) -> List[Task]:
        """Get tasks related to a specific episode."""
        all_tasks = self.store.list_tasks()
        return [t for t in all_tasks if episode_id in t.related_episode_ids]

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.store.get_task(task_id)
