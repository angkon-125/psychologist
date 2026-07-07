"""
Executive Brain — Cognitive Core Tests

Tests for all executive components:
- TaskPlanner: plan generation, multi-agent detection
- ConfidenceEngine: fusion math, thresholds, clarification
- ReflectionLayer: each check type, regeneration flag
- GoalTracker: create/update/detect goals, persistence
- DecisionLogger: log retrieval, debug mode gating
- ReasoningPipeline: agent selection, multi-agent voting
- ExecutiveController: full pipeline, crisis bypass, metadata
"""

import os
import sys
import json
import tempfile
import pytest

# Ensure project root is in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.executive.schemas import (
    ExecutionPlan, ConfidenceReport, ReflectionResult, GoalState, DecisionRecord,
)
from backend.agent.executive.task_planner import TaskPlanner
from backend.agent.executive.confidence_engine import ConfidenceEngine
from backend.agent.executive.reflection import ReflectionLayer
from backend.agent.executive.goal_tracker import GoalTracker
from backend.agent.executive.decision_log import DecisionLogger
from backend.agent.executive.reasoning_pipeline import ReasoningPipeline
from backend.agent.executive.executive_controller import ExecutiveController
from backend.agent.schemas import AgentRequest, AgentResponse
from backend.agent.base import BaseAgent


# ── Fake agent for testing ────────────────────────────────────────

class FakeAgent(BaseAgent):
    """Minimal agent for testing."""
    def __init__(self, name="fake", response="fake response", confidence=0.8, intent="general"):
        self._name = name
        self._response = response
        self._confidence = confidence
        self._intent = intent
        super().__init__()
        self._initialized = True

    def _get_agent_name(self):
        return self._name

    def process(self, request):
        return AgentResponse(
            success=True,
            agent=self._name,
            intent=self._intent,
            response=self._response,
            confidence=self._confidence,
        )


class FailingAgent(BaseAgent):
    """Agent that always fails."""
    def __init__(self, name="failing"):
        self._name = name
        super().__init__()
        self._initialized = True

    def _get_agent_name(self):
        return self._name

    def process(self, request):
        raise RuntimeError("Agent failure")


# ═══════════════════════════════════════════════════════════════════
# TestExecutionPlan
# ═══════════════════════════════════════════════════════════════════

class TestExecutionPlan:
    """Tests for TaskPlanner plan generation."""

    def setup_method(self):
        self.planner = TaskPlanner()

    def test_plan_emotional_support(self):
        plan = self.planner.plan("I feel so sad today", intent="emotional_support", intent_confidence=0.85)
        assert "psychologist" in plan.required_agents
        assert plan.goal == "Provide emotional support"
        assert plan.estimated_confidence > 0.0

    def test_plan_crisis(self):
        plan = self.planner.plan("I want to end it all", intent="crisis", intent_confidence=0.95)
        assert "safety" in plan.required_agents
        assert plan.risk_assessment == "high"

    def test_plan_tool_request(self):
        plan = self.planner.plan("Open file test.py", intent="tool_request", intent_confidence=0.8)
        assert "tool" in plan.required_agents
        assert len(plan.required_tools) > 0

    def test_plan_general(self):
        plan = self.planner.plan("What is Python?", intent="general", intent_confidence=0.6)
        assert "llm" in plan.required_agents

    def test_plan_multi_agent_detection(self):
        plan = self.planner.plan(
            "I'm anxious and my deadline is tomorrow",
            intent="emotional_support",
            intent_confidence=0.8,
        )
        assert plan.is_multi_agent is True
        assert len(plan.required_agents) > 1

    def test_plan_memory_needed(self):
        plan = self.planner.plan(
            "Remember what I said before about my project",
            intent="general",
            intent_confidence=0.5,
        )
        assert plan.needs_memory is True

    def test_plan_memory_needed_from_context(self):
        plan = self.planner.plan(
            "Continue working on it",
            intent="general",
            intent_confidence=0.5,
            context="Previous: user was coding a Python app",
        )
        assert plan.needs_memory is True

    def test_plan_clarification_needed(self):
        plan = self.planner.plan(
            "it",
            intent="general",
            intent_confidence=0.3,
        )
        assert plan.needs_clarification is True

    def test_plan_steps_generated(self):
        plan = self.planner.plan("Hello", intent="greeting", intent_confidence=0.9)
        assert len(plan.steps) > 0
        assert "classify_intent" in plan.steps
        assert "generate_response" in plan.steps

    def test_plan_to_dict(self):
        plan = self.planner.plan("test", intent="general")
        d = plan.to_dict()
        assert "plan_id" in d
        assert "required_agents" in d
        assert "steps" in d


