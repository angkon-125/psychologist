"""
Cognitive Workspace — ZARA Phase 5

Persistent project & task management with dependency tracking,
milestone grouping, progress calculation, and search.
"""

from .schemas import Project, Task, Milestone, ProgressReport, WorkspaceSummaryData
from .workspace_store import WorkspaceStore
from .project_manager import ProjectManager
from .task_manager import TaskManager
from .dependency_graph import DependencyGraph
from .milestone_tracker import MilestoneTracker
from .progress_engine import ProgressEngine
from .workspace_search import WorkspaceSearch
from .workspace_summary import WorkspaceSummaryBuilder
from .workspace_manager import WorkspaceManager

__all__ = [
    "Project",
    "Task",
    "Milestone",
    "ProgressReport",
    "WorkspaceSummaryData",
    "WorkspaceStore",
    "ProjectManager",
    "TaskManager",
    "DependencyGraph",
    "MilestoneTracker",
    "ProgressEngine",
    "WorkspaceSearch",
    "WorkspaceSummaryBuilder",
    "WorkspaceManager",
]
