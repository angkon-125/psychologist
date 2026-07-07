"""
Workspace Search — Cognitive Workspace

Query-based search across projects, tasks, and milestones.
"""

import logging
from typing import Dict, List, Any, Optional

from .schemas import Project, Task, Milestone
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.search")


class WorkspaceSearch:
    """
    Search across the workspace.

    Usage:
        ws = WorkspaceSearch(store)
        results = ws.search("android")
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store

    def search(self, query: str) -> Dict[str, List[Any]]:
        """
        Search across projects, tasks, and milestones.

        Matches against title, description, tags, assigned_agents.
        Returns dict with projects, tasks, milestones lists.
        """
        if not query:
            return {"projects": [], "tasks": [], "milestones": []}

        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Search projects
        all_projects = self.store.list_projects()
        matched_projects = [
            p for p in all_projects
            if self._matches(p.name, p.description, p.tags, query_lower, query_words)
        ]

        # Search tasks
        all_tasks = self.store.list_tasks()
        matched_tasks = [
            t for t in all_tasks
            if self._matches(
                t.title, t.description, t.tags + t.assigned_agents,
                query_lower, query_words
            )
        ]

        # Search milestones
        all_milestones = self.store.list_milestones()
        matched_milestones = [
            m for m in all_milestones
            if self._matches(m.name, m.description, [], query_lower, query_words)
        ]

        return {
            "projects": [p.to_dict() for p in matched_projects],
            "tasks": [t.to_dict() for t in matched_tasks],
            "milestones": [m.to_dict() for m in matched_milestones],
        }

    def _matches(
        self,
        title: str,
        description: str,
        tags: List[str],
        query_lower: str,
        query_words: set,
    ) -> bool:
        """Check if an item matches the search query."""
        # Direct substring match
        if query_lower in title.lower():
            return True
        if query_lower in description.lower():
            return True
        # Tag match
        for tag in tags:
            if query_lower in tag.lower():
                return True
        # Word overlap
        text_words = set((title + " " + description).lower().split())
        if query_words & text_words:
            return True
        return False

    def find_unfinished_tasks(self, project_id: Optional[str] = None) -> List[Task]:
        """Find all unfinished tasks (pending, in_progress, blocked)."""
        tasks = self.store.list_tasks(project_id=project_id)
        return [t for t in tasks if t.status in ("pending", "in_progress", "blocked")]

    def find_blocked_tasks(self, project_id: Optional[str] = None) -> List[Task]:
        """Find all blocked tasks."""
        return self.store.list_tasks(project_id=project_id, status="blocked")

    def find_tasks_for_agent(self, agent_name: str) -> List[Task]:
        """Find tasks assigned to a specific agent."""
        all_tasks = self.store.list_tasks()
        return [t for t in all_tasks if agent_name in t.assigned_agents]

    def find_completed_milestones(self, project_id: Optional[str] = None) -> List[Milestone]:
        """Find completed milestones."""
        milestones = self.store.list_milestones(project_id=project_id)
        return [m for m in milestones if m.status == "completed"]
