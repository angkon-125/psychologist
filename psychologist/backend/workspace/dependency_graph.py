"""
Dependency Graph — Cognitive Workspace

DAG-based dependency tracking for tasks.
Detects blocked tasks, ready tasks, and circular dependencies.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .schemas import Task
from .workspace_store import WorkspaceStore

logger = logging.getLogger("zara.workspace.dependency_graph")


class DependencyGraph:
    """
    Manages task dependencies within projects.

    Usage:
        dg = DependencyGraph(store)
        ready = dg.get_ready_tasks(project_id)
        blocked = dg.get_blocked_tasks(project_id)
    """

    def __init__(self, store: WorkspaceStore):
        self.store = store
        self._cache: Dict[str, Dict[str, List[str]]] = {}

    def _invalidate_cache(self, project_id: str) -> None:
        """Invalidate the dependency graph cache for a project."""
        self._cache.pop(project_id, None)

    def build_graph(self, project_id: str) -> Dict[str, List[str]]:
        """
        Build adjacency list from task dependencies.

        Returns:
            Dict mapping task_id -> list of task_ids it depends on
        """
        if project_id in self._cache:
            return self._cache[project_id]

        tasks = self.store.list_tasks(project_id=project_id)
        graph: Dict[str, List[str]] = {}
        for task in tasks:
            graph[task.task_id] = list(task.depends_on)

        self._cache[project_id] = graph
        return graph

    def get_blocked_tasks(self, project_id: str) -> List[Task]:
        """
        Get tasks whose dependencies are not all completed.

        A task is blocked if:
        - It has dependencies (depends_on is non-empty)
        - At least one dependency is not completed
        - The task itself is not completed/cancelled
        """
        tasks = self.store.list_tasks(project_id=project_id)
        completed_ids = {t.task_id for t in tasks if t.status == "completed"}

        blocked = []
        for task in tasks:
            if task.status in ("completed", "cancelled"):
                continue
            if not task.depends_on:
                continue
            # Check if all dependencies are completed
            unmet = [dep for dep in task.depends_on if dep not in completed_ids]
            if unmet:
                blocked.append(task)

        return blocked

    def get_ready_tasks(self, project_id: str) -> List[Task]:
        """
        Get tasks whose dependencies are all completed and status is pending.

        These are tasks that can be started immediately.
        """
        tasks = self.store.list_tasks(project_id=project_id)
        completed_ids = {t.task_id for t in tasks if t.status == "completed"}

        ready = []
        for task in tasks:
            if task.status != "pending":
                continue
            # Check if all dependencies are completed
            if task.depends_on:
                unmet = [dep for dep in task.depends_on if dep not in completed_ids]
                if unmet:
                    continue
            ready.append(task)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ready.sort(key=lambda t: priority_order.get(t.priority, 2))

        return ready

    def detect_circular_dependencies(self, project_id: str) -> List[List[str]]:
        """
        Detect circular dependencies in the project.

        Returns:
            List of cycles, where each cycle is a list of task_ids
        """
        graph = self.build_graph(project_id)
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def _dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for dep in graph.get(node, []):
                if dep not in visited:
                    _dfs(dep)
                elif dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycles.append(path[cycle_start:] + [dep])

            path.pop()
            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                _dfs(node)

        return cycles

    def get_dependency_chain(self, task_id: str) -> List[str]:
        """
        Get the ordered chain of dependencies for a task.

        Returns:
            List of task_ids in dependency order (deepest first)
        """
        # Find which project this task belongs to
        task = self.store.get_task(task_id)
        if not task:
            return []

        graph = self.build_graph(task.project_id)
        chain: List[str] = []
        visited: Set[str] = set()

        def _collect(tid: str) -> None:
            if tid in visited:
                return
            visited.add(tid)
            for dep in graph.get(tid, []):
                _collect(dep)
            chain.append(tid)

        _collect(task_id)
        return chain

    def invalidate(self, project_id: str) -> None:
        """Public method to invalidate cache (called after task status changes)."""
        self._invalidate_cache(project_id)
