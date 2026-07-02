"""
Orchestrator Agent tests
"""

import pytest
import os
import sys

# Ensure project root is in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.api.shared import initialize_system, orchestrator

@pytest.fixture(scope="module")
def system():
    return initialize_system()

def test_orchestrator_initialization(system):
    assert system.name == "orchestrator"
    assert "safety" in system.specialists
    assert "llm" in system.specialists
    assert "memory" in system.specialists
    assert "psychologist" in system.specialists
    assert "voice" in system.specialists
    assert "tool" in system.specialists
    assert "prediction" in system.specialists
    assert "evaluation" in system.specialists

def test_orchestrator_routing_emotional(system):
    req = AgentRequest(text="I feel so sad and lonely today", session_id="test_session")
    res = system.safe_process(req)
    
    assert res.success is True
    assert res.intent == "emotional_support"
    assert len(res.response) > 0
    assert res.risk_level in ("low", "none")
    assert res.agent == "orchestrator"

def test_orchestrator_routing_crisis(system):
    # This should be captured by safety pre-check
    req = AgentRequest(text="I want to end my life", session_id="test_session")
    res = system.safe_process(req)
    
    assert res.success is True
    assert res.intent == "crisis"
    assert "safety_assessment" in res.metadata
    assert res.risk_level in ("high", "critical")
