"""
System Health Routes Blueprint

Provides REST API endpoints for system health monitoring.
"""

from flask import Blueprint, jsonify
from .shared import orchestrator

system_health_bp = Blueprint("system_health_bp", __name__)

# Global health monitor instance (lazy-initialized)
_health_monitor = None


def _get_health_monitor():
    """Get or create the health monitor."""
    global _health_monitor
    if _health_monitor is None:
        from backend.system_health import HealthMonitor
        from backend.config import config
        _health_monitor = HealthMonitor(
            specialists=orchestrator.specialists,
            db_path=config.MEMORY_DB_PATH,
            ollama_url=config.OLLAMA_BASE_URL,
        )
    else:
        # Ensure specialists are up to date
        _health_monitor.update_specialists(orchestrator.specialists)
    return _health_monitor


@system_health_bp.route("/api/system/health/full", methods=["GET"])
def full_health():
    """Full system health report."""
    monitor = _get_health_monitor()
    health = monitor.check_all(use_cache=False)
    return jsonify({"success": True, **health.to_dict()})


@system_health_bp.route("/api/system/health/models", methods=["GET"])
def model_health():
    """Ollama and model status."""
    monitor = _get_health_monitor()
    ollama = monitor.model_checker.check_ollama()
    default_model = monitor.model_checker.check_default_model()
    return jsonify({
        "success": True,
        "ollama": ollama.to_dict(),
        "default_model": default_model.to_dict(),
    })


@system_health_bp.route("/api/system/health/resources", methods=["GET"])
def resource_health():
    """CPU/RAM/disk usage."""
    monitor = _get_health_monitor()
    resources = monitor.resource_monitor.get_resources()
    return jsonify({"success": True, **resources.to_dict()})


@system_health_bp.route("/api/system/health/degraded", methods=["GET"])
def degraded_health():
    """List of degraded features and advice."""
    monitor = _get_health_monitor()
    health = monitor.check_all()
    degraded = {}
    for name, fallback in monitor.degradation_manager.get_all_degraded().items():
        degraded[name] = {
            "fallback": fallback,
            "advice": monitor.degradation_manager.get_fallback_advice(name),
            "fix": monitor.degradation_manager.get_fix_suggestion(name),
        }
    return jsonify({
        "success": True,
        "overall_status": health.status,
        "degraded_features": degraded,
        "recommendations": health.recommendations,
    })


@system_health_bp.route("/api/system/latency", methods=["GET"])
def latency_data():
    """Latency tracker data."""
    monitor = _get_health_monitor()
    tracker = monitor.latency_tracker
    return jsonify({
        "success": True,
        "averages": tracker.get_all_averages(),
        "slow_endpoints": tracker.get_slow_endpoints(),
        "recent": [e.to_dict() for e in tracker.get_recent(20)],
    })
