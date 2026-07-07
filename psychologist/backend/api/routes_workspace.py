"""
Workspace Routes Blueprint

Provides REST API endpoints for the Cognitive Workspace:
projects, tasks, milestones, progress, search, and blocked tasks.
"""

import logging
from flask import Blueprint, request, jsonify
from .shared import orchestrator

logger = logging.getLogger("zara.api.routes_workspace")

workspace_bp = Blueprint("workspace_bp", __name__)


def _get_workspace_manager():
    """Lazy-init workspace manager on the orchestrator."""
    if not hasattr(orchestrator, '_workspace_manager'):
        try:
            from backend.workspace import WorkspaceManager
            from backend.config import config
            orchestrator._workspace_manager = WorkspaceManager(
                db_path=config.MEMORY_DB_PATH
            )
        except Exception as e:
            logger.error("Failed to initialize WorkspaceManager: %s", e)
            return None
    return orchestrator._workspace_manager


# ─── Summary ─────────────────────────────────────────────────────

@workspace_bp.route("/api/workspace", methods=["GET"])
def workspace_summary():
    """Full workspace summary for the dashboard widget."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    try:
        summary = wm.get_summary()
        return jsonify({"success": True, **summary.to_dict()})
    except Exception as e:
        logger.error("workspace_summary error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Projects ────────────────────────────────────────────────────

@workspace_bp.route("/api/workspace/projects", methods=["GET"])
def list_projects():
    """List projects with optional status filter."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    status = request.args.get("status")
    projects = wm.list_projects(status=status)
    return jsonify({
        "success": True,
        "projects": [p.to_dict() for p in projects],
        "count": len(projects),
    })


@workspace_bp.route("/api/workspace/project", methods=["POST"])
def create_project():
    """Create a new project."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400
    try:
        project = wm.create_project(
            name=name,
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
            deadline=data.get("deadline"),
            tags=data.get("tags", []),
        )
        return jsonify({"success": True, "project": project.to_dict()})
    except Exception as e:
        logger.error("create_project error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_bp.route("/api/workspace/project/<project_id>", methods=["PATCH"])
def update_project(project_id):
    """Update a project (archive, resume, rename, etc.)."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    try:
        if action == "archive":
            result = wm.archive_project(project_id)
        elif action == "resume":
            result = wm.resume_project(project_id)
        elif action == "rename":
            new_name = data.get("name", "").strip()
            if not new_name:
                return jsonify({"success": False, "error": "name is required"}), 400
            result = wm.rename_project(project_id, new_name)
        else:
            return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400

        if result:
            return jsonify({"success": True, "project": result.to_dict()})
        return jsonify({"success": False, "error": "Project not found"}), 404
    except Exception as e:
        logger.error("update_project error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_bp.route("/api/workspace/project/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project and its tasks/milestones."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    result = wm.delete_project(project_id)
    if result:
        return jsonify({"success": True, "deleted": project_id})
    return jsonify({"success": False, "error": "Project not found"}), 404


# ─── Tasks ───────────────────────────────────────────────────────

@workspace_bp.route("/api/workspace/tasks", methods=["GET"])
def list_tasks():
    """List tasks with optional project_id and status filters."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    project_id = request.args.get("project_id")
    status = request.args.get("status")
    tasks = wm.list_tasks(project_id=project_id, status=status)
    return jsonify({
        "success": True,
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    })


@workspace_bp.route("/api/workspace/task", methods=["POST"])
def create_task():
    """Create a new task."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    data = request.get_json(silent=True) or {}
    project_id = data.get("project_id", "").strip()
    title = data.get("title", "").strip()
    if not project_id or not title:
        return jsonify({"success": False, "error": "project_id and title are required"}), 400
    try:
        task = wm.create_task(
            project_id=project_id,
            title=title,
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
            depends_on=data.get("depends_on", []),
            estimated_effort=data.get("estimated_effort", "medium"),
            assigned_agents=data.get("assigned_agents", []),
            tags=data.get("tags", []),
        )
        return jsonify({"success": True, "task": task.to_dict()})
    except Exception as e:
        logger.error("create_task error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_bp.route("/api/workspace/task/<task_id>", methods=["PATCH"])
def update_task(task_id):
    """Update a task (status, priority, etc.)."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    try:
        if action == "complete":
            result = wm.complete_task(task_id)
        elif action == "start":
            result = wm.start_task(task_id)
        elif action == "block":
            reason = data.get("reason", "")
            result = wm.block_task(task_id, reason=reason)
        else:
            # Generic field update
            fields = {}
            for key in ("title", "description", "priority", "status", "estimated_effort", "tags"):
                if key in data:
                    fields[key] = data[key]
            if not fields:
                return jsonify({"success": False, "error": "No fields to update"}), 400
            result = wm.update_task(task_id, **fields)

        if result:
            return jsonify({"success": True, "task": result.to_dict()})
        return jsonify({"success": False, "error": "Task not found"}), 404
    except Exception as e:
        logger.error("update_task error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@workspace_bp.route("/api/workspace/task/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    result = wm.delete_task(task_id)
    if result:
        return jsonify({"success": True, "deleted": task_id})
    return jsonify({"success": False, "error": "Task not found"}), 404


# ─── Progress ────────────────────────────────────────────────────

@workspace_bp.route("/api/workspace/progress/<project_id>", methods=["GET"])
def get_progress(project_id):
    """Progress report for a project."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    try:
        report = wm.calculate_progress(project_id)
        return jsonify({"success": True, **report.to_dict()})
    except Exception as e:
        logger.error("get_progress error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Search ──────────────────────────────────────────────────────

@workspace_bp.route("/api/workspace/search", methods=["GET"])
def search_workspace():
    """Search across workspace."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    query = request.args.get("q", "")
    if not query:
        return jsonify({"success": True, "projects": [], "tasks": [], "milestones": []})
    try:
        results = wm.search(query)
        return jsonify({"success": True, **results})
    except Exception as e:
        logger.error("search_workspace error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Milestones ──────────────────────────────────────────────────

@workspace_bp.route("/api/workspace/milestones", methods=["GET"])
def list_milestones():
    """List milestones with optional project_id filter."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    project_id = request.args.get("project_id")
    milestones = wm.list_milestones(project_id=project_id)
    return jsonify({
        "success": True,
        "milestones": [m.to_dict() for m in milestones],
        "count": len(milestones),
    })


@workspace_bp.route("/api/workspace/milestone", methods=["POST"])
def create_milestone():
    """Create a new milestone."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    data = request.get_json(silent=True) or {}
    project_id = data.get("project_id", "").strip()
    name = data.get("name", "").strip()
    if not project_id or not name:
        return jsonify({"success": False, "error": "project_id and name are required"}), 400
    try:
        milestone = wm.create_milestone(
            project_id=project_id,
            name=name,
            description=data.get("description", ""),
            task_ids=data.get("task_ids", []),
        )
        return jsonify({"success": True, "milestone": milestone.to_dict()})
    except Exception as e:
        logger.error("create_milestone error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Blocked Tasks ───────────────────────────────────────────────

@workspace_bp.route("/api/workspace/blocked", methods=["GET"])
def blocked_tasks():
    """Blocked tasks across all projects."""
    wm = _get_workspace_manager()
    if not wm:
        return jsonify({"success": False, "error": "Workspace not initialized"}), 503
    try:
        tasks = wm.list_tasks(status="blocked")
        return jsonify({
            "success": True,
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        })
    except Exception as e:
        logger.error("blocked_tasks error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
