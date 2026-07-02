"""
Prediction Agent

Responsible for:
  - future proposition generation
  - project risk prediction
  - mood trend prediction
  - system failure prediction
  - next-action recommendation

Every prediction must include:
  - prediction
  - reason
  - confidence
  - risk_level
  - missing_information
  - recommended_preparation
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse, PredictionResult
from emotion_engine.behavior_predictor.behavior_predictor import BehaviorPredictor
from .risk_model import RiskModel
from .future_proposition import FuturePropositionGenerator

class PredictionAgent(BaseAgent):
    """
    Prediction Agent performs trajectory evaluations, behavior predictions,
    and formats them to standard Prediction schemas.
    """

    def __init__(self):
        super().__init__()
        self._behavior_predictor = None
        self._risk_model = None
        self._proposition_gen = None

    def _get_agent_name(self) -> str:
        return "prediction"

    def initialize(self) -> bool:
        self._behavior_predictor = BehaviorPredictor()
        self._risk_model = RiskModel()
        self._proposition_gen = FuturePropositionGenerator()
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        user_mood = request.user_mood or "neutral"
        text = request.text
        
        # Legacy behavior predictor call
        # Requires: current_emotional_state, personality_traits, context, emotional_history
        # Let's create mock objects or read values to pass safely
        try:
            from emotion_engine.models import EmotionalState, PersonalityTraits, ConversationContext
            mock_state = EmotionalState()
            mock_state.primary_emotions[user_mood] = 0.8 if user_mood in mock_state.primary_emotions else 0.0
            mock_traits = PersonalityTraits()
            mock_context = ConversationContext()
            
            legacy_predictions = self._behavior_predictor.get_full_prediction(
                mock_state, mock_traits, mock_context, []
            )
        except Exception as e:
            self._logger.warning("Legacy behavior prediction failed: %s", e)
            legacy_predictions = {}
            
        # Use our clean RiskModel and FuturePropositions to construct standard schema
        evaluated_risk = self._risk_model.evaluate_risk(user_mood, 0.8, [])
        propositions = self._proposition_gen.generate_propositions(user_mood, evaluated_risk["risk_level"])
        
        # Select first proposition or fallback
        prop = propositions[0] if propositions else {
            "action": "Routine check-in in 24 hours",
            "reason": "Normal Operational Cycle",
            "recommended_preparation": "None"
        }
        
        pred_result = PredictionResult(
            prediction=prop["action"],
            reason=prop["reason"],
            confidence=evaluated_risk["confidence"],
            risk_level=evaluated_risk["risk_level"],
            missing_information=["detailed historical sleep data", "trigger mapping logs"] if evaluated_risk["risk_level"] != "low" else [],
            recommended_preparation=[prop["recommended_preparation"]]
        )
        
        # Format response
        res_text = (
            f"Prediction: {pred_result.prediction}\n"
            f"Reason: {pred_result.reason}\n"
            f"Confidence: {pred_result.confidence}\n"
            f"Risk Level: {pred_result.risk_level}"
        )
        
        return AgentResponse(
            success=True,
            agent=self.name,
            intent="prediction",
            response=res_text,
            confidence=pred_result.confidence,
            risk_level=pred_result.risk_level,
            metadata=pred_result.to_dict()
        )
