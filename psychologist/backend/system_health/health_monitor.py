"""
Health Monitor — System Health

Aggregates all subsystem checkers into a unified health report.
Caches results for 5 seconds to avoid excessive I/O.
"""

import time
import logging
from typing import Dict, List, Optional

from .schemas import SubsystemStatus, OverallHealth
from .model_checker import ModelChecker
from .resource_monitor import ResourceMonitor
from .latency_tracker import LatencyTracker
from .dependency_checker import DependencyChecker
from .degradation import DegradationManager

logger = logging.getLogger("zara.health.monitor")

_CACHE_TTL_SECONDS = 5.0


class HealthMonitor:
    """
    Central health aggregator for ZARA.

    Usage:
        monitor = HealthMonitor(specialists)
        health = monitor.check_all()
    """

    def __init__(
        self,
        specialists: Optional[Dict] = None,
        db_path: str = "",
        ollama_url: str = "",
    ):
        self._model_checker = ModelChecker(base_url=ollama_url or None)
        self._resource_monitor = ResourceMonitor()
        self._latency_tracker = LatencyTracker()
        self._dependency_checker = DependencyChecker(
            specialists=specialists, db_path=db_path
        )
        self._degradation_manager = DegradationManager()

        self._start_time = time.time()
        self._cache: Optional[OverallHealth] = None
        self._cache_time: float = 0.0

    @property
    def model_checker(self) -> ModelChecker:
        return self._model_checker

    @property
    def resource_monitor(self) -> ResourceMonitor:
        return self._resource_monitor

    @property
    def latency_tracker(self) -> LatencyTracker:
        return self._latency_tracker

    @property
    def dependency_checker(self) -> DependencyChecker:
        return self._dependency_checker

    @property
    def degradation_manager(self) -> DegradationManager:
        return self._degradation_manager

    def update_specialists(self, specialists: Dict) -> None:
        """Update the specialists reference (called after orchestrator init)."""
        self._dependency_checker.set_specialists(specialists)

    def check_all(self, use_cache: bool = True) -> OverallHealth:
        """
        Run all health checks and return aggregated report.

        Args:
            use_cache: If True, return cached result if < 5s old

        Returns:
            OverallHealth with all subsystem statuses
        """
        # Check cache
        if use_cache and self._cache:
            age = time.time() - self._cache_time
            if age < _CACHE_TTL_SECONDS:
                return self._cache

        all_subsystems: List[SubsystemStatus] = []

        # 1. Model checks
        try:
            all_subsystems.append(self._model_checker.check_ollama())
            all_subsystems.append(self._model_checker.check_default_model())
        except Exception as e:
            logger.debug("Model check failed: %s", e)
            all_subsystems.append(SubsystemStatus(
                name="ollama", status="unknown", message=f"Check failed: {e}",
            ))

        # 2. Dependency checks
        try:
            dep_statuses = self._dependency_checker.check_all()
            all_subsystems.extend(dep_statuses)
        except Exception as e:
            logger.debug("Dependency check failed: %s", e)

        # 3. Evaluate degradations
        degraded_features = self._degradation_manager.evaluate(all_subsystems)
        recommendations = self._degradation_manager.get_recommendations()

        # 4. Determine overall status
        overall = self._determine_overall_status(all_subsystems)

        health = OverallHealth(
            status=overall,
            subsystems=all_subsystems,
            uptime_seconds=time.time() - self._start_time,
            degraded_features=degraded_features,
            recommendations=recommendations,
        )

        # Cache result
        self._cache = health
        self._cache_time = time.time()

        return health

    def check_subsystem(self, name: str) -> SubsystemStatus:
        """Check a single subsystem by name."""
        check_map = {
            "ollama": self._model_checker.check_ollama,
            "default_model": self._model_checker.check_default_model,
            "stt": self._dependency_checker.check_stt,
            "tts": self._dependency_checker.check_tts,
            "sqlite_memory": self._dependency_checker.check_sqlite_memory,
            "episodic_memory": self._dependency_checker.check_episodic_memory,
            "graph_memory": self._dependency_checker.check_graph_memory,
            "vector_store": self._dependency_checker.check_vector_store,
            "tools": self._dependency_checker.check_tools_registry,
            "safety": self._dependency_checker.check_safety_config,
            "backend_api": self._dependency_checker.check_backend_api,
        }
        fn = check_map.get(name)
        if fn:
            try:
                return fn()
            except Exception as e:
                return SubsystemStatus(
                    name=name, status="unknown",
                    message=f"Check failed: {e}",
                )
        return SubsystemStatus(
            name=name, status="unknown",
            message=f"Unknown subsystem: {name}",
        )

    def get_degraded_features(self) -> List[str]:
        """Return list of currently degraded feature descriptions."""
        return self._degradation_manager.get_all_degraded()

    def get_recommendations(self) -> List[str]:
        """Return fix recommendations for degraded subsystems."""
        return self._degradation_manager.get_recommendations()

    def _determine_overall_status(self, subsystems: List[SubsystemStatus]) -> str:
        """
        Determine overall health from subsystem statuses.

        - All healthy/unknown -> "healthy"
        - Any degraded (none unavailable) -> "degraded"
        - Any unavailable -> "unavailable"
        """
        if not subsystems:
            return "unknown"

        has_unavailable = False
        has_degraded = False

        for s in subsystems:
            if s.status == "unavailable":
                has_unavailable = True
            elif s.status == "degraded":
                has_degraded = True

        if has_unavailable:
            return "unavailable"
        if has_degraded:
            return "degraded"
        return "healthy"
