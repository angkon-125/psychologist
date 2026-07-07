"""
Workspace Store — SQLite Persistence

SQLite-backed storage for projects, tasks, and milestones.
Uses the existing data/zara_memory.db database.
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .schemas import Project, Task, Milestone

logger = logging.getLogger("zara.workspace.store")


class WorkspaceStore:
    """
    SQLite-backed persistence for the cognitive workspace.

    Usage:
        store = WorkspaceStore("data/zara_memory.db")
        store.save_project(project)
        projects = store.list_projects(status="active")
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create workspace tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ws_projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    created_at TEXT,
                    updated_at TEXT,
                    deadline TEXT,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ws_tasks (
                    task_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    depends_on TEXT,
                    estimated_effort TEXT DEFAULT 'medium',
                    assigned_agents TEXT,
                    related_episode_ids TEXT,
                    related_memory_keys TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    tags TEXT,
                    FOREIGN KEY (project_id) REFERENCES ws_projects(project_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ws_milestones (
                    milestone_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    task_ids TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES ws_projects(project_id)
                )
            """)
            # Indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_tasks_project ON ws_tasks(project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_tasks_status ON ws_tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_tasks_priority ON ws_tasks(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_tasks_created ON ws_tasks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_projects_status ON ws_projects(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_projects_priority ON ws_projects(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_milestones_project ON ws_milestones(project_id)")
            conn.commit()
        logger.info("WorkspaceStore tables verified at %s", self.db_path)

    # ─── Projects ─────────────────────────────────────────────────

    def save_project(self, project: Project) -> None:
        """Save or update a project."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ws_projects
                (project_id, name, description, status, priority, created_at, updated_at, deadline, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.project_id,
                    project.name,
                    project.description,
                    project.status,
                    project.priority,
                    project.created_at,
                    project.updated_at,
                    project.deadline,
                    json.dumps(project.tags),
                ),
            )
            conn.commit()
        logger.debug("Saved project: %s (%s)", project.name, project.project_id)

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM ws_projects WHERE project_id = ?", (project_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_project(row)

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        """List projects, optionally filtered by status."""
        with self._get_connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM ws_projects WHERE status = ? ORDER BY updated_at DESC",
                    (status,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM ws_projects ORDER BY updated_at DESC"
                )
            return [self._row_to_project(row) for row in cursor.fetchall()]

    def delete_project(self, project_id: str) -> bool:
        """Delete a project and its tasks/milestones."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM ws_tasks WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM ws_milestones WHERE project_id = ?", (project_id,))
            cursor = conn.execute("DELETE FROM ws_projects WHERE project_id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        """Convert a database row to a Project."""
        return Project(
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"] or "",
            status=row["status"],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            deadline=row["deadline"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    # ─── Tasks ────────────────────────────────────────────────────

    def save_task(self, task: Task) -> None:
        """Save or update a task."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ws_tasks
                (task_id, project_id, title, description, status, priority, depends_on,
                 estimated_effort, assigned_agents, related_episode_ids, related_memory_keys,
                 created_at, completed_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.project_id,
                    task.title,
                    task.description,
                    task.status,
                    task.priority,
                    json.dumps(task.depends_on),
                    task.estimated_effort,
                    json.dumps(task.assigned_agents),
                    json.dumps(task.related_episode_ids),
                    json.dumps(task.related_memory_keys),
                    task.created_at,
                    task.completed_at,
                    json.dumps(task.tags),
                ),
            )
            conn.commit()
        logger.debug("Saved task: %s (%s)", task.title, task.task_id)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM ws_tasks WHERE task_id = ?", (task_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_task(row)

    def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        query = "SELECT * FROM ws_tasks WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_task(row) for row in cursor.fetchall()]

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM ws_tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a Task."""
        return Task(
            task_id=row["task_id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"] or "",
            status=row["status"],
            priority=row["priority"],
            depends_on=json.loads(row["depends_on"]) if row["depends_on"] else [],
            estimated_effort=row["estimated_effort"] or "medium",
            assigned_agents=json.loads(row["assigned_agents"]) if row["assigned_agents"] else [],
            related_episode_ids=json.loads(row["related_episode_ids"]) if row["related_episode_ids"] else [],
            related_memory_keys=json.loads(row["related_memory_keys"]) if row["related_memory_keys"] else [],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    # ─── Milestones ───────────────────────────────────────────────

    def save_milestone(self, milestone: Milestone) -> None:
        """Save or update a milestone."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ws_milestones
                (milestone_id, project_id, name, description, task_ids, status, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    milestone.milestone_id,
                    milestone.project_id,
                    milestone.name,
                    milestone.description,
                    json.dumps(milestone.task_ids),
                    milestone.status,
                    milestone.created_at,
                    milestone.completed_at,
                ),
            )
            conn.commit()
        logger.debug("Saved milestone: %s (%s)", milestone.name, milestone.milestone_id)

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """Get a milestone by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM ws_milestones WHERE milestone_id = ?", (milestone_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_milestone(row)

    def list_milestones(self, project_id: Optional[str] = None) -> List[Milestone]:
        """List milestones, optionally filtered by project."""
        with self._get_connection() as conn:
            if project_id:
                cursor = conn.execute(
                    "SELECT * FROM ws_milestones WHERE project_id = ? ORDER BY created_at",
                    (project_id,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM ws_milestones ORDER BY created_at"
                )
            return [self._row_to_milestone(row) for row in cursor.fetchall()]

    def delete_milestone(self, milestone_id: str) -> bool:
        """Delete a milestone."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM ws_milestones WHERE milestone_id = ?", (milestone_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_milestone(self, row: sqlite3.Row) -> Milestone:
        """Convert a database row to a Milestone."""
        return Milestone(
            milestone_id=row["milestone_id"],
            project_id=row["project_id"],
            name=row["name"],
            description=row["description"] or "",
            task_ids=json.loads(row["task_ids"]) if row["task_ids"] else [],
            status=row["status"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )
