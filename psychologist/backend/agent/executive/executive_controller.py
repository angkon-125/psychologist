"""
Executive Controller — Executive Brain

Main entry point for the cognitive core. Wraps the existing orchestrator
pipeline and adds: planning, confidence fusion, reflection, goal tracking,
and decision logging.

Pipeline:
  1. Safety pre-check
  2. Intent classification
  3. Task planning (TaskPlanner)
  4. Memory retrieval
  5. Reasoning pipeline (agent selection, execution, confidence fusion)
  6. Reflection (ReflectionLayer)
  7. If reflection says regenerate: one retry
  8. Response validation (safety post-filter)
  9. Memory update
  10. Decision logging
  11. Goal tracking update
  12. Return enriched AgentResponse with executive metadata
"""

import time
import logging
from typing import Dict, Optional

from backend.agent.schemas import AgentRequest, AgentResponse
from backend.agent.router import IntentRouter
from backend.agent.state import ConversationStateManager
from backend.agent.mode_context import (
    resolve_final_mode,
    get_emotion_context_for_mode,
    get_mode_label,
    is_valid_mode,
    DEFAULT_MODE,
)
from .task_planner import TaskPlanner
from .confidence_engine import ConfidenceEngine
from .reflection import ReflectionLayer
from .goal_tracker import GoalTracker
from .decision_log import DecisionLogger
from .reasoning_pipeline import ReasoningPipeline
from .schemas import DecisionRecord

logger = logging.getLogger("zara.executive.controller")


