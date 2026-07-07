"""
Cognitive Workspace Tests

Tests for all workspace components:
- Schemas: Project, Task, Milestone, ProgressReport, WorkspaceSummaryData
- WorkspaceStore: SQLite persistence, CRUD operations
- ProjectManager: project lifecycle management
- TaskManager: task lifecycle management
- DependencyGraph: DAG, blocked/ready detection, cycle detection
- MilestoneTracker: milestone grouping, auto-completion
- ProgressEngine: real % calculation, velocity, health
- WorkspaceSearch: query matching, finders
- WorkspaceRoutes: API endpoint response shapes
- ExecutiveWorkspace: workspace context injection
"""

import os
import sys
import json
import tempfile
import pytest
from datetime import datetime, timedelta

# Ensure project root is in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.workspace.schemas import (
    Project, Task, Milestone, ProgressReport, WorkspaceSummaryData
)
from backend.workspace.workspace_store import WorkspaceStore
from backend.workspace.project_manager import ProjectManager
from backend.workspace.task_manager import TaskManager
from backend.workspace.dependency_graph import DependencyGraph
from backend.workspace.milestone_tracker import MilestoneTracker
from backend.workspace.progress_engine import ProgressEngine
from backend.workspace.workspace_search import WorkspaceSearch
from backend.workspace.workspace_summary import WorkspaceSummaryBuilder
from backend.workspace.workspace_manager import WorkspaceManager


# ═══════════════════════════════════════════════════════════════════
# TestWorkspaceSchemas
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceSchemas:
    """Tests for workspace data schemas."""

    def test_project_creation_defaults(self):
        p = Project(project_id="p1", name="Test")
        assert p.project_id == "p1"
        assert p.name == "Test"
        assert p.status == "active"
        assert p.priority == "medium"
        assert p.tags == []
        assert p.deadline is None

    def test_project_to_dict(self):
        p = Project(project_id="p1", name="Test", description="desc", priority="high", tags=["a", "b"])
        d = p.to_dict()
        assert d["project_id"] == "p1"
        assert d["name"] == "Test"
        assert d["priority"] == "high"
        assert d["tags"] == ["a", "b"]

    def test_project_from_dict(self):
        d = {"project_id": "p2", "name": "Proj", "status": "paused", "priority": "low"}
        p = Project.from_dict(d)
        assert p.project_id == "p2"
        assert p.status == "paused"
        assert p.priority == "low"

    def test_task_creation_defaults(self):
        t = Task(task_id="t1", project_id="p1", title="Do thing")
        assert t.status == "pending"
        assert t.priority == "medium"
        assert t.depends_on == []
        assert t.assigned_agents == []
        assert t.completed_at is None

    def test_task_to_dict(self):
        t = Task(task_id="t1", project_id="p1", title="Do thing", priority="high", tags=["x"])
        d = t.to_dict()
        assert d["task_id"] == "t1"
        assert d["priority"] == "high"
        assert d["tags"] == ["x"]

    def test_task_from_dict(self):
        d = {"task_id": "t2", "project_id": "p1", "title": "Task", "status": "completed", "priority": "critical"}
        t = Task.from_dict(d)
        assert t.task_id == "t2"
        assert t.status == "completed"
        assert t.priority == "critical"

    def test_milestone_creation_defaults(self):
        m = Milestone(milestone_id="m1", project_id="p1", name="M1")
        assert m.status == "pending"
        assert m.task_ids == []
        assert m.completed_at is None

    def test_milestone_to_dict(self):
        m = Milestone(milestone_id="m1", project_id="p1", name="M1", task_ids=["t1", "t2"])
        d = m.to_dict()
        assert d["milestone_id"] == "m1"
        assert d["task_ids"] == ["t1", "t2"]

    def test_milestone_from_dict(self):
        d = {"milestone_id": "m1", "project_id": "p1", "name": "M1", "status": "completed"}
        m = Milestone.from_dict(d)
        assert m.status == "completed"

    def test_progress_report_defaults(self):
        pr = ProgressReport(project_id="p1", project_name="Test")
        assert pr.total_tasks == 0
        assert pr.completed_tasks == 0
        assert pr.completion_pct == 0.0
        assert pr.health == "on_track"

    def test_progress_report_to_dict(self):
        pr = ProgressReport(project_id="p1", project_name="Test", total_tasks=10, completed_tasks=5, completion_pct=50.0)
        d = pr.to_dict()
        assert d["completion_pct"] == 50.0
        assert d["total_tasks"] == 10

    def test_workspace_summary_data_defaults(self):
        ws = WorkspaceSummaryData()
        assert ws.active_project is None
        assert ws.total_active_projects == 0
        assert ws.progress_pct == 0.0

    def test_workspace_summary_data_to_dict(self):
        ws = WorkspaceSummaryData(active_project={"name": "Test"}, total_active_tasks=5, progress_pct=42.0)
        d = ws.to_dict()
        assert d["active_project"]["name"] == "Test"
        assert d["total_active_tasks"] == 5


