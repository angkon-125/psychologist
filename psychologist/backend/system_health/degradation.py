"""
Degradation Manager — System Health

Rules-based feature degradation when subsystems are unavailable.
Provides natural language advice for the Executive Brain to use
when informing the user about degraded capabilities.
"""

import logging
from typing import Dict, List

from .schemas import SubsystemStatus

logger = logging.getLogger("zara.health.degradation")


# Mapping: subsystem name -> (feature_label, fallback_description, advice)
_DEGRADATION_RULES: Dict[str, Dict[str, str]] = {
    "ollama": {
        "feature": "LLM",
        "fallback": "Using EmotionEngine fallback for responses",
        "advice": "Local LLM is unavailable, so I'm using the fallback engine.",
        "fix": "Start Ollama with: ollama serve",
    },
    "default_model": {
        "feature": "LLM Model",
        "fallback": "Default model missing, using alternative",
        "advice": "The configured language model isn't available. I'm using an alternative.",
        "fix": "Pull the default model: ollama pull <model_name>",
    },
    "stt": {
        "feature": "Voice Input",
        "fallback": "Voice transcription degraded, text mode available",
        "advice": "Voice transcription is degraded. Text mode still works perfectly.",
        "fix": "Install faster-whisper for full STT support",
    },
    "tts": {
        "feature": "Voice Output",
        "fallback": "Voice output unavailable, text-only mode",
        "advice": "Voice output is unavailable right now. I'll respond in text.",
        "fix": "Install pyttsx3 or Piper for voice output",
    },
    "sqlite_memory": {
        "feature": "Long-term Memory",
        "fallback": "Session-only memory, no long-term recall",
        "advice": "I can answer, but I may not remember this session later.",
        "fix": "Check database file permissions and disk space",
    },
    "episodic_memory": {
        "feature": "Episodic Memory",
        "fallback": "Timeline and episode recall unavailable",
        "advice": "Episodic memory is unavailable. Timeline features are paused.",
        "fix": "Re-initialize the memory agent",
    },
    "graph_memory": {
        "feature": "Knowledge Graph",
        "fallback": "Graph-based reasoning unavailable",
        "advice": "Knowledge graph is offline. Entity relationships won't be tracked.",
        "fix": "Re-initialize the memory agent",
    },
    "vector_store": {
        "feature": "Semantic Search",
        "fallback": "Using keyword matching instead of semantic search",
        "advice": "Semantic search is using keyword fallback. Results may be less precise.",
        "fix": "Install ChromaDB or FAISS for full semantic search",
    },
    "tools": {
        "feature": "Tool Execution",
        "fallback": "Responding without tool use",
        "advice": "Tools are unavailable. I'll answer directly without executing tools.",
        "fix": "Check tool agent initialization",
    },
    "safety": {
        "feature": "Safety Layer",
        "fallback": "Running without safety pre-filter",
        "advice": "Safety layer is degraded. Responses may not be pre-filtered.",
        "fix": "Re-initialize the safety agent",
    },
}


class DegradationManager:
    """
    Manages feature degradation based on subsystem health.

    Usage:
        manager = DegradationManager()
        degraded = manager.evaluate(subsystem_statuses)
        advice = manager.get_fallback_advice("stt")
    """

    def __init__(self):
        self._active_degradations: Dict[str, str] = {}

    def evaluate(self, subsystems: List[SubsystemStatus]) -> List[str]:
        """
        Evaluate which features are degraded based on subsystem statuses.

        Args:
            subsystems: List of SubsystemStatus from dependency checker

        Returns:
            List of active degradation descriptions
        """
        self._active_degradations.clear()
        degraded_features = []

        for status in subsystems:
            if status.status in ("unavailable", "degraded"):
                rule = _DEGRADATION_RULES.get(status.name)
                if rule:
                    self._active_degradations[status.name] = rule["fallback"]
                    degraded_features.append(rule["fallback"])

        logger.debug("Active degradations: %s", list(self._active_degradations.keys()))
        return degraded_features

    def get_fallback_advice(self, feature_or_subsystem: str) -> str:
        """
        Get natural language advice for a degraded feature.

        Args:
            feature_or_subsystem: Either the subsystem name (e.g. "stt")
                                  or feature name (e.g. "Voice Input")

        Returns:
            Natural language string for ZARA to use in responses
        """
        # Try direct subsystem name match
        rule = _DEGRADATION_RULES.get(feature_or_subsystem)
        if rule:
            return rule["advice"]

        # Try feature name match
        for subsystem_name, r in _DEGRADATION_RULES.items():
            if r["feature"].lower() == feature_or_subsystem.lower():
                return r["advice"]

        return f"{feature_or_subsystem} is experiencing issues."

    def is_degraded(self, feature_or_subsystem: str) -> bool:
        """Check if a feature or subsystem is currently degraded."""
        if feature_or_subsystem in self._active_degradations:
            return True
        # Check by feature name
        for subsystem_name, rule in _DEGRADATION_RULES.items():
            if rule["feature"].lower() == feature_or_subsystem.lower():
                return subsystem_name in self._active_degradations
        return False

    def get_fix_suggestion(self, subsystem_name: str) -> str:
        """Get fix suggestion for a subsystem."""
        rule = _DEGRADATION_RULES.get(subsystem_name)
        if rule:
            return rule.get("fix", "")
        return ""

    def get_all_degraded(self) -> Dict[str, str]:
        """Return dict of all currently degraded subsystems and their fallback descriptions."""
        return dict(self._active_degradations)

    def get_recommendations(self) -> List[str]:
        """Return list of fix recommendations for all degraded subsystems."""
        recs = []
        for subsystem_name in self._active_degradations:
            fix = self.get_fix_suggestion(subsystem_name)
            if fix:
                recs.append(fix)
        return recs
