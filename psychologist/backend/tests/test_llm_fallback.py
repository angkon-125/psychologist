"""
LLM Agent fallback tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.llm.llm_agent import LLMAgent

@pytest.fixture
def llm_agent():
    # Force Ollama disabled to guarantee fallback testing
    from backend.config import config
    config.USE_OLLAMA = False
    
    agent = LLMAgent()
    agent.initialize()
    return agent

def test_llm_fallback_to_emotion_engine(llm_agent):
    req = AgentRequest(text="I am feeling so anxious", language="en")
    res = llm_agent.safe_process(req)
    
    assert res.success is True
    # Should flag fallback as True
    assert res.metadata["fallback_used"] is True
    assert res.metadata["dominant_emotion"] in ("sadness", "anxiety", "neutral", "fear")
    assert len(res.response) > 0
