"""
Episodic Memory Routes Blueprint

Provides REST API endpoints for the Timeline page and episode management.
"""

from flask import Blueprint, request, jsonify
from .shared import orchestrator

episodes_bp = Blueprint("episodes_bp", __name__)


def _get_memory_agent():
    """Get the memory agent from the orchestrator."""
    return orchestrator.specialists.get("memory")


@episodes_bp.route("/api/episodes", methods=["GET"])
def list_episodes():
    """List episodes with optional filters."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'episode_store') or not memory.episode_store:
        return jsonify({"success": False, "error": "Episodic memory not initialized"}), 503

    period = request.args.get("period", "all")
    topic = request.args.get("topic", "")
    emotion = request.args.get("emotion", "")
    limit = min(int(request.args.get("limit", 50)), 200)

    if topic:
        episodes = memory.episode_store.get_episodes_by_topic(topic, limit=limit)
    elif emotion:
        episodes = memory.episode_store.get_episodes_by_emotion(emotion, limit=limit)
    elif period != "all":
        if memory.timeline:
            episodes = memory.timeline.get_timeline(period=period)
        else:
            episodes = memory.episode_store.get_all_episodes()
    else:
        episodes = memory.episode_store.get_all_episodes()[:limit]

    return jsonify({
        "success": True,
        "episodes": [e.to_dict() for e in episodes],
        "count": len(episodes),
    })


@episodes_bp.route("/api/episodes/<episode_id>", methods=["GET"])
def get_episode(episode_id):
    """Get a single episode by ID."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'episode_store') or not memory.episode_store:
        return jsonify({"success": False, "error": "Episodic memory not initialized"}), 503

    episode = memory.episode_store.get_episode(episode_id)
    if not episode:
        return jsonify({"success": False, "error": "Episode not found"}), 404

    return jsonify({"success": True, "episode": episode.to_dict()})


@episodes_bp.route("/api/episodes/timeline", methods=["GET"])
def get_timeline():
    """Get timeline data for the frontend."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'timeline') or not memory.timeline:
        return jsonify({"success": False, "error": "Timeline not initialized"}), 503

    summary = memory.timeline.get_timeline_summary()
    return jsonify({"success": True, **summary})


@episodes_bp.route("/api/episodes/projects", methods=["GET"])
def get_projects():
    """Get episodes grouped by project/topic."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'timeline') or not memory.timeline:
        return jsonify({"success": False, "error": "Timeline not initialized"}), 503

    projects = memory.timeline.get_projects()
    result = {}
    for topic, episodes in projects.items():
        result[topic] = [e.to_dict() for e in episodes]

    return jsonify({"success": True, "projects": result})


@episodes_bp.route("/api/episodes/emotions", methods=["GET"])
def get_emotional_journey():
    """Get emotional journey data."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'timeline') or not memory.timeline:
        return jsonify({"success": False, "error": "Timeline not initialized"}), 503

    snapshots = memory.timeline.get_emotional_journey()
    return jsonify({
        "success": True,
        "journey": [s.to_dict() for s in snapshots],
    })


@episodes_bp.route("/api/episodes/pending", methods=["GET"])
def get_pending():
    """Get episodes with pending tasks."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'episode_recall') or not memory.episode_recall:
        return jsonify({"success": False, "error": "Episode recall not initialized"}), 503

    episodes = memory.episode_recall.recall_pending()
    return jsonify({
        "success": True,
        "episodes": [e.to_dict() for e in episodes],
    })


@episodes_bp.route("/api/episodes/search", methods=["GET"])
def search_episodes():
    """Search episodes by query."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'episode_recall') or not memory.episode_recall:
        return jsonify({"success": False, "error": "Episode recall not initialized"}), 503

    query = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 20)), 100)

    if not query:
        return jsonify({"success": True, "episodes": [], "query": ""})

    result = memory.episode_recall.recall_by_query(query, limit=limit)
    return jsonify({
        "success": True,
        **result.to_dict(),
    })


@episodes_bp.route("/api/episodes/<episode_id>", methods=["DELETE"])
def delete_episode(episode_id):
    """Delete an episode."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'forgetting') or not memory.forgetting:
        return jsonify({"success": False, "error": "Forgetting policy not initialized"}), 503

    result = memory.forgetting.delete_episode(memory.episode_store, episode_id)
    if result:
        return jsonify({"success": True, "deleted": episode_id})
    return jsonify({"success": False, "error": "Episode not found or locked"}), 404


@episodes_bp.route("/api/episodes/<episode_id>/lock", methods=["POST"])
def lock_episode(episode_id):
    """Lock or unlock an episode."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'episode_store') or not memory.episode_store:
        return jsonify({"success": False, "error": "Episode store not initialized"}), 503

    data = request.get_json(silent=True) or {}
    locked = data.get("locked", True)

    result = memory.episode_store.lock_episode(episode_id, locked=locked)
    if result:
        return jsonify({"success": True, "episode_id": episode_id, "locked": locked})
    return jsonify({"success": False, "error": "Episode not found"}), 404


@episodes_bp.route("/api/episodes/forgetting", methods=["POST"])
def apply_forgetting():
    """Run forgetting policy."""
    memory = _get_memory_agent()
    if not memory or not hasattr(memory, 'forgetting') or not memory.forgetting:
        return jsonify({"success": False, "error": "Forgetting policy not initialized"}), 503

    data = request.get_json(silent=True) or {}
    action = data.get("action", "decay")

    if action == "decay":
        count = memory.forgetting.apply_decay(memory.episode_store)
    elif action == "archive":
        days = data.get("days", 90)
        count = memory.forgetting.archive_old(memory.episode_store, days=days)
    elif action == "erase":
        count = memory.forgetting.privacy_erase(memory.episode_store)
    else:
        return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400

    return jsonify({"success": True, "action": action, "affected": count})
