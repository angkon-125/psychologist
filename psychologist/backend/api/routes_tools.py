"""
Tools routes Blueprint

Handles tool execution checks and executions.
"""

from flask import Blueprint, request, jsonify
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

tools_bp = Blueprint("tools_bp", __name__)

@tools_bp.route("/api/tools/execute", methods=["POST"])
def execute_tool():
    data = request.get_json(silent=True) or {}
    tool_name = data.get("tool_name", "")
    arguments = data.get("arguments", {})
    session_id = data.get("session_id", "")
    
    if not tool_name:
        return jsonify({"success": False, "errors": ["tool_name is required."]}), 400
        
    tool_agent = orchestrator.specialists.get("tool")
    if not tool_agent:
        return jsonify({"success": False, "errors": ["Tool Agent not registered."]}), 503
        
    # Safety Check: check permissions first before running tool
    safety_agent = orchestrator.specialists.get("safety")
    if safety_agent:
        perm_req = AgentRequest(
            text="",
            session_id=session_id,
            metadata={
                "purpose": "tool_check",
                "tool_name": tool_name,
                "risk_level": "medium" if tool_name == "read_file" else "low"
            }
        )
        perm_res = safety_agent.safe_process(perm_req)
        if not perm_res.success:
            return jsonify({
                "success": False,
                "errors": [f"Permission denied: {perm_res.response}"],
                "metadata": perm_res.metadata
            }), 403
            
    req = AgentRequest(
        text="",
        session_id=session_id,
        metadata={
            "purpose": "execute",
            "tool_calls": [{"tool_name": tool_name, "arguments": arguments}]
        }
    )
    
    res = tool_agent.safe_process(req)
    return jsonify(res.to_dict())
