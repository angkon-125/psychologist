"""
Orchestrator Agent

Main central coordinator. Orchestrates routing, safety evaluation, Specialist Agent selection,
LLM response generation, memory access, and final validation.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from backend.agent.router import IntentRouter
from backend.agent.state import ConversationStateManager

logger = logging.getLogger("zara.orchestrator")

class OrchestratorAgent(BaseAgent):
    """
    Central Orchestrator of the ZARA Multi-Agent System.
    Ensures all steps in the target execution pipeline are followed.
    """

    def __init__(self):
        super().__init__()
        self.router = IntentRouter()
        self.state_manager = ConversationStateManager()
        self.specialists: Dict[str, BaseAgent] = {}

    def _get_agent_name(self) -> str:
        return "orchestrator"

    def register_specialist(self, name: str, agent: BaseAgent):
        """Register a specialist agent."""
        self.specialists[name] = agent
        logger.info("Registered specialist agent: %s", name)

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Receives user request, performs safety checks, routes to specialist,
        optionally generates response via LLM agent, checks safety again,
        updates memory, and logs evaluation metrics.
        """
        start_time = time.perf_counter()
        
        # 1. Receive User Input & Initialize state if needed
        session_id = request.session_id or self.state_manager.session_id
        request.session_id = session_id
        
        # 2. Safety Agent Pre-Check
        safety_agent = self.specialists.get("safety")
        if not safety_agent:
            return AgentResponse.error(self.name, "Safety Agent not registered")

        safety_res = safety_agent.safe_process(request)
        if safety_res.risk_level in ("high", "critical") or not safety_res.success:
            # Escalation: bypass regular routing, return safe crisis response
            latency = (time.perf_counter() - start_time) * 1000
            turn = self.state_manager.record_turn(
                request_id=request.request_id,
                user_text=request.text,
                intent="crisis",
                intent_confidence=1.0,
                dispatched_agent="safety",
                response_text=safety_res.response,
                response_confidence=1.0,
                risk_level=safety_res.risk_level,
                latency_ms=latency,
                errors=safety_res.errors
            )
            # Update memory agent if present
            memory_agent = self.specialists.get("memory")
            if memory_agent:
                memory_agent.safe_process(AgentRequest(
                    text=f"User: {request.text} | ZARA: {safety_res.response}",
                    session_id=session_id,
                    metadata={"purpose": "save_interaction", "risk": safety_res.risk_level}
                ))
            
            return AgentResponse(
                success=True,
                agent=self.name,
                intent="crisis",
                response=safety_res.response,
                confidence=1.0,
                risk_level=safety_res.risk_level,
                metadata={"safety_assessment": safety_res.metadata}
            )

        # 3. Intent Routing
        intent, intent_conf, target_agent_name = self.router.classify(request.text)
        request.metadata["intent"] = intent
        request.metadata["intent_confidence"] = intent_conf
        
        # 4. Memory Retrieval (Retrieve relevant past turns/context)
        memory_agent = self.specialists.get("memory")
        recent_context = ""
        if memory_agent:
            mem_query_res = memory_agent.safe_process(AgentRequest(
                text=request.text,
                session_id=session_id,
                metadata={"purpose": "retrieve", "limit": 5}
            ))
            if mem_query_res.success:
                recent_context = mem_query_res.metadata.get("context", "")
                request.metadata["context"] = recent_context
        
        if not recent_context:
            request.metadata["context"] = self.state_manager.get_recent_context()

        # 5. Specialist Agent selection
        specialist = self.specialists.get(target_agent_name)
        if not specialist:
            logger.warning("Specialist agent %s not found. Falling back to LLM agent.", target_agent_name)
            target_agent_name = "llm"
            specialist = self.specialists.get("llm")

        if not specialist:
            return AgentResponse.error(self.name, f"Specialist agent '{target_agent_name}' and LLM agent are not available.")

        # Process via Specialist Agent
        specialist_res = specialist.safe_process(request)
        
        # 6. Optional LLM Agent validation/generation if specialist didn't produce direct text
        # (For psychologist/tools, they might output a script key or structured action)
        final_text = specialist_res.response
        response_source = specialist_res.agent
        confidence = specialist_res.confidence
        tool_calls = specialist_res.tool_calls
        
        # If intent requires tools and tool agent is selected
        if target_agent_name == "tool" and specialist_res.success:
            # We must route tool calls to Tool Agent
            tool_agent = self.specialists.get("tool")
            if tool_agent:
                # Tool Execution flow
                # Before execution: check permissions
                for tool_call in tool_calls:
                    perm_req = AgentRequest(
                        text="",
                        session_id=session_id,
                        metadata={
                            "purpose": "tool_check",
                            "tool_name": tool_call.get("tool_name", ""),
                            "risk_level": tool_call.get("risk_level", "low"),
                            "action_name": tool_call.get("action_name", "")
                        }
                    )
                    perm_res = safety_agent.safe_process(perm_req)
                    if not perm_res.success:
                        # Denied!
                        final_text = f"Tool execution blocked: {perm_res.response}"
                        tool_calls = []
                        break
                
                if tool_calls:
                    # Execute tool
                    tool_exec_res = tool_agent.safe_process(AgentRequest(
                        text=request.text,
                        session_id=session_id,
                        metadata={"purpose": "execute", "tool_calls": tool_calls}
                    ))
                    final_text = tool_exec_res.response
                    confidence = tool_exec_res.confidence
                    
        elif not final_text:
            # Fall back to LLM agent
            llm_agent = self.specialists.get("llm")
            if llm_agent:
                llm_res = llm_agent.safe_process(request)
                final_text = llm_res.response
                response_source = llm_res.agent
                confidence = llm_res.confidence

        # 7. Safety Validation (Post-Check: filter diagnosis/medical boundaries)
        # Use Safety Agent response filtering
        if hasattr(safety_agent, "filter_response"):
            final_text = safety_agent.filter_response(final_text)

        # 8. Memory Update
        if memory_agent:
            memory_agent.safe_process(AgentRequest(
                text=f"User: {request.text} | ZARA: {final_text}",
                session_id=session_id,
                metadata={
                    "purpose": "save_interaction",
                    "risk": specialist_res.risk_level,
                    "intent": intent
                }
            ))

        # 9. Evaluation Logging
        latency = (time.perf_counter() - start_time) * 1000
        
        # Log to state manager
        self.state_manager.record_turn(
            request_id=request.request_id,
            user_text=request.text,
            intent=intent,
            intent_confidence=intent_conf,
            dispatched_agent=response_source,
            response_text=final_text,
            response_confidence=confidence,
            risk_level=specialist_res.risk_level,
            latency_ms=latency,
            fallback_used=(response_source == "llm" and target_agent_name != "llm")
        )

        return AgentResponse(
            success=True,
            agent=self.name,
            intent=intent,
            response=final_text,
            confidence=confidence,
            risk_level=specialist_res.risk_level,
            tool_calls=tool_calls,
            metadata={
                "selected_agent": response_source,
                "latency_ms": latency,
                "session_id": session_id
            }
        )
