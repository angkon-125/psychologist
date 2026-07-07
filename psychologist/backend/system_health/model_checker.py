"""
Model Checker — System Health

Checks Ollama availability, model list, and default model presence.
Pure HTTP checks, no LLM calls.
"""

import time
import logging
from typing import List

from backend.config import config
from .schemas import SubsystemStatus

logger = logging.getLogger("zara.health.model_checker")


class ModelChecker:
    """
    Checks LLM model availability via Ollama HTTP API.

    Usage:
        checker = ModelChecker()
        status = checker.check_ollama()
    """

    def __init__(self, base_url: str = None, timeout: float = 3.0):
        self._base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._default_model = config.DEFAULT_MODEL

    def check_ollama(self) -> SubsystemStatus:
        """
        Check if Ollama is responding.

        Returns:
            SubsystemStatus with healthy/degraded/unavailable
        """
        start = time.perf_counter()
        try:
            import urllib.request
            import json

            url = f"{self._base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                elapsed = (time.perf_counter() - start) * 1000
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    status = "degraded" if elapsed > 2000 else "healthy"
                    return SubsystemStatus(
                        name="ollama",
                        status=status,
                        latency_ms=elapsed,
                        message=f"Ollama responding ({len(models)} models)",
                        details={"models": models, "model_count": len(models)},
                    )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.debug("Ollama check failed: %s", e)
            return SubsystemStatus(
                name="ollama",
                status="unavailable",
                latency_ms=elapsed,
                message=f"Ollama unreachable: {e}",
                fix="Start Ollama: `ollama serve`",
            )

        elapsed = (time.perf_counter() - start) * 1000
        return SubsystemStatus(
            name="ollama",
            status="unavailable",
            latency_ms=elapsed,
            message="Ollama returned unexpected response",
            fix="Check Ollama configuration",
        )

    def get_available_models(self) -> List[str]:
        """Return list of available model names."""
        status = self.check_ollama()
        return status.details.get("models", [])

    def check_default_model(self) -> SubsystemStatus:
        """Check if the default model is available in Ollama."""
        ollama_status = self.check_ollama()
        if ollama_status.status == "unavailable":
            return SubsystemStatus(
                name="default_model",
                status="unavailable",
                latency_ms=ollama_status.latency_ms,
                message=f"Cannot check model '{self._default_model}': Ollama unavailable",
                fix=ollama_status.fix,
            )

        models = ollama_status.details.get("models", [])
        model_names_lower = [m.lower() for m in models]
        if self._default_model.lower() in model_names_lower:
            return SubsystemStatus(
                name="default_model",
                status="healthy",
                latency_ms=ollama_status.latency_ms,
                message=f"Model '{self._default_model}' is available",
            )
        else:
            return SubsystemStatus(
                name="default_model",
                status="degraded",
                latency_ms=ollama_status.latency_ms,
                message=f"Model '{self._default_model}' not found. Available: {models}",
                fix=f"Pull model: `ollama pull {self._default_model}`",
            )
