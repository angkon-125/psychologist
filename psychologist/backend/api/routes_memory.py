"""
Memory routes Blueprint

Handles POST /api/memory/query to retrieve records.
"""

from flask import Blueprint, request, jsonify
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

memory_bp = Blueprint("memory_bp", __name__)

@memory_bp.route("/api/memory/query", methods=["POST"])
def query_memory():
    data = request.get_json(silent=True) or {}
    text = data.get("query", "") or data.get("text", "")
    session_id = data.get("session_id", "")
    limit = data.get("limit", 5)
    
    memory_agent = orchestrator.specialists.get("memory")
    if not memory_agent:
        return jsonify({"success": False, "errors": ["Memory Agent not registered."]}), 503
        
    req = AgentRequest(
        text=text,
        session_id=session_id,
        metadata={"purpose": "retrieve", "limit": limit}
    )
    res = memory_agent.safe_process(req)
    return jsonify(res.to_dict())
