"""
Task Planner — Executive Brain

Generates an internal execution plan before responding.
Uses keyword/heuristic analysis to determine:
  - Which agents are needed (single or multi-agent)
  - Whether memory retrieval is needed
  - Whether tools might be needed
  - Whether clarification might be needed
  - Estimated confidence based on intent clarity

Performance target: <30ms (pure heuristic, no LLM call).
"""

import re
import logging
from typing import List, Optional

from .schemas import ExecutionPlan

logger = logging.getLogger("zara.executive.planner")

# Intent → primary agent mapping (mirrors router.py)
_INTENT_PRIMARY_AGENT = {
    "crisis": "safety",
    "emotional_support": "psychologist",
    "journaling": "psychologist",
    "breathing": "psychologist",
    "reflection": "psychologist",
    "mood_checkin": "psychologist",
    "grounding": "psychologist",
    "tool_request": "tool",
    "voice_command": "voice",
    "greeting": "llm",
    "farewell": "llm",
    "prediction": "prediction",
    "session_summary": "psychologist",
    "general": "llm",
}

# Patterns that suggest multiple agents are needed
_MULTI_AGENT_PATTERNS = [
    re.compile(r"\band\b.*\b(also|too|as well)\b", re.IGNORECASE),
    re.compile(r"\b(anxious|stressed|worried)\b.*\b(deadline|project|work|task)\b", re.IGNORECASE),
    re.compile(r"\b(deadline|project|work|task)\b.*\b(anxious|stressed|worried)\b", re.IGNORECASE),
    re.compile(r"\b(sad|depressed|lonely)\b.*\b(can't|cannot|unable)\b.*\b(focus|work|code)\b", re.IGNORECASE),
    re.compile(r"\b(help|need)\b.*\b(feel|emotion|mood)\b.*\b(build|create|project)\b", re.IGNORECASE),
]

# Patterns that suggest memory is needed
_MEMORY_PATTERNS = [
    re.compile(r"\b(remember|recall|last time|before|previously)\b", re.IGNORECASE),
    re.compile(r"\b(continue|resume|where (was|were|did))\b", re.IGNORECASE),
    re.compile(r"\b(as i (said|mentioned)|earlier)\b", re.IGNORECASE),
    re.compile(r"\b(my|our)\b.*\b(project|goal|plan|progress)\b", re.IGNORECASE),
]

# Patterns that suggest tools are needed
_TOOL_PATTERNS = [
    re.compile(r"\b(open|create|delete|list|scan|run|execute)\b.*\b(file|command|project|script)\b", re.IGNORECASE),
    re.compile(r"\b(system|disk|cpu|memory)\b.*\b(info|usage|check)\b", re.IGNORECASE),
]

# Patterns that suggest the request is ambiguous
_AMBIGUITY_PATTERNS = [
    re.compile(r"^\s*(it|this|that|they)\s+", re.IGNORECASE),
    re.compile(r"^\s*(do|can|could|would)\s+(it|this|that)\b", re.IGNORECASE),
    re.compile(r"^\s*\w+\s*\??$", re.IGNORECASE),  # single word
]


