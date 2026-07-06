"""
Psychologist Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.psychologist.psychologist_agent import PsychologistAgent

@pytest.fixture
def psychologist_agent():
    agent = PsychologistAgent()
    agent.initialize()
    return agent

def test_psychologist_initialization(psychologist_agent):
    """Verify agent initializes successfully with all handlers."""
    assert psychologist_agent.name == "psychologist"
    assert psychologist_agent._support_tools is not None
    assert psychologist_agent._grounding is not None
    assert psychologist_agent._journaling is not None
    assert psychologist_agent._summary is not None

def test_emotional_support_default(psychologist_agent):
    """Test default emotional support response (calm_down)."""
    req = AgentRequest(text="I feel overwhelmed", language="en", user_mood="anxiety")
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "emotional_support"
    assert res.risk_level == "low"
    assert len(res.response) > 0
    assert "action" in res.metadata

def test_grounding_intent(psychologist_agent):
    """Test grounding exercise dispatch."""
    req = AgentRequest(
        text="I need to ground myself",
        language="en",
        metadata={"intent": "grounding"}
    )
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "grounding"
    assert len(res.response) > 0

def test_journaling_intent(psychologist_agent):
    """Test journaling prompt dispatch."""
    req = AgentRequest(
        text="I want to journal",
        language="en",
        user_mood="sadness",
        metadata={"intent": "journaling"}
    )
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "journaling"
    assert len(res.response) > 0

def test_breathing_intent(psychologist_agent):
    """Test breathing exercise dispatch."""
    req = AgentRequest(
        text="Help me breathe",
        language="en",
        metadata={"intent": "breathing"}
    )
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "breathing"
    assert len(res.response) > 0

def test_mood_checkin_intent(psychologist_agent):
    """Test mood check-in dispatch."""
    req = AgentRequest(
        text="",
        language="en",
        metadata={"intent": "mood_checkin"}
    )
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "mood_checkin"
    assert len(res.response) > 0

def test_bangla_language_support(psychologist_agent):
    """Test that Bangla language is passed through correctly."""
    req = AgentRequest(
        text="আমি খুব দুঃখিত",
        language="bn",
        user_mood="sadness"
    )
    res = psychologist_agent.safe_process(req)
    
    assert res.success is True
    assert len(res.response) > 0
