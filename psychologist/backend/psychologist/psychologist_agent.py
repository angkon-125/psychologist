"""
Psychologist Agent

Responsible for emotional support scripts, journaling exercises, breathing activities,
mood check-ins, grounding exercises, and summaries.
Enforces the safety boundaries: does not diagnose, does not pretend to be a therapist,
and escalates crisis concerns directly.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from emotion_engine.interaction.support_tools import SupportTools
from .grounding import GroundingHandler
from .journaling import JournalingHandler
from .session_summary import SessionSummaryHandler

class PsychologistAgent(BaseAgent):
    """
    Psychologist Agent manages supportive interactions.
    Delegates to SupportTools and ensures strict clinical safety boundaries.
    """

    def __init__(self):
        super().__init__()
        self._support_tools = None
        self._grounding = None
        self._journaling = None
        self._summary = None

    def _get_agent_name(self) -> str:
        return "psychologist"

    def initialize(self) -> bool:
        self._support_tools = SupportTools()
        self._grounding = GroundingHandler(self._support_tools)
        self._journaling = JournalingHandler(self._support_tools)
        self._summary = SessionSummaryHandler(self._support_tools)
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        intent = request.metadata.get("intent", "emotional_support")
        language = request.language
        user_mood = request.user_mood or "neutral"
        
        response_text = ""
        metadata = {}
        
        # Dispatch to appropriate handler based on intent
        if intent == "grounding":
            action = self._grounding.get_exercise(language)
            response_text = action.get("content", "")
            metadata = {"action": action}
        elif intent == "journaling":
            action = self._journaling.get_prompt(language, user_mood)
            response_text = action.get("content", "")
            metadata = {"action": action}
        elif intent == "breathing":
            action = self._support_tools.breathing_exercise(language).to_dict()
            response_text = action.get("content", "")
            metadata = {"action": action}
        elif intent == "reflection":
            action = self._support_tools.reflection_questions(language).to_dict()
            response_text = action.get("content", "")
            metadata = {"action": action}
        elif intent == "mood_checkin":
            action = self._support_tools.mood_checkin(language).to_dict()
            response_text = action.get("content", "")
            metadata = {"action": action}
        elif intent == "session_summary":
            action = self._summary.get_summary_prompt(language)
            response_text = action.get("content", "")
            metadata = {"action": action}
        else:
            # Default general emotional support
            action = self._support_tools.calm_down(language).to_dict()
            response_text = action.get("content", "")
            metadata = {"action": action}
            
        return AgentResponse(
            success=True,
            agent=self.name,
            intent=intent,
            response=response_text,
            confidence=0.9,
            risk_level="low",
            metadata=metadata
        )
