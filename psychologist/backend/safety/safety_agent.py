"""
Safety Agent

Responsible for checking all user input for crisis, self-harm, medical/therapy
boundaries, and validating tool permissions before execution.
"""

from typing import Dict, Any, Optional

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from .crisis_detector import CrisisDetector
from .permission_checker import PermissionChecker
from .policy import default_policy

class SafetyAgent(BaseAgent):
    """
    Enforces safety policies, detects crises, filters diagnosis language,
    and approves/denies tool execution permissions.
    """

    def __init__(self):
        super().__init__()
        self._crisis_detector = None
        self._permission_checker = None

    def _get_agent_name(self) -> str:
        return "safety"

    def initialize(self) -> bool:
        self._crisis_detector = CrisisDetector()
        self._permission_checker = PermissionChecker()
        self._initialized = self._crisis_detector.available
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Runs safety checks on user input or validates a tool execution request.
        """
        text = request.text
        language = request.language
        
        # Check if this is a tool check or content check
        purpose = request.metadata.get("purpose", "content_check")
        
        if purpose == "tool_check":
            tool_name = request.metadata.get("tool_name", "")
            risk_level = request.metadata.get("risk_level", "low")
            action_name = request.metadata.get("action_name", "")
            
            result = self._permission_checker.check_tool_permission(
                tool_name=tool_name,
                risk_level=risk_level,
                action_name=action_name
            )
            
            return AgentResponse(
                success=result["permitted"],
                agent=self.name,
                intent="tool_permission",
                response=result["reason"],
                confidence=1.0,
                risk_level=result["risk_level"],
                requires_confirmation=result["requires_confirmation"],
                metadata=result
            )
            
        # Default: content check on user input
        assessment = self._crisis_detector.assess(text, language)
        
        # Determine risk level mapping
        risk_level = assessment.get("risk_level", "none")
        should_escalate = assessment.get("should_escalate", False)
        
        response_text = ""
        if should_escalate:
            response_text = assessment.get("safe_response_template", "")
            
        return AgentResponse(
            success=not should_escalate, # If crisis, we override the flow
            agent=self.name,
            intent="safety_check",
            response=response_text,
            confidence=1.0 if should_escalate else 0.0,
            risk_level=risk_level,
            requires_confirmation=False,
            metadata=assessment
        )

    def filter_response(self, response_text: str) -> str:
        """Filters diagnosis/therapy boundary violations from assistant responses."""
        if not self._crisis_detector:
            return response_text
        return self._crisis_detector.filter_response(response_text)

    def is_safe_response(self, response_text: str) -> bool:
        """Checks if response is safe."""
        if not self._crisis_detector:
            return True
        return self._crisis_detector.is_safe_response(response_text)
