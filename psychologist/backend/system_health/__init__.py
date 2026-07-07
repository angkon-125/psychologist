"""
System Health Intelligence — ZARA Phase 4

Monitors all ZARA subsystems and provides health awareness.
Supports degradation detection, resource monitoring, latency tracking,
and graceful fallback recommendations.
"""

from .schemas import SubsystemStatus, OverallHealth, ResourceSnapshot, LatencyEntry
from .health_monitor import HealthMonitor
from .model_checker import ModelChecker
from .resource_monitor import ResourceMonitor
from .latency_tracker import LatencyTracker
from .dependency_checker import DependencyChecker
from .degradation import DegradationManager

__all__ = [
    "SubsystemStatus",
    "OverallHealth",
    "ResourceSnapshot",
    "LatencyEntry",
    "HealthMonitor",
    "ModelChecker",
    "ResourceMonitor",
    "LatencyTracker",
    "DependencyChecker",
    "DegradationManager",
]
