"""
Prediction Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.prediction.prediction_agent import PredictionAgent

@pytest.fixture
def prediction_agent():
    agent = PredictionAgent()
    agent.initialize()
    return agent

def test_prediction_output_schema(prediction_agent):
    req = AgentRequest(
        text="I am extremely stressed", 
        user_mood="sadness"
    )
    res = prediction_agent.safe_process(req)
    
    assert res.success is True
    assert res.intent == "prediction"
    
    # Verify properties of metadata containing PredictionResult schema
    meta = res.metadata
    assert "prediction" in meta
    assert "reason" in meta
    assert "confidence" in meta
    assert "risk_level" in meta
    assert "missing_information" in meta
    assert "recommended_preparation" in meta
    
    assert isinstance(meta["missing_information"], list)
    assert isinstance(meta["recommended_preparation"], list)
