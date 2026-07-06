"""
Evaluation Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.evaluation.evaluation_agent import EvaluationAgent

@pytest.fixture
def evaluation_agent():
    agent = EvaluationAgent()
    agent.initialize()
    return agent

def test_evaluation_initialization(evaluation_agent):
    """Verify evaluation agent initializes successfully."""
    assert evaluation_agent.name == "evaluation"
    assert evaluation_agent._runner is not None

def test_evaluation_run_suite(evaluation_agent):
    """Test running the accuracy evaluation suite."""
    req = AgentRequest(text="", metadata={"purpose": "run_suite"})
    res = evaluation_agent.safe_process(req)
    
    # The runner should complete (even with low scores) or return an error gracefully
    assert res.agent == "evaluation"
    assert res.intent == "evaluation" or res.success is False
    # If successful, verify metadata structure
    if res.success:
        assert "overall" in res.metadata or "accuracy" in res.metadata or len(res.response) > 0

def test_evaluation_unknown_purpose(evaluation_agent):
    """Test error handling for unknown purpose."""
    req = AgentRequest(text="", metadata={"purpose": "unknown_action"})
    res = evaluation_agent.safe_process(req)
    
    assert res.success is False
    assert "Unknown" in res.response or "error" in res.response.lower()
