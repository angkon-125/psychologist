"""
Evaluation Agent

Responsible for measuring accuracy, running the test pipeline, and generating performance reports.
"""

from typing import Dict, Any

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from .accuracy_runner import AccuracyRunner

class EvaluationAgent(BaseAgent):
    """
    Evaluation Agent triggers accuracy evaluations, reads intent/safety test cases,
    and returns a summary of the metrics report.
    """

    def __init__(self):
        super().__init__()
        self._runner = None

    def _get_agent_name(self) -> str:
        return "evaluation"

    def initialize(self) -> bool:
        self._runner = AccuracyRunner()
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        purpose = request.metadata.get("purpose", "run_suite")
        
        if purpose == "run_suite":
            self._logger.info("Running system-wide accuracy evaluation suite...")
            try:
                results = self._runner.run()
                overall = results.get("overall", 0.0)
                
                res_text = (
                    f"Accuracy Evaluation Run Completed.\n"
                    f"Overall Accuracy Score: {overall * 100:.2f}%\n"
                    f"All Targets Met: {results.get('all_targets_met', False)}"
                )
                
                return AgentResponse(
                    success=True,
                    agent=self.name,
                    intent="evaluation",
                    response=res_text,
                    confidence=1.0,
                    risk_level="low",
                    metadata=results
                )
            except Exception as e:
                self._logger.error("Accuracy runner failed: %s", e)
                return AgentResponse.error(self.name, f"Evaluation suite failure: {e}")
                
        return AgentResponse.error(self.name, f"Unknown evaluation agent purpose: {purpose}")