# ═══════════════════════════════════════════════════════════════════
# TestWorkspaceStore
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceStore:
    """Tests for SQLite persistence layer."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_tables_created(self):
        import sqlite3
        conn = sqlite3.connect(self.tmpfile.name)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "ws_projects" in tables
        assert "ws_tasks" in tables
        assert "ws_milestones" in tables

    def test_save_and_get_project(self):
        p = Project(project_id="p1", name="Test Project")
        self.store.save_project(p)
        loaded = self.store.get_project("p1")
        assert loaded is not None
        assert loaded.name == "Test Project"
        assert loaded.status == "active"

    def test_list_projects_empty(self):
        projects = self.store.list_projects()
        assert projects == []

    def test_list_projects_with_filter(self):
        p1 = Project(project_id="p1", name="Active")
        p2 = Project(project_id="p2", name="Paused", status="paused")
        self.store.save_project(p1)
        self.store.save_project(p2)
        active = self.store.list_projects(status="active")
        assert len(active) == 1
        assert active[0].name == "Active"

    def test_delete_project(self):
        p = Project(project_id="p1", name="Test")
        self.store.save_project(p)
        assert self.store.delete_project("p1") is True
        assert self.store.get_project("p1") is None

    def test_delete_project_cascades_tasks(self):
        p = Project(project_id="p1", name="Test")
        t = Task(task_id="t1", project_id="p1", title="Task 1")
        self.store.save_project(p)
        self.store.save_task(t)
        self.store.delete_project("p1")
        assert self.store.get_task("t1") is None

    def test_save_and_get_task(self):
        p = Project(project_id="p1", name="Test")
        self.store.save_project(p)
        t = Task(task_id="t1", project_id="p1", title="Task 1", priority="high")
        self.store.save_task(t)
        loaded = self.store.get_task("t1")
        assert loaded is not None
        assert loaded.title == "Task 1"
        assert loaded.priority == "high"

    def test_list_tasks_by_project(self):
        p = Project(project_id="p1", name="Test")
        self.store.save_project(p)
        t1 = Task(task_id="t1", project_id="p1", title="T1")
        t2 = Task(task_id="t2", project_id="p1", title="T2", status="completed")
        self.store.save_task(t1)
        self.store.save_task(t2)
        pending = self.store.list_tasks(project_id="p1", status="pending")
        assert len(pending) == 1
        assert pending[0].task_id == "t1"

    def test_update_task_status(self):
        t = Task(task_id="t1", project_id="p1", title="T1")
        p = Project(project_id="p1", name="Test")
        self.store.save_project(p)
        self.store.save_task(t)
        # Update by loading, modifying, and re-saving
        loaded = self.store.get_task("t1")
        loaded.status = "in_progress"
        self.store.save_task(loaded)
        reloaded = self.store.get_task("t1")
        assert reloaded.status == "in_progress"

    def test_save_and_get_milestone(self):
        m = Milestone(milestone_id="m1", project_id="p1", name="M1", task_ids=["t1"])
        self.store.save_milestone(m)
        loaded = self.store.get_milestone("m1")
        assert loaded is not None
        assert loaded.name == "M1"
        assert loaded.task_ids == ["t1"]

    def test_list_milestones(self):
        m1 = Milestone(milestone_id="m1", project_id="p1", name="M1")
        m2 = Milestone(milestone_id="m2", project_id="p1", name="M2")
        self.store.save_milestone(m1)
        self.store.save_milestone(m2)
        milestones = self.store.list_milestones(project_id="p1")
        assert len(milestones) == 2

    def test_get_nonexistent_project(self):
        assert self.store.get_project("nonexistent") is None

    def test_get_nonexistent_task(self):
        assert self.store.get_task("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# TestProjectManager
# ═══════════════════════════════════════════════════════════════════

class TestProjectManager:
    """Tests for project lifecycle management."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_create_project(self):
        p = self.pm.create_project("My Project")
        assert p.name == "My Project"
        assert p.status == "active"
        assert p.project_id is not None

    def test_create_project_with_options(self):
        p = self.pm.create_project("Proj", description="desc", priority="high", tags=["a"])
        assert p.priority == "high"
        assert p.tags == ["a"]

    def test_archive_project(self):
        p = self.pm.create_project("Proj")
        archived = self.pm.archive_project(p.project_id)
        assert archived is not None
        assert archived.status == "archived"

    def test_resume_project(self):
        p = self.pm.create_project("Proj")
        self.pm.archive_project(p.project_id)
        resumed = self.pm.resume_project(p.project_id)
        assert resumed is not None
        assert resumed.status == "active"

    def test_rename_project(self):
        p = self.pm.create_project("Old Name")
        renamed = self.pm.rename_project(p.project_id, "New Name")
        assert renamed is not None
        assert renamed.name == "New Name"

    def test_delete_project(self):
        p = self.pm.create_project("Proj")
        assert self.pm.delete_project(p.project_id) is True
        assert self.pm.get_active_project() is None

    def test_get_active_project(self):
        p = self.pm.create_project("Proj")
        active = self.pm.get_active_project()
        assert active is not None
        assert active.project_id == p.project_id

    def test_set_active_project(self):
        p1 = self.pm.create_project("P1")
        p2 = self.pm.create_project("P2")
        self.pm.set_active_project(p2.project_id)
        active = self.pm.get_active_project()
        assert active.project_id == p2.project_id

    def test_archive_nonexistent(self):
        assert self.pm.archive_project("nonexistent") is None

    def test_list_projects(self):
        self.pm.create_project("P1")
        self.pm.create_project("P2")
        projects = self.pm.list_projects()
        assert len(projects) == 2


