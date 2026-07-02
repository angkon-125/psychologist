"""
Memory Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.memory.memory_agent import MemoryAgent

@pytest.fixture
def memory_agent(tmp_path):
    # Use temporary DB path for test isolation
    db_file = tmp_path / "test_zara.db"
    
    # Configure DB path override
    from backend.config import config
    config.MEMORY_DB_PATH = str(db_file)
    
    agent = MemoryAgent()
    agent.initialize()
    return agent

def test_memory_crud(memory_agent):
    session_id = "test_memory_session"
    
    # Save interaction
    req = AgentRequest(
        text="User: I need to relax | ZARA: Let's do breathing exercise together.",
        session_id=session_id,
        metadata={"purpose": "save_interaction", "intent": "breathing", "emotion": "stressed", "risk": "low"}
    )
    res = memory_agent.safe_process(req)
    assert res.success is True
    
    # Retrieve context
    req_ret = AgentRequest(
        text="",
        session_id=session_id,
        metadata={"purpose": "retrieve", "limit": 5}
    )
    res_ret = memory_agent.safe_process(req_ret)
    assert res_ret.success is True
    assert "User: I need to relax" in res_ret.metadata["context"]
    assert "ZARA: Let's do breathing exercise together." in res_ret.metadata["context"]

def test_preferences(memory_agent):
    # Set preference
    req_set = AgentRequest(
        text="",
        metadata={"purpose": "set_preference", "key": "slow_speaker", "value": True}
    )
    res_set = memory_agent.safe_process(req_set)
    assert res_set.success is True
    
    # Get preference
    req_get = AgentRequest(
        text="",
        metadata={"purpose": "get_preference", "key": "slow_speaker", "default": False}
    )
    res_get = memory_agent.safe_process(req_get)
    assert res_get.success is True
    assert res_get.metadata["value"] is True