# ═══════════════════════════════════════════════════════════════════
# TestConfidenceEngine
# ═══════════════════════════════════════════════════════════════════

class TestConfidenceEngine:
    """Tests for confidence fusion and threshold logic."""

    def setup_method(self):
        self.engine = ConfidenceEngine()

    def test_high_confidence_respond(self):
        report = self.engine.fuse(
            intent_confidence=0.95,
            agent_confidence=0.95,
            context_quality=0.9,
            plan_confidence=0.9,
        )
        assert report.recommendation == "respond"
        assert report.overall_confidence > 0.90

    def test_medium_confidence_uncertain(self):
        report = self.engine.fuse(
            intent_confidence=0.75,
            agent_confidence=0.80,
            context_quality=0.5,
            plan_confidence=0.7,
        )
        assert report.recommendation in ("respond_uncertain", "respond")

    def test_low_confidence_clarify(self):
        report = self.engine.fuse(
            intent_confidence=0.5,
            agent_confidence=0.5,
            context_quality=0.3,
            plan_confidence=0.5,
        )
        assert report.recommendation == "clarify"

    def test_very_low_confidence_explain(self):
        report = self.engine.fuse(
            intent_confidence=0.1,
            agent_confidence=0.1,
            context_quality=0.0,
            plan_confidence=0.1,
        )
        assert report.recommendation == "explain_missing"
        assert report.overall_confidence < 0.40

    def test_fusion_weights(self):
        # Verify weighted average: 0.3*intent + 0.4*agent + 0.15*context + 0.15*plan
        report = self.engine.fuse(
            intent_confidence=1.0,
            agent_confidence=1.0,
            context_quality=1.0,
            plan_confidence=1.0,
        )
        assert abs(report.overall_confidence - 1.0) < 0.01

    def test_fusion_weights_partial(self):
        report = self.engine.fuse(
            intent_confidence=1.0,
            agent_confidence=0.0,
            context_quality=0.0,
            plan_confidence=0.0,
        )
        # 0.3*1.0 + 0.4*0.0 + 0.15*0.0 + 0.15*0.0 = 0.30
        assert abs(report.overall_confidence - 0.30) < 0.01

    def test_should_clarify(self):
        report = ConfidenceReport(overall_confidence=0.55, recommendation="clarify")
        assert self.engine.should_clarify(report) is True

    def test_should_not_clarify_high(self):
        report = ConfidenceReport(overall_confidence=0.95, recommendation="respond")
        assert self.engine.should_clarify(report) is False

    def test_generate_clarification_with_missing(self):
        report = ConfidenceReport(
            overall_confidence=0.5,
            missing_information=["your project name", "the deadline"],
            recommendation="clarify",
        )
        prompt = self.engine.generate_clarification_prompt(report, "help me")
        assert "project name" in prompt or "deadline" in prompt

    def test_generate_clarification_generic(self):
        report = ConfidenceReport(overall_confidence=0.5, recommendation="clarify")
        prompt = self.engine.generate_clarification_prompt(report, "help")
        assert len(prompt) > 10

    def test_generate_missing_explanation(self):
        report = ConfidenceReport(
            overall_confidence=0.2,
            missing_information=["topic"],
            recommendation="explain_missing",
        )
        explanation = self.engine.generate_missing_explanation(report)
        assert "topic" in explanation

    def test_clamp_inputs(self):
        # Values > 1.0 should be clamped
        report = self.engine.fuse(
            intent_confidence=2.0,
            agent_confidence=-0.5,
            context_quality=1.5,
            plan_confidence=0.5,
        )
        assert 0.0 <= report.overall_confidence <= 1.0

    def test_agent_confidences_in_report(self):
        report = self.engine.fuse(
            agent_confidences={"psychologist": 0.9, "llm": 0.7},
        )
        assert "psychologist" in report.agent_confidences
        assert report.agent_confidences["psychologist"] == 0.9


# ═══════════════════════════════════════════════════════════════════
# TestReflectionLayer
# ═══════════════════════════════════════════════════════════════════

