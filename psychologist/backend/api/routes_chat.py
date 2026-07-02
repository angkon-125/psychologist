"""
Chat routes Blueprint

Provides /api/chat endpoint routed through the Orchestrator Agent.
"""

from flask import Blueprint, request, jsonify
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    session_id = data.get("session_id", "")
    language = data.get("language", "en")
    user_mood = data.get("user_mood")
    
    if not text:
        return jsonify({"success": False, "errors": ["Text field is required."]}), 400
        
    req = AgentRequest(
        text=text,
        session_id=session_id,
        language=language,
        user_mood=user_mood
    )
    
    res = orchestrator.safe_process(req)
    return jsonify(res.to_dict())
