"""
Evaluation routes Blueprint

Handles running system accuracy test suites and metrics generation.
"""

from flask import Blueprint, jsonify
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

evaluation_bp = Blueprint("evaluation_bp", __name__)

@evaluation_bp.route("/api/evaluation/run", methods=["POST"])
def run_evaluation():
    eval_agent = orchestrator.specialists.get("evaluation")
    if not eval_agent:
        return jsonify({"success": False, "errors": ["Evaluation Agent not registered."]}), 503
        
    req = AgentRequest(text="", metadata={"purpose": "run_suite"})
    res = eval_agent.safe_process(req)
    return jsonify(res.to_dict())