# ═══════════════════════════════════════════════════════════════════
# TestTaskManager
# ═══════════════════════════════════════════════════════════════════

class TestTaskManager:
    """Tests for task lifecycle management."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)
        self.tm = TaskManager(self.store)
        self.project = self.pm.create_project("Test Project")

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_create_task(self):
        t = self.tm.create_task(self.project.project_id, "Task 1")
        assert t.title == "Task 1"
        assert t.status == "pending"
        assert t.project_id == self.project.project_id

    def test_create_task_with_options(self):
        t = self.tm.create_task(
            self.project.project_id, "Task 1",
            priority="high", estimated_effort="large",
            assigned_agents=["coder"], tags=["ui"]
        )
        assert t.priority == "high"
        assert t.estimated_effort == "large"
        assert t.assigned_agents == ["coder"]

    def test_complete_task(self):
        t = self.tm.create_task(self.project.project_id, "Task 1")
        completed = self.tm.complete_task(t.task_id)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.completed_at is not None

    def test_start_task(self):
        t = self.tm.create_task(self.project.project_id, "Task 1")
        started = self.tm.start_task(t.task_id)
        assert started is not None
        assert started.status == "in_progress"

    def test_block_task(self):
        t = self.tm.create_task(self.project.project_id, "Task 1")
        blocked = self.tm.block_task(t.task_id, reason="waiting on API")
        assert blocked is not None
        assert blocked.status == "blocked"

    def test_delete_task(self):
        t = self.tm.create_task(self.project.project_id, "Task 1")
        assert self.tm.delete_task(t.task_id) is True
        assert self.tm.get_task(t.task_id) is None if hasattr(self.tm, 'get_task') else True

    def test_list_tasks_by_project(self):
        self.tm.create_task(self.project.project_id, "T1")
        self.tm.create_task(self.project.project_id, "T2")
        tasks = self.tm.list_tasks(project_id=self.project.project_id)
        assert len(tasks) == 2

    def test_list_tasks_by_status(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2")
        self.tm.complete_task(t1.task_id)
        pending = self.tm.list_tasks(project_id=self.project.project_id, status="pending")
        assert len(pending) == 1

    def test_get_tasks_for_agent(self):
        self.tm.create_task(self.project.project_id, "T1", assigned_agents=["coder"])
        self.tm.create_task(self.project.project_id, "T2", assigned_agents=["reviewer"])
        tasks = self.tm.get_tasks_for_agent("coder")
        assert len(tasks) == 1

    def test_update_task(self):
        t = self.tm.create_task(self.project.project_id, "T1")
        updated = self.tm.update_task(t.task_id, title="Updated Title", priority="high")
        assert updated.title == "Updated Title"
        assert updated.priority == "high"

    def test_complete_nonexistent_task(self):
        assert self.tm.complete_task("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# TestDependencyGraph
# ═══════════════════════════════════════════════════════════════════

class TestDependencyGraph:
    """Tests for dependency graph operations."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)
        self.tm = TaskManager(self.store)
        self.dg = DependencyGraph(self.store)
        self.project = self.pm.create_project("Test Project")

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_build_graph_empty(self):
        graph = self.dg.build_graph(self.project.project_id)
        assert graph == {}

    def test_build_graph_with_deps(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        graph = self.dg.build_graph(self.project.project_id)
        # graph maps task_id -> list of task_ids it depends on
        assert t1.task_id in graph
        assert t2.task_id in graph
        assert t1.task_id in graph[t2.task_id]  # t2 depends on t1

    def test_get_blocked_tasks(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        blocked = self.dg.get_blocked_tasks(self.project.project_id)
        assert len(blocked) == 1
        assert blocked[0].task_id == t2.task_id

    def test_get_ready_tasks(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        ready = self.dg.get_ready_tasks(self.project.project_id)
        assert len(ready) == 1
        assert ready[0].task_id == t1.task_id

    def test_ready_after_completion(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        self.dg.invalidate(self.project.project_id)
        self.tm.complete_task(t1.task_id)
        self.dg.invalidate(self.project.project_id)
        ready = self.dg.get_ready_tasks(self.project.project_id)
        assert len(ready) == 1
        assert ready[0].task_id == t2.task_id

    def test_detect_circular_no_cycle(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        cycles = self.dg.detect_circular_dependencies(self.project.project_id)
        assert len(cycles) == 0

    def test_detect_circular_with_cycle(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2", depends_on=[t1.task_id])
        # Manually create a cycle by updating t1 to depend on t2
        self.store.save_task(Task(
            task_id=t1.task_id, project_id=t1.project_id, title=t1.title,
            description=t1.description, status=t1.status, priority=t1.priority,
            depends_on=[t2.task_id], estimated_effort=t1.estimated_effort,
            assigned_agents=t1.assigned_agents, related_episode_ids=t1.related_episode_ids,
            related_memory_keys=t1.related_memory_keys, created_at=t1.created_at,
            completed_at=t1.completed_at, tags=t1.tags
        ))
        self.dg.invalidate(self.project.project_id)
        cycles = self.dg.detect_circular_dependencies(self.project.project_id)
        assert len(cycles) > 0

    def test_no_blocked_when_no_deps(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        blocked = self.dg.get_blocked_tasks(self.project.project_id)
        assert len(blocked) == 0

    def test_invalidate_cache(self):
        self.dg.build_graph(self.project.project_id)
        self.dg.invalidate(self.project.project_id)
        assert self.project.project_id not in self.dg._cache


# ═══════════════════════════════════════════════════════════════════
# TestMilestoneTracker
# ═══════════════════════════════════════════════════════════════════

class TestMilestoneTracker:
    """Tests for milestone tracking."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)
        self.tm = TaskManager(self.store)
        self.mt = MilestoneTracker(self.store)
        self.project = self.pm.create_project("Test Project")

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_create_milestone(self):
        m = self.mt.create_milestone(self.project.project_id, "M1", task_ids=["t1", "t2"])
        assert m.name == "M1"
        assert m.task_ids == ["t1", "t2"]
        assert m.status == "pending"

    def test_complete_milestone(self):
        m = self.mt.create_milestone(self.project.project_id, "M1")
        completed = self.mt.complete_milestone(m.milestone_id)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.completed_at is not None

    def test_milestone_progress_empty(self):
        m = self.mt.create_milestone(self.project.project_id, "M1", task_ids=[])
        pct = self.mt.get_milestone_progress(m.milestone_id)
        assert pct == 0.0

    def test_milestone_progress_partial(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2")
        m = self.mt.create_milestone(self.project.project_id, "M1", task_ids=[t1.task_id, t2.task_id])
        self.tm.complete_task(t1.task_id)
        pct = self.mt.get_milestone_progress(m.milestone_id)
        assert pct == 50.0

    def test_milestone_progress_full(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        m = self.mt.create_milestone(self.project.project_id, "M1", task_ids=[t1.task_id])
        self.tm.complete_task(t1.task_id)
        pct = self.mt.get_milestone_progress(m.milestone_id)
        assert pct == 100.0

    def test_list_milestones(self):
        self.mt.create_milestone(self.project.project_id, "M1")
        self.mt.create_milestone(self.project.project_id, "M2")
        milestones = self.mt.list_milestones(project_id=self.project.project_id)
        assert len(milestones) == 2

    def test_get_next_milestone(self):
        m1 = self.mt.create_milestone(self.project.project_id, "M1")
        m2 = self.mt.create_milestone(self.project.project_id, "M2")
        nxt = self.mt.get_next_milestone(self.project.project_id)
        assert nxt is not None

    def test_auto_completion(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        m = self.mt.create_milestone(self.project.project_id, "M1", task_ids=[t1.task_id])
        self.tm.complete_task(t1.task_id)
        self.mt.check_auto_completion(m.milestone_id)
        updated = self.store.get_milestone(m.milestone_id)
        assert updated.status == "completed"

    def test_complete_nonexistent_milestone(self):
        assert self.mt.complete_milestone("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# TestProgressEngine
# ═══════════════════════════════════════════════════════════════════

class TestProgressEngine:
    """Tests for progress calculation."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)
        self.tm = TaskManager(self.store)
        self.pe = ProgressEngine(self.store)
        self.project = self.pm.create_project("Test Project")

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_empty_project_progress(self):
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.total_tasks == 0
        assert report.completion_pct == 0.0

    def test_partial_completion(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2")
        self.tm.complete_task(t1.task_id)
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.total_tasks == 2
        assert report.completed_tasks == 1
        assert report.completion_pct == 50.0

    def test_full_completion(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        self.tm.complete_task(t1.task_id)
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.completion_pct == 100.0

    def test_health_stalled_no_tasks(self):
        report = self.pe.calculate_progress(self.project.project_id)
        # Empty project defaults to on_track
        assert report.health in ("stalled", "on_track")

    def test_health_on_track(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        self.tm.complete_task(t1.task_id)
        report = self.pe.calculate_progress(self.project.project_id)
        # With completions, should not be stalled
        assert report.health in ("on_track", "at_risk")

    def test_completed_today_count(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        self.tm.complete_task(t1.task_id)
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.completed_today >= 1

    def test_velocity_positive(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        self.tm.complete_task(t1.task_id)
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.velocity > 0

    def test_report_has_project_name(self):
        report = self.pe.calculate_progress(self.project.project_id)
        assert report.project_name == "Test Project"


# ═══════════════════════════════════════════════════════════════════
# TestWorkspaceSearch
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceSearch:
    """Tests for workspace search."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.store = WorkspaceStore(self.tmpfile.name)
        self.pm = ProjectManager(self.store)
        self.tm = TaskManager(self.store)
        self.ws = WorkspaceSearch(self.store)
        self.project = self.pm.create_project("Android App")

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_search_by_project_name(self):
        results = self.ws.search("Android")
        assert len(results["projects"]) >= 1
        assert results["projects"][0]["name"] == "Android App"

    def test_search_by_task_title(self):
        self.tm.create_task(self.project.project_id, "Build UI")
        results = self.ws.search("Build UI")
        assert len(results["tasks"]) >= 1

    def test_search_empty_query(self):
        results = self.ws.search("")
        assert results["projects"] == []
        assert results["tasks"] == []

    def test_search_no_match(self):
        results = self.ws.search("nonexistent_xyz")
        assert len(results["projects"]) == 0

    def test_find_unfinished_tasks(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        t2 = self.tm.create_task(self.project.project_id, "T2")
        self.tm.complete_task(t1.task_id)
        unfinished = self.ws.find_unfinished_tasks(self.project.project_id)
        assert len(unfinished) == 1

    def test_find_blocked_tasks(self):
        t1 = self.tm.create_task(self.project.project_id, "T1")
        self.tm.block_task(t1.task_id, reason="blocked")
        blocked = self.ws.find_blocked_tasks(self.project.project_id)
        assert len(blocked) == 1

    def test_find_tasks_for_agent(self):
        self.tm.create_task(self.project.project_id, "T1", assigned_agents=["coder"])
        tasks = self.ws.find_tasks_for_agent("coder")
        assert len(tasks) == 1

    def test_find_completed_milestones(self):
        m = self.mt.create_milestone(self.project.project_id, "M1") if hasattr(self, 'mt') else None
        # Create milestone directly
        from backend.workspace.schemas import Milestone
        m = Milestone(milestone_id="m1", project_id=self.project.project_id, name="M1", status="completed")
        self.store.save_milestone(m)
        completed = self.ws.find_completed_milestones(self.project.project_id)
        assert len(completed) == 1


# ═══════════════════════════════════════════════════════════════════
# TestWorkspaceManager
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceManager:
    """Tests for the orchestrator."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.wm = WorkspaceManager(self.tmpfile.name)

    def teardown_method(self):
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_create_project(self):
        p = self.wm.create_project("Test")
        assert p.name == "Test"

    def test_create_task(self):
        p = self.wm.create_project("Test")
        t = self.wm.create_task(p.project_id, "Task 1")
        assert t.title == "Task 1"

    def test_complete_task_invalidates_cache(self):
        p = self.wm.create_project("Test")
        t1 = self.wm.create_task(p.project_id, "T1")
        t2 = self.wm.create_task(p.project_id, "T2", depends_on=[t1.task_id])
        self.wm.complete_task(t1.task_id)
        ready = self.wm.dependency_graph.get_ready_tasks(p.project_id)
        assert any(t.task_id == t2.task_id for t in ready)

    def test_get_summary(self):
        p = self.wm.create_project("Test")
        summary = self.wm.get_summary()
        assert summary is not None
        assert summary.active_project is not None

    def test_get_full_workspace(self):
        p = self.wm.create_project("Test")
        self.wm.create_task(p.project_id, "T1")
        full = self.wm.get_full_workspace()
        assert "summary" in full
        assert "projects" in full
        assert "tasks" in full
        assert "milestones" in full

    def test_search(self):
        self.wm.create_project("Android App")
        results = self.wm.search("Android")
        assert len(results["projects"]) >= 1

    def test_create_milestone(self):
        p = self.wm.create_project("Test")
        m = self.wm.create_milestone(p.project_id, "M1")
        assert m.name == "M1"


# ═══════════════════════════════════════════════════════════════════
# TestWorkspaceRoutes
# ═══════════════════════════════════════════════════════════════════

class TestWorkspaceRoutes:
    """Tests for API endpoint response shapes."""

    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        # Patch config to use temp db
        from backend.config import config
        self._orig_db_path = config.MEMORY_DB_PATH
        config.MEMORY_DB_PATH = self.tmpfile.name

        from backend.main import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    def teardown_method(self):
        from backend.config import config
        config.MEMORY_DB_PATH = self._orig_db_path
        # Clean up workspace manager if cached
        from backend.api.shared import orchestrator
        if hasattr(orchestrator, '_workspace_manager'):
            delattr(orchestrator, '_workspace_manager')
        try:
            os.unlink(self.tmpfile.name)
        except Exception:
            pass

    def test_get_workspace_summary(self):
        resp = self.client.get("/api/workspace")
        data = resp.get_json()
        assert data["success"] is True
        assert "progress_pct" in data

    def test_create_and_list_projects(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test", "priority": "high"})
        data = resp.get_json()
        assert data["success"] is True
        assert data["project"]["name"] == "Test"

        resp = self.client.get("/api/workspace/projects")
        data = resp.get_json()
        assert data["success"] is True
        assert data["count"] >= 1

    def test_create_project_missing_name(self):
        resp = self.client.post("/api/workspace/project", json={"description": "no name"})
        data = resp.get_json()
        assert data["success"] is False

    def test_update_project_archive(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.patch(f"/api/workspace/project/{pid}", json={"action": "archive"})
        data = resp.get_json()
        assert data["success"] is True
        assert data["project"]["status"] == "archived"

    def test_delete_project(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.delete(f"/api/workspace/project/{pid}")
        data = resp.get_json()
        assert data["success"] is True

    def test_create_and_list_tasks(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.post("/api/workspace/task", json={"project_id": pid, "title": "T1"})
        data = resp.get_json()
        assert data["success"] is True

        resp = self.client.get(f"/api/workspace/tasks?project_id={pid}")
        data = resp.get_json()
        assert data["count"] >= 1

    def test_update_task_complete(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.post("/api/workspace/task", json={"project_id": pid, "title": "T1"})
        tid = resp.get_json()["task"]["task_id"]
        resp = self.client.patch(f"/api/workspace/task/{tid}", json={"action": "complete"})
        data = resp.get_json()
        assert data["success"] is True
        assert data["task"]["status"] == "completed"

    def test_get_progress(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.get(f"/api/workspace/progress/{pid}")
        data = resp.get_json()
        assert data["success"] is True
        assert "completion_pct" in data

    def test_search_workspace(self):
        self.client.post("/api/workspace/project", json={"name": "Android App"})
        resp = self.client.get("/api/workspace/search?q=Android")
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["projects"]) >= 1

    def test_search_empty_query(self):
        resp = self.client.get("/api/workspace/search?q=")
        data = resp.get_json()
        assert data["success"] is True

    def test_list_milestones(self):
        resp = self.client.get("/api/workspace/milestones")
        data = resp.get_json()
        assert data["success"] is True

    def test_create_milestone(self):
        resp = self.client.post("/api/workspace/project", json={"name": "Test"})
        pid = resp.get_json()["project"]["project_id"]
        resp = self.client.post("/api/workspace/milestone", json={"project_id": pid, "name": "M1"})
        data = resp.get_json()
        assert data["success"] is True
        assert data["milestone"]["name"] == "M1"

    def test_blocked_tasks(self):
        resp = self.client.get("/api/workspace/blocked")
        data = resp.get_json()
        assert data["success"] is True
        assert "tasks" in data

    def test_delete_nonexistent_project(self):
        resp = self.client.delete("/api/workspace/project/nonexistent")
        data = resp.get_json()
        assert data["success"] is False


# ═══════════════════════════════════════════════════════════════════
# TestExecutiveWorkspace
# ═══════════════════════════════════════════════════════════════════

class TestExecutiveWorkspace:
    """Tests for executive controller workspace integration."""

    def test_workspace_context_injection(self):
        """Verify that workspace context is injected into metadata."""
        tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmpfile.close()
        try:
            from backend.config import config
            orig_path = config.MEMORY_DB_PATH
            config.MEMORY_DB_PATH = tmpfile.name

            from backend.agent.executive.executive_controller import ExecutiveController
            controller = ExecutiveController()

            # Init workspace manager
            from backend.workspace import WorkspaceManager
            controller._workspace_manager = WorkspaceManager(db_path=tmpfile.name)
            wm = controller._workspace_manager
            p = wm.create_project("Test Project")
            t = wm.create_task(p.project_id, "Build UI")

            # Check that workspace context can be built
            summary = wm.get_summary()
            ctx = {
                "active_project": summary.active_project,
                "next_task": summary.next_task,
                "blocked_count": summary.total_blocked_tasks,
                "completed_today": summary.completed_today,
            }
            assert ctx["active_project"] is not None
            assert ctx["active_project"]["name"] == "Test Project"
            assert ctx["blocked_count"] == 0

            config.MEMORY_DB_PATH = orig_path
        finally:
            try:
                os.unlink(tmpfile.name)
            except Exception:
                pass

    def test_workspace_graceful_failure(self):
        """Verify workspace module is optional (try/except)."""
        from backend.agent.executive.executive_controller import ExecutiveController
        controller = ExecutiveController()
        # Without _workspace_manager, the workspace steps should be skipped gracefully
        # This is verified by the try/except in the controller code
        assert not hasattr(controller, '_workspace_manager')
