"""
Base Agent — Abstract Base Class

Every agent in the ZARA system inherits from BaseAgent.
This ensures uniform interfaces, health checks, logging, and
structured responses across all agents.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .schemas import AgentRequest, AgentResponse


class BaseAgent(ABC):
    """
    Abstract base for all ZARA agents.

    Subclasses must implement:
      - process(request) -> AgentResponse
      - _get_agent_name() -> str

    Optionally override:
      - health_check() -> dict
      - get_info() -> dict
    """

    def __init__(self):
        self._name = self._get_agent_name()
        self._logger = logging.getLogger(f"zara.agent.{self._name}")
        self._request_count = 0
        self._error_count = 0
        self._total_latency_ms = 0.0
        self._initialized = False

    # ── Abstract interface ────────────────────────────────────────

    @abstractmethod
    def _get_agent_name(self) -> str:
        """Return the unique name of this agent."""
        ...

    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a request and return a structured response.

        This is the main entry point for agent logic. Must never raise
        unhandled exceptions — wrap all logic and return AgentResponse.error()
        on failure.
        """
        ...

    # ── Safe execution wrapper ────────────────────────────────────

    def safe_process(self, request: AgentRequest) -> AgentResponse:
        """
        Execute process() with timing, logging, and error handling.

        Use this instead of process() directly for production calls.
        """
        self._request_count += 1
        start = time.perf_counter()

        try:
            self._logger.info(
                "Processing request %s (total: %d)",
                request.request_id,
                self._request_count,
            )
            response = self.process(request)
            response.agent = self._name

            elapsed_ms = (time.perf_counter() - start) * 1000
            self._total_latency_ms += elapsed_ms

            response.metadata["latency_ms"] = round(elapsed_ms, 2)
            response.metadata["request_id"] = request.request_id

            self._logger.info(
                "Completed request %s in %.1fms (confidence=%.2f, risk=%s)",
                request.request_id,
                elapsed_ms,
                response.confidence,
                response.risk_level,
            )
            return response

        except Exception as e:
            self._error_count += 1
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._logger.error(
                "Failed request %s after %.1fms: %s",
                request.request_id,
                elapsed_ms,
                e,
                exc_info=True,
            )
            error_response = AgentResponse.error(
                agent=self._name,
                message=f"Agent error: {e}",
                intent=request.metadata.get("intent", ""),
            )
            error_response.metadata["latency_ms"] = round(elapsed_ms, 2)
            error_response.metadata["request_id"] = request.request_id
            return error_response

    # ── Health and info ───────────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    def health_check(self) -> Dict[str, Any]:
        """
        Return the health status of this agent.

        Override in subclasses to add component-specific checks
        (e.g., database connectivity, model availability).
        """
        avg_latency = (
            self._total_latency_ms / self._request_count
            if self._request_count > 0
            else 0.0
        )
        return {
            "agent": self._name,
            "status": "healthy",
            "initialized": self._initialized,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "avg_latency_ms": round(avg_latency, 2),
        }

    def get_info(self) -> Dict[str, Any]:
        """Return agent info for debugging."""
        return {
            "name": self._name,
            "type": self.__class__.__name__,
            "initialized": self._initialized,
            "request_count": self._request_count,
            "error_count": self._error_count,
        }

    def initialize(self) -> bool:
        """
        Initialize the agent. Called once during startup.

        Override in subclasses for setup that may fail (DB connections, etc.).
        Returns True if initialization was successful.
        """
        self._initialized = True
        self._logger.info("Agent %s initialized", self._name)
        return True
