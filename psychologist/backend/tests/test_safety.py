"""
Safety Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.safety.safety_agent import SafetyAgent

@pytest.fixture
def safety_agent():
    agent = SafetyAgent()
    agent.initialize()
    return agent

def test_crisis_detection(safety_agent):
    # Crisis content check
    req = AgentRequest(text="I want to suicide", metadata={"purpose": "content_check"})
    res = safety_agent.safe_process(req)
    
    assert res.success is False
    assert res.risk_level in ("high", "critical")
    assert len(res.response) > 0 # Safe response template provided

def test_safe_content(safety_agent):
    req = AgentRequest(text="Hello Zara, how's your day?", metadata={"purpose": "content_check"})
    res = safety_agent.safe_process(req)
    
    assert res.success is True
    assert res.risk_level == "none"

def test_tool_permission_checker(safety_agent):
    # Check low risk tool
    req = AgentRequest(
        text="", 
        metadata={
            "purpose": "tool_check",
            "tool_name": "system_info",
            "risk_level": "low"
        }
    )
    res = safety_agent.safe_process(req)
    assert res.success is True
    assert res.requires_confirmation is False

    # Check high risk blocked action
    req = AgentRequest(
        text="", 
        metadata={
            "purpose": "tool_check",
            "tool_name": "delete_system_file",
            "risk_level": "high",
            "action_name": "delete_system_file"
        }
    )
    res = safety_agent.safe_process(req)
    assert res.success is False
