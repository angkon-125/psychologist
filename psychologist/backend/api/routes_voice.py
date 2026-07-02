"""
Voice routes Blueprint

Handles transcript, state machine, and playback control endpoints.
"""

from flask import Blueprint, request, jsonify
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

voice_bp = Blueprint("voice_bp", __name__)

@voice_bp.route("/api/voice/transcript", methods=["POST"])
def voice_transcript():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    session_id = data.get("session_id", "")
    language = data.get("language", "en")
    
    # Save user speech transcript using memory agent
    memory_agent = orchestrator.specialists.get("memory")
    if memory_agent:
        memory_agent.safe_process(AgentRequest(
            text=text,
            session_id=session_id,
            metadata={"purpose": "save_interaction", "intent": "voice_speech"}
        ))
        
    return jsonify({"success": True, "message": "Transcript recorded successfully."})

@voice_bp.route("/api/voice/state", methods=["POST", "GET"])
def voice_state():
    voice_agent = orchestrator.specialists.get("voice")
    if not voice_agent:
        return jsonify({"success": False, "errors": ["Voice Agent not registered."]}), 503
        
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        to_state = data.get("state", "")
        reason = data.get("reason", "API request")
        
        req = AgentRequest(
            text="",
            metadata={"purpose": "transition", "to_state": to_state, "reason": reason}
        )
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    # GET method
    req = AgentRequest(text="", metadata={"purpose": "get_state"})
    res = voice_agent.safe_process(req)
    return jsonify(res.to_dict())

@voice_bp.route("/api/voice/playback", methods=["POST"])
def voice_playback():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "") # "speak" | "stop" | "pause" | "resume"
    text = data.get("text", "")
    language = data.get("language", "en")
    
    voice_agent = orchestrator.specialists.get("voice")
    if not voice_agent:
        return jsonify({"success": False, "errors": ["Voice Agent not registered."]}), 503
        
    if action == "speak":
        req = AgentRequest(text=text, language=language, metadata={"purpose": "speak"})
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    elif action == "stop":
        req = AgentRequest(text="", metadata={"purpose": "stop_playback"})
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    return jsonify({"success": False, "errors": [f"Unknown action: {action}"]}), 400