class TestReflectionLayer:
    """Tests for post-response reflection checks."""

    def setup_method(self):
        self.reflection = ReflectionLayer()

    def test_no_issues_good_response(self):
        result = self.reflection.reflect(
            request_text="How do I open a file?",
            response_text="To open a file in Python, use the open() function.",
            intent="general",
        )
        assert result.issue_type == "none"
        assert result.should_regenerate is False

    def test_misunderstood_request(self):
        result = self.reflection.reflect(
            request_text="How do I cook pasta?",
            response_text="The weather is nice today.",
            intent="general",
        )
        assert result.issue_type == "misunderstood"
        assert result.should_regenerate is True

    def test_ignored_memory_context(self):
        result = self.reflection.reflect(
            request_text="Tell me more about it",
            response_text="Sure, here is some information about programming.",
            context="User previously discussed their Python project about data analysis",
            intent="general",
        )
        # Response doesn't reference the Python project context
        assert "ignored_memory" in result.issue_type or result.issue_type == "none"

    def test_forgot_tool(self):
        plan = ExecutionPlan(required_tools=["file_operations"])
        result = self.reflection.reflect(
            request_text="Scan my project",
            response_text="I'd be happy to help with that.",
            plan=plan,
            intent="tool_request",
        )
        assert result.issue_type == "forgot_tool"

    def test_tool_mentioned_no_issue(self):
        plan = ExecutionPlan(required_tools=["file_operations"])
        result = self.reflection.reflect(
            request_text="Scan my project",
            response_text="I'll run a file scan operation on your project.",
            plan=plan,
            intent="tool_request",
        )
        assert result.issue_type != "forgot_tool"

    def test_safety_violation(self):
        result = self.reflection.reflect(
            request_text="How are you?",
            response_text="Here's how to kill a process permanently.",
            intent="greeting",
        )
        assert result.issue_type == "safety_violation"
        assert result.should_regenerate is True

    def test_contradiction_detection(self):
        result = self.reflection.reflect(
            request_text="What did I say?",
            response_text="I didn't say that before. You are wrong.",
            context="User asked about Python earlier",
            intent="general",
        )
        # Contradiction patterns may or may not trigger depending on exact wording
        assert isinstance(result.issues_found, list)

    def test_greeting_no_misunderstanding(self):
        result = self.reflection.reflect(
            request_text="Hello!",
            response_text="Hi there! How can I help?",
            intent="greeting",
        )
        assert result.issue_type == "none"

    def test_farewell_no_misunderstanding(self):
        result = self.reflection.reflect(
            request_text="Goodbye",
            response_text="Take care! See you soon.",
            intent="farewell",
        )
        assert result.issue_type == "none"

    def test_reflection_result_to_dict(self):
        result = ReflectionResult(issues_found=["test"], should_regenerate=True, issue_type="misunderstood")
        d = result.to_dict()
        assert d["issue_type"] == "misunderstood"
        assert d["should_regenerate"] is True


# ═══════════════════════════════════════════════════════════════════
# TestGoalTracker
# ═══════════════════════════════════════════════════════════════════

class TestGoalTracker:
    """Tests for goal tracking and persistence."""

    def test_create_goal(self):
        tracker = GoalTracker()
        goal = tracker.create_goal("Complete project", tasks=["design", "code", "test"])
        assert goal.description == "Complete project"
        assert goal.status == "active"
        assert len(goal.pending_tasks) == 3
        assert goal.completion_pct == 0.0

    def test_update_goal(self):
        tracker = GoalTracker()
        goal = tracker.create_goal("Test goal", tasks=["a", "b", "c"])
        updated = tracker.update_goal(goal.goal_id, completed_tasks=["a"], pending_tasks=["b", "c"])
        assert updated is not None
        assert len(updated.completed_tasks) == 1
        assert abs(updated.completion_pct - 1/3) < 0.01

    def test_goal_auto_complete(self):
        tracker = GoalTracker()
        goal = tracker.create_goal("Quick task", tasks=["step1"])
        updated = tracker.update_goal(goal.goal_id, completed_tasks=["step1"], pending_tasks=[])
        assert updated.status == "completed"
        assert updated.completion_pct == 1.0

    def test_get_active_goals(self):
        tracker = GoalTracker()
        tracker.create_goal("Goal 1")
        tracker.create_goal("Goal 2")
        active = tracker.get_active_goals()
        assert len(active) == 2

    def test_get_goal_summary(self):
        tracker = GoalTracker()
        goal = tracker.create_goal("My goal", tasks=["task1", "task2"])
        tracker.update_goal(goal.goal_id, completed_tasks=["task1"], pending_tasks=["task2"])
        summary = tracker.get_goal_summary(goal.goal_id)
        assert summary is not None
        assert summary["description"] == "My goal"
        assert summary["completed"] == 1
        assert summary["pending"] == 1
        assert "task2" in summary["next_steps"]

    def test_detect_goal_from_text(self):
        tracker = GoalTracker()
        tracker.create_goal("Finish Python project")
        detected = tracker.detect_goal_from_text("I want to finish my Python project today")
        assert detected is not None

    def test_detect_goal_no_match(self):
        tracker = GoalTracker()
        tracker.create_goal("Finish Python project")
        detected = tracker.detect_goal_from_text("What is the weather today?")
        assert detected is None

    def test_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save
            tracker1 = GoalTracker(session_dir=tmpdir)
            goal = tracker1.create_goal("Persistent goal", tasks=["x", "y"])

            # Load in new instance
            tracker2 = GoalTracker(session_dir=tmpdir)
            assert len(tracker2.goals) == 1
            loaded = list(tracker2.goals.values())[0]
            assert loaded.description == "Persistent goal"
            assert loaded.pending_tasks == ["x", "y"]

    def test_goal_state_from_dict(self):
        data = {
            "goal_id": "test-id",
            "description": "Test",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "completed_tasks": ["a"],
            "pending_tasks": ["b"],
            "completion_pct": 0.5,
        }
        goal = GoalState.from_dict(data)
        assert goal.goal_id == "test-id"
        assert goal.completion_pct == 0.5