class ExecutiveController:
    """
    Central cognitive controller that wraps the orchestrator pipeline.

    Usage:
        controller = ExecutiveController(specialists)
        response = controller.execute(request)
    """

    def __init__(
        self,
        specialists: Optional[Dict] = None,
        debug_mode: bool = False,
        session_dir: Optional[str] = None,
    ):
        self.planner = TaskPlanner()
        self.confidence_engine = ConfidenceEngine()
        self.reflection = ReflectionLayer()
        self.goal_tracker = GoalTracker(session_dir=session_dir)
        self.decision_logger = DecisionLogger(debug_mode=debug_mode)
        self.pipeline = ReasoningPipeline(self.confidence_engine)

        self.router = IntentRouter()
        self.state_manager = ConversationStateManager()
        self.specialists: Dict = specialists or {}

        # Interrupt state
        self._interrupted_plan = None
        self._interrupted_request = None

    def register_specialist(self, name: str, agent) -> None:
        """Register a specialist agent."""
        self.specialists[name] = agent

    def execute(self, request: AgentRequest) -> AgentResponse:
        """
        Execute the full cognitive pipeline.

        Args:
            request: AgentRequest from the API layer

        Returns:
            AgentResponse with executive metadata
        """
        start_time = time.perf_counter()

        # Check for interrupt resume
        if self._interrupted_plan and self._interrupted_request:
            logger.info("Resuming from interrupted plan")
            return self._resume_interrupted(request, start_time)

        session_id = request.session_id or self.state_manager.session_id
        request.session_id = session_id
        frontend_mode = request.agent_mode if is_valid_mode(request.agent_mode) else DEFAULT_MODE

        # ── Step 1: Safety Pre-Check ──
        safety_agent = self.specialists.get("safety")
        if not safety_agent:
            return AgentResponse.error("executive", "Safety Agent not registered")

        safety_res = safety_agent.safe_process(request)
        if safety_res.risk_level in ("high", "critical") or not safety_res.success:
            return self._crisis_response(
                request, safety_res, session_id, start_time
            )

        # ── Step 2: Intent Classification ──
        intent, intent_conf, target_agent_name = self.router.classify(request.text)
        request.metadata["intent"] = intent
        request.metadata["intent_confidence"] = intent_conf

        # Resolve mode
        resolved_mode = resolve_final_mode(frontend_mode, intent, safety_override=False)
        emotion_context = get_emotion_context_for_mode(resolved_mode)
        request.metadata["resolved_mode"] = resolved_mode
        request.metadata["emotion_context"] = emotion_context

        # ── Step 2b: Health Awareness ──
        health_context = None
        try:
            from backend.system_health import HealthMonitor
            from backend.config import config
            # Lazy init health monitor (reuse if exists)
            if not hasattr(self, '_health_monitor'):
                self._health_monitor = HealthMonitor(
                    specialists=self.specialists,
                    db_path=config.MEMORY_DB_PATH,
                    ollama_url=config.OLLAMA_BASE_URL,
                )
            else:
                self._health_monitor.update_specialists(self.specialists)
            
            health = self._health_monitor.check_all(use_cache=True)
            if health.status != "healthy":
                degraded = health.degraded_features
                if degraded:
                    health_context = {
                        "status": health.status,
                        "degraded_features": degraded,
                        "recommendations": health.recommendations,
                    }
                    request.metadata["health_context"] = health_context
                    logger.info("Health awareness: %s degraded features", len(degraded))
        except Exception as e:
            logger.debug("Health awareness check skipped: %s", e)

        # ── Step 2c: Workspace Awareness ──
        workspace_context = None
        try:
            from backend.workspace import WorkspaceManager
            from backend.config import config as _cfg
            if not hasattr(self, '_workspace_manager'):
                self._workspace_manager = WorkspaceManager(db_path=_cfg.MEMORY_DB_PATH)
            wm = self._workspace_manager
            summary = wm.get_summary()
            workspace_context = {
                "active_project": summary.active_project,
                "next_task": summary.next_task,
                "blocked_count": summary.total_blocked_tasks,
                "completed_today": summary.completed_today,
            }
            request.metadata["workspace_context"] = workspace_context
            # If user text references a project name, set it as active
            if summary.active_project and summary.active_project.get("name"):
                proj_name = summary.active_project["name"].lower()
                if proj_name in request.text.lower():
                    logger.info("Workspace: user referenced active project '%s'", proj_name)
        except Exception as e:
            logger.debug("Workspace awareness skipped: %s", e)

        # ── Step 3: Task Planning ──
        context = request.metadata.get("context", "")
        plan = self.planner.plan(
            text=request.text,
            intent=intent,
            intent_confidence=intent_conf,
            context=context,
            mode=resolved_mode,
        )

        # ── Step 4: Memory Retrieval ──
        memory_agent = self.specialists.get("memory")
        recent_context = ""
        if memory_agent:
            mem_res = memory_agent.safe_process(AgentRequest(
                text=request.text,
                session_id=session_id,
                metadata={"purpose": "retrieve", "limit": 5}
            ))
            if mem_res.success:
                recent_context = mem_res.metadata.get("context", "")
                request.metadata["context"] = recent_context

        if not recent_context:
            recent_context = self.state_manager.get_recent_context()
            request.metadata["context"] = recent_context

        # ── Step 4b: Episode Recall ──
        episode_context = ""
        if memory_agent and hasattr(memory_agent, 'episode_recall') and memory_agent.episode_recall:
            try:
                recall_result = memory_agent.episode_recall.recall_by_query(request.text, limit=3)
                if recall_result.episodes:
                    ep_parts = []
                    for ep in recall_result.episodes:
                        ep_parts.append(f"[{ep.title}] {ep.summary}")
                    episode_context = "Relevant episodes: " + "; ".join(ep_parts)
                    request.metadata["episode_context"] = episode_context
                    # Enrich context with episode info
                    recent_context = (recent_context + "\n" + episode_context).strip()
            except Exception as e:
                logger.debug("Episode recall skipped: %s", e)

        # ── Step 5: Reasoning Pipeline ──
        pipeline_result = self.pipeline.execute(
            request_text=request.text,
            plan=plan,
            specialists=self.specialists,
            request_obj=request,
            intent_confidence=intent_conf,
            context=recent_context,
        )

        final_text = pipeline_result["response"]
        response_source = pipeline_result["agent"]
        confidence = pipeline_result["confidence"]
        confidence_report = pipeline_result["confidence_report"]
        pipeline_errors = pipeline_result.get("errors", [])

        # Handle clarification recommendation
        if confidence_report and self.confidence_engine.should_clarify(confidence_report):
            clarification = self.confidence_engine.generate_clarification_prompt(
                confidence_report, request.text
            )
            if clarification:
                final_text = clarification + (" " + final_text if final_text else "")

        # ── Step 6: Reflection ──
        reflection_result = self.reflection.reflect(
            request_text=request.text,
            response_text=final_text,
            plan=plan,
            context=recent_context,
            intent=intent,
        )

        # ── Step 7: Regeneration (max 1 pass) ──
        if reflection_result.should_regenerate and reflection_result.issue_type == "misunderstood":
            logger.info("Reflection: regenerating response (issue=%s)", reflection_result.issue_type)
            retry_result = self.pipeline.execute(
                request_text=request.text,
                plan=plan,
                specialists=self.specialists,
                request_obj=request,
                intent_confidence=intent_conf,
                context=recent_context,
            )
            if retry_result["response"]:
                final_text = retry_result["response"]
                response_source = retry_result["agent"]
                confidence = retry_result["confidence"]
                confidence_report = retry_result["confidence_report"]

        # ── Step 8: Safety Post-Filter ──
        if hasattr(safety_agent, "filter_response"):
            final_text = safety_agent.filter_response(final_text)

        # ── Step 9: Memory Update ──
        if memory_agent:
            memory_agent.safe_process(AgentRequest(
                text=f"User: {request.text} | ZARA: {final_text}",
                session_id=session_id,
                metadata={
                    "purpose": "save_interaction",
                    "risk": "low",
                    "intent": intent,
                }
            ))

        # ── Step 9b: Episode Builder Update ──
        if memory_agent and hasattr(memory_agent, 'episode_builder') and memory_agent.episode_builder:
            try:
                memory_agent.episode_builder.add_turn(
                    text=request.text,
                    role="user",
                    intent=intent,
                    emotion=request.metadata.get("emotion_context", "neutral"),
                    session_id=session_id,
                )
                if memory_agent.episode_builder.should_create_episode():
                    episode = memory_agent.episode_builder.build_episode()
                    if episode and memory_agent.episode_store:
                        episode.source_session_id = session_id
                        memory_agent.episode_store.save_episode(episode)
                        memory_agent.episode_builder.reset()
                        logger.info("Episode created: %s", episode.title)
            except Exception as e:
                logger.debug("Episode builder skipped: %s", e)

        # ── Step 10: Decision Logging ──
        latency = (time.perf_counter() - start_time) * 1000
        decision = DecisionRecord(
            request_id=request.request_id,
            intent=intent,
            selected_agents=[response_source],
            selected_tools=plan.required_tools,
            confidence=confidence,
            reflection_result=reflection_result.issue_type,
            duration_ms=latency,
            errors=pipeline_errors,
        )
        self.decision_logger.log(decision)

        # ── Step 11: Goal Tracking ──
        goal_id = self.goal_tracker.detect_goal_from_text(request.text)
        goal_state = None
        if goal_id:
            goal_state = self.goal_tracker.get_goal_summary(goal_id)

        # ── Step 11b: Workspace Update ──
        try:
            if hasattr(self, '_workspace_manager') and self._workspace_manager:
                wm_ws = self._workspace_manager
                # Detect task completion from text
                ws_tasks = wm_ws.list_tasks(status="in_progress")
                for t in ws_tasks:
                    if t.title.lower() in request.text.lower():
                        if any(w in request.text.lower() for w in ("done", "completed", "finished", "finished")):
                            wm_ws.complete_task(t.task_id)
                            logger.info("Workspace: auto-completed task '%s'", t.title)
                            break
        except Exception as e:
            logger.debug("Workspace update skipped: %s", e)

        # ── Step 12: State Logging ──
        self.state_manager.record_turn(
            request_id=request.request_id,
            user_text=request.text,
            intent=intent,
            intent_confidence=intent_conf,
            dispatched_agent=response_source,
            response_text=final_text,
            response_confidence=confidence,
            risk_level="low",
            latency_ms=latency,
        )

        # ── Build Response ──
        metadata = {
            "selected_agent": response_source,
            "latency_ms": latency,
            "session_id": session_id,
            "resolved_mode": resolved_mode,
            "emotion_context": emotion_context,
            "mode_label": get_mode_label(resolved_mode),
            # Executive metadata
            "executive_plan": plan.to_dict(),
            "confidence_report": confidence_report.to_dict() if confidence_report else None,
            "reflection": reflection_result.to_dict(),
            "goal_state": goal_state,
            "workspace_context": workspace_context,
            "decision_id": decision.decision_id,
        }

        return AgentResponse(
            success=True,
            agent="executive",
            intent=intent,
            response=final_text,
            confidence=confidence,
            risk_level="low",
            metadata=metadata,
        )

    def interrupt(self) -> None:
        """Save current state for later resume."""
        logger.info("Executive interrupted — saving state")
        # State is preserved in the instance variables

    def _crisis_response(self, request, safety_res, session_id, start_time) -> AgentResponse:
        """Handle crisis bypass — skip executive planning."""
        latency = (time.perf_counter() - start_time) * 1000
        self.state_manager.record_turn(
            request_id=request.request_id,
            user_text=request.text,
            intent="crisis",
            intent_confidence=1.0,
            dispatched_agent="safety",
            response_text=safety_res.response,
            response_confidence=1.0,
            risk_level=safety_res.risk_level,
            latency_ms=latency,
            errors=safety_res.errors,
        )
        resolved_mode = "safety"
        emotion_context = get_emotion_context_for_mode(resolved_mode)

        return AgentResponse(
            success=True,
            agent="executive",
            intent="crisis",
            response=safety_res.response,
            confidence=1.0,
            risk_level=safety_res.risk_level,
            metadata={
                "safety_assessment": safety_res.metadata,
                "resolved_mode": resolved_mode,
                "emotion_context": emotion_context,
                "mode_label": get_mode_label(resolved_mode),
                "executive_plan": None,
                "confidence_report": None,
                "reflection": {"issues_found": [], "should_regenerate": False, "issue_type": "none"},
                "goal_state": None,
                "decision_id": None,
            }
        )

    def _resume_interrupted(self, request, start_time) -> AgentResponse:
        """Resume from an interrupted plan."""
        plan = self._interrupted_plan
        self._interrupted_plan = None
        self._interrupted_request = None
        # Re-execute with the saved plan
        pipeline_result = self.pipeline.execute(
            request_text=request.text,
            plan=plan,
            specialists=self.specialists,
            request_obj=request,
        )
        latency = (time.perf_counter() - start_time) * 1000
        return AgentResponse(
            success=True,
            agent="executive",
            intent=plan.goal,
            response=pipeline_result["response"],
            confidence=pipeline_result["confidence"],
            metadata={"resumed": True, "latency_ms": latency},
        )