class TaskPlanner:
    """
    Generates execution plans using keyword heuristics.

    Usage:
        planner = TaskPlanner()
        plan = planner.plan("I'm anxious and my deadline is tomorrow",
                            intent="emotional_support",
                            intent_confidence=0.85,
                            context="",
                            mode="assistant")
    """

    def plan(
        self,
        text: str,
        intent: str = "general",
        intent_confidence: float = 0.5,
        context: str = "",
        mode: str = "assistant",
    ) -> ExecutionPlan:
        """
        Generate an execution plan for the given request.

        Args:
            text: User's input text
            intent: Classified intent from router
            intent_confidence: Confidence of intent classification
            context: Recent conversation context
            mode: Current agent mode

        Returns:
            ExecutionPlan with agents, tools, memory needs, etc.
        """
        plan = ExecutionPlan()
        text_lower = text.lower().strip() if text else ""

        # 1. Determine primary agent
        primary_agent = _INTENT_PRIMARY_AGENT.get(intent, "llm")
        plan.required_agents = [primary_agent]

        # 2. Check for multi-agent need
        is_multi = any(p.search(text_lower) for p in _MULTI_AGENT_PATTERNS)
        if is_multi:
            plan.is_multi_agent = True
            # Add secondary agents based on detected aspects
            secondary = self._detect_secondary_agents(text_lower, primary_agent)
            for agent in secondary:
                if agent not in plan.required_agents:
                    plan.required_agents.append(agent)

        # 3. Check if memory is needed
        plan.needs_memory = any(p.search(text_lower) for p in _MEMORY_PATTERNS)
        # Also need memory if there's existing context
        if context and context.strip():
            plan.needs_memory = True

        # 4. Check if tools might be needed
        needs_tools = any(p.search(text_lower) for p in _TOOL_PATTERNS)
        if needs_tools or intent == "tool_request":
            plan.required_tools = ["file_operations"]  # default tool group
            if "tool" not in plan.required_agents:
                plan.required_agents.append("tool")

        # 5. Check if clarification might be needed
        is_ambiguous = any(p.search(text_lower) for p in _AMBIGUITY_PATTERNS)
        plan.needs_clarification = is_ambiguous and intent_confidence < 0.7

        # 6. Estimate confidence
        plan.estimated_confidence = self._estimate_confidence(
            intent_confidence, len(text_lower), is_ambiguous, bool(context)
        )

        # 7. Set goal description
        plan.goal = self._describe_goal(intent, text_lower, mode)

        # 8. Set risk assessment
        plan.risk_assessment = self._assess_risk(intent, text_lower)

        # 9. Build steps
        plan.steps = self._build_steps(plan)

        logger.debug(
            "Plan: goal=%s, agents=%s, multi=%s, confidence=%.2f",
            plan.goal, plan.required_agents, plan.is_multi_agent,
            plan.estimated_confidence,
        )
        return plan

    def _detect_secondary_agents(self, text: str, primary: str) -> List[str]:
        """Detect secondary agents needed for multi-agent requests."""
        agents = []
        emotion_words = re.findall(
            r"\b(anxious|stressed|worried|sad|depressed|lonely|overwhelmed|scared)\b",
            text, re.IGNORECASE,
        )
        task_words = re.findall(
            r"\b(deadline|project|work|task|code|build|create|file)\b",
            text, re.IGNORECASE,
        )
        predict_words = re.findall(
            r"\b(will|predict|forecast|what if|might|could happen)\b",
            text, re.IGNORECASE,
        )

        if emotion_words and primary != "psychologist":
            agents.append("psychologist")
        if task_words and primary != "tool" and primary != "llm":
            agents.append("llm")
        if predict_words and primary != "prediction":
            agents.append("prediction")

        return agents

    def _estimate_confidence(
        self,
        intent_conf: float,
        text_len: int,
        is_ambiguous: bool,
        has_context: bool,
    ) -> float:
        """Estimate plan confidence from available signals."""
        base = intent_conf * 0.6

        # Longer text usually means clearer intent
        if text_len > 20:
            base += 0.15
        elif text_len > 5:
            base += 0.1
        else:
            base -= 0.1

        # Ambiguity reduces confidence
        if is_ambiguous:
            base -= 0.2

        # Having context helps
        if has_context:
            base += 0.1

        return max(0.0, min(1.0, base))

    def _describe_goal(self, intent: str, text: str, mode: str) -> str:
        """Generate a human-readable goal description."""
        goal_map = {
            "crisis": "Ensure user safety",
            "emotional_support": "Provide emotional support",
            "journaling": "Support journaling",
            "breathing": "Guide breathing exercise",
            "tool_request": "Execute requested tool",
            "prediction": "Provide prediction",
            "greeting": "Respond to greeting",
            "farewell": "Respond to farewell",
            "general": "Answer user's question",
        }
        return goal_map.get(intent, f"Handle {intent} request in {mode} mode")

    def _assess_risk(self, intent: str, text: str) -> str:
        """Assess risk level of the request."""
        if intent == "crisis":
            return "high"
        risk_patterns = [
            re.compile(r"\b(kill|harm|die|suicide)\b", re.IGNORECASE),
            re.compile(r"\b(delete|remove|destroy)\b.*\b(file|data|project)\b", re.IGNORECASE),
        ]
        if any(p.search(text) for p in risk_patterns):
            return "medium"
        return "low"

    def _build_steps(self, plan: ExecutionPlan) -> List[str]:
        """Build ordered execution steps from the plan."""
        steps = ["classify_intent"]
        if plan.needs_memory:
            steps.append("retrieve_memory")
        if plan.is_multi_agent:
            steps.append("multi_agent_dispatch")
        else:
            steps.append("select_agent")
        if plan.required_tools:
            steps.append("check_tool_permissions")
            steps.append("execute_tools")
        steps.append("generate_response")
        steps.append("reflect")
        steps.append("validate_response")
        steps.append("update_memory")
        return steps