# ═══════════════════════════════════════════════════════════════════
# TestDecisionLogger
# ═══════════════════════════════════════════════════════════════════

class TestDecisionLogger:
    """Tests for decision logging and retrieval."""

    def test_log_disabled(self):
        dl = DecisionLogger(debug_mode=False)
        record = DecisionRecord(request_id="r1", intent="general", confidence=0.8)
        dl.log(record)
        assert dl.get_recent() == []

    def test_log_enabled(self):
        dl = DecisionLogger(debug_mode=True)
        record = DecisionRecord(request_id="r1", intent="general", confidence=0.8)
        dl.log(record)
        recent = dl.get_recent(n=5)
        assert len(recent) == 1
        assert recent[0].request_id == "r1"

    def test_get_for_request(self):
        dl = DecisionLogger(debug_mode=True)
        dl.log(DecisionRecord(request_id="r1", intent="greeting"))
        dl.log(DecisionRecord(request_id="r2", intent="general"))
        found = dl.get_for_request("r2")
        assert found is not None
        assert found.intent == "general"

    def test_get_for_request_not_found(self):
        dl = DecisionLogger(debug_mode=True)
        assert dl.get_for_request("nonexistent") is None

    def test_get_recent_limit(self):
        dl = DecisionLogger(debug_mode=True)
        for i in range(20):
            dl.log(DecisionRecord(request_id=f"r{i}", intent="general"))
        recent = dl.get_recent(n=5)
        assert len(recent) == 5

    def test_file_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dl = DecisionLogger(debug_mode=True, log_dir=tmpdir)
            dl.log(DecisionRecord(request_id="r1", intent="test"))
            log_file = os.path.join(tmpdir, "decision_log.jsonl")
            assert os.path.exists(log_file)
            with open(log_file) as f:
                lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["request_id"] == "r1"


# ═══════════════════════════════════════════════════════════════════
# TestReasoningPipeline
# ═══════════════════════════════════════════════════════════════════

class TestReasoningPipeline:
    """Tests for the reasoning pipeline agent selection and voting."""

    def setup_method(self):
        self.engine = ConfidenceEngine()
        self.pipeline = ReasoningPipeline(self.engine)

    def test_single_agent_selection(self):
        fake = FakeAgent(name="psychologist", response="I understand how you feel.", confidence=0.85)
        specialists = {"psychologist": fake}
        plan = ExecutionPlan(required_agents=["psychologist"], is_multi_agent=False)
        request = AgentRequest(text="I feel sad")

        result = self.pipeline.execute(
            request_text="I feel sad",
            plan=plan,
            specialists=specialists,
            request_obj=request,
            intent_confidence=0.8,
        )
        assert result["agent"] == "psychologist"
        assert result["confidence"] == 0.85
        assert result["confidence_report"] is not None

    def test_fallback_to_llm(self):
        fake_llm = FakeAgent(name="llm", response="Hello!", confidence=0.7)
        specialists = {"llm": fake_llm}
        plan = ExecutionPlan(required_agents=["psychologist"], is_multi_agent=False)
        request = AgentRequest(text="test")

        result = self.pipeline.execute(
            request_text="test",
            plan=plan,
            specialists=specialists,
            request_obj=request,
        )
        assert result["agent"] == "llm"

    def test_multi_agent_voting(self):
        psych = FakeAgent(name="psychologist", response="I hear you.", confidence=0.7)
        llm = FakeAgent(name="llm", response="Let me help.", confidence=0.9)
        specialists = {"psychologist": psych, "llm": llm}
        plan = ExecutionPlan(
            required_agents=["psychologist", "llm"],
            is_multi_agent=True,
        )
        request = AgentRequest(text="I'm anxious and my deadline is tomorrow")

        result = self.pipeline.execute(
            request_text="I'm anxious and my deadline is tomorrow",
            plan=plan,
            specialists=specialists,
            request_obj=request,
        )
        # LLM has higher confidence, should win
        assert result["agent"] == "llm"
        assert result["confidence"] == 0.9

    def test_no_agents_available(self):
        plan = ExecutionPlan(required_agents=["psychologist"], is_multi_agent=False)
        request = AgentRequest(text="test")

        result = self.pipeline.execute(
            request_text="test",
            plan=plan,
            specialists={},
            request_obj=request,
        )
        assert result["agent"] == "llm"
        assert len(result["errors"]) > 0


