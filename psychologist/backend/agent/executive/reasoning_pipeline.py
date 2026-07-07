"""
Reasoning Pipeline — Executive Brain

Orchestrates the internal cognitive steps within the Executive Controller:
  - Agent selection (single or multi-agent voting)
  - Multi-agent voting: dispatch to multiple agents, fuse best response
  - Confidence fusion after agent responses
  - Clarification decision
"""

import logging
from typing import Dict, List, Optional, Tuple

from .schemas import ConfidenceReport, ExecutionPlan
from .confidence_engine import ConfidenceEngine

logger = logging.getLogger("zara.executive.pipeline")


class ReasoningPipeline:
    """
    Inner cognitive loop called by the Executive Controller.

    Usage:
        pipeline = ReasoningPipeline(confidence_engine)
        result = pipeline.execute(request, plan, specialists, intent_confidence)
    """

    def __init__(self, confidence_engine: ConfidenceEngine):
        self.confidence_engine = confidence_engine

    def execute(
        self,
        request_text: str,
        plan: ExecutionPlan,
        specialists: Dict,
        request_obj,
        intent_confidence: float = 0.5,
        context: str = "",
    ) -> Dict:
        """
        Execute the reasoning pipeline.

        Args:
            request_text: User's input text
            plan: The execution plan from TaskPlanner
            specialists: Dict of name -> BaseAgent specialist instances
            request_obj: The original AgentRequest
            intent_confidence: Confidence from intent classification
            context: Retrieved memory context

        Returns:
            Dict with keys:
              - response: final response text
              - agent: selected agent name
              - confidence: agent confidence
              - confidence_report: ConfidenceReport
              - errors: list of error strings
        """
        result = {
            "response": "",
            "agent": "",
            "confidence": 0.0,
            "confidence_report": None,
            "errors": [],
        }

        # Agent selection
        if plan.is_multi_agent and len(plan.required_agents) > 1:
            response, agent, confidence, errors = self._multi_agent_vote(
                request_text, plan, specialists, request_obj
            )
        else:
            response, agent, confidence, errors = self._single_agent_select(
                plan, specialists, request_obj
            )

        result["response"] = response
        result["agent"] = agent
        result["confidence"] = confidence
        result["errors"].extend(errors)

        # Confidence fusion
        context_quality = 0.0
        if context and context.strip():
            context_quality = min(1.0, len(context) / 200.0)

        report = self.confidence_engine.fuse(
            intent_confidence=intent_confidence,
            agent_confidence=confidence,
            context_quality=context_quality,
            plan_confidence=plan.estimated_confidence,
        )
        result["confidence_report"] = report

        logger.debug(
            "Pipeline: agent=%s, confidence=%.2f, recommendation=%s",
            agent, report.overall_confidence, report.recommendation,
        )
        return result

    def _single_agent_select(
        self, plan: ExecutionPlan, specialists: Dict, request_obj
    ) -> Tuple[str, str, float, List[str]]:
        """Select and dispatch to a single agent."""
        errors = []
        target_agent = plan.required_agents[0] if plan.required_agents else "llm"

        specialist = specialists.get(target_agent)
        if not specialist:
            logger.warning("Agent %s not found, falling back to llm", target_agent)
            target_agent = "llm"
            specialist = specialists.get("llm")

        if not specialist:
            return "", "llm", 0.0, ["No specialist agents available"]

        try:
            res = specialist.safe_process(request_obj)
            return res.response, res.agent, res.confidence, errors
        except Exception as e:
            errors.append(f"Agent {target_agent} failed: {str(e)}")
            return "", target_agent, 0.0, errors

    def _multi_agent_vote(
        self, request_text: str, plan: ExecutionPlan,
        specialists: Dict, request_obj
    ) -> Tuple[str, str, float, List[str]]:
        """
        Dispatch to multiple agents and select the best response.

        Simple voting: agent with highest confidence wins.
        """
        errors = []
        agent_responses = []

        for agent_name in plan.required_agents:
            specialist = specialists.get(agent_name)
            if not specialist:
                logger.debug("Multi-agent: skipping %s (not registered)", agent_name)
                continue
            try:
                res = specialist.safe_process(request_obj)
                if res.success and res.response:
                    agent_responses.append((res.response, res.agent, res.confidence))
            except Exception as e:
                errors.append(f"Agent {agent_name} failed: {str(e)}")

        if not agent_responses:
            return "", "", 0.0, errors or ["No agents responded"]

        # Vote: highest confidence wins
        best = max(agent_responses, key=lambda x: x[2])
        logger.info(
            "Multi-agent vote: %d agents responded, winner=%s (%.2f)",
            len(agent_responses), best[1], best[2],
        )
        return best[0], best[1], best[2], errors