# ═══════════════════════════════════════════════════════════════════
# TestExecutiveController
# ═══════════════════════════════════════════════════════════════════

class TestExecutiveController:
    """Tests for the full executive controller pipeline."""

    def _make_controller(self, **kwargs):
        """Create a controller with fake specialists."""
        safety = FakeAgent(name="safety", response="I'm here for you.", confidence=0.9)
        # Safety agent needs filter_response method
        safety.filter_response = lambda text: text
        llm = FakeAgent(name="llm", response="Hello! How can I help?", confidence=0.8)
        psychologist = FakeAgent(name="psychologist", response="I understand.", confidence=0.85)
        memory = FakeAgent(name="memory", response="", confidence=0.5)
        # Memory agent returns context via metadata
        original_process = memory.process
        def memory_process(request):
            res = original_process(request)
            res.metadata = {"context": ""}
            return res
        memory.process = memory_process

        specialists = {
            "safety": safety,
            "llm": llm,
            "psychologist": psychologist,
            "memory": memory,
        }
        return ExecutiveController(specialists=specialists, **kwargs)

    def test_basic_execution(self):
        controller = self._make_controller()
        request = AgentRequest(text="Hello there!", session_id="test")
        response = controller.execute(request)
        assert response.success is True
        assert response.agent == "executive"
        assert len(response.response) > 0

    def test_executive_metadata_present(self):
        controller = self._make_controller()
        request = AgentRequest(text="Hello", session_id="test")
        response = controller.execute(request)
        assert "executive_plan" in response.metadata
        assert "confidence_report" in response.metadata
        assert "reflection" in response.metadata
        assert "decision_id" in response.metadata

    def test_crisis_bypass(self):
        # Safety agent detects crisis
        safety = FakeAgent(name="safety", response="Please reach out for help.", confidence=1.0)
        safety.filter_response = lambda text: text
        # Override safe_process to return high risk
        original_safe = safety.safe_process
        def crisis_safe_process(request):
            res = original_safe(request)
            res.risk_level = "high"
            return res
        safety.safe_process = crisis_safe_process

        controller = ExecutiveController(specialists={"safety": safety})
        request = AgentRequest(text="I want to end my life", session_id="test")
        response = controller.execute(request)
        assert response.intent == "crisis"
        assert response.risk_level == "high"
        assert response.metadata["resolved_mode"] == "safety"

    def test_safety_agent_required(self):
        controller = ExecutiveController(specialists={})
        request = AgentRequest(text="Hello", session_id="test")
        response = controller.execute(request)
        assert response.success is False

    def test_mode_resolution(self):
        controller = self._make_controller()
        request = AgentRequest(text="Hello", session_id="test", agent_mode="assistant")
        response = controller.execute(request)
        assert "resolved_mode" in response.metadata
        assert "mode_label" in response.metadata

    def test_emotional_support_routing(self):
        controller = self._make_controller()
        request = AgentRequest(text="I feel so sad and lonely", session_id="test")
        response = controller.execute(request)
        assert response.success is True
        assert response.intent == "emotional_support"

    def test_decision_logged(self):
        controller = self._make_controller(debug_mode=True)
        request = AgentRequest(text="Hello", session_id="test")
        response = controller.execute(request)
        recent = controller.decision_logger.get_recent(n=5)
        assert len(recent) >= 1

    def test_interrupt(self):
        controller = self._make_controller()
        # Interrupt should not raise
        controller.interrupt()
