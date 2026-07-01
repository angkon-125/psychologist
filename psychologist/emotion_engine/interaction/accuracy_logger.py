"""
Accuracy Logger

Logs every interaction locally for accuracy analysis.
Writes to logs/accuracy_log.jsonl (one JSON object per line).

Privacy: respects a configurable flag. When disabled, only metadata
(timestamps, counts) is logged — no transcript content.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("zara.accuracy_logger")


class AccuracyLogger:
    """
    Logs interaction data for accuracy measurement.

    Usage:
        logger = AccuracyLogger()
        logger.log_interaction({
            "input_mode": "text",
            "transcript": "I feel anxious",
            "detected_intent": "fear",
            "confidence_scores": {...},
            "selected_backend": "emotion_engine",
            "response_type": "supportive",
            "fallback_used": False,
            "correction": None,
            "error_state": None,
        })
    """

    def __init__(self, log_dir: Optional[str] = None, privacy_enabled: bool = True):
        if log_dir:
            self._log_dir = Path(log_dir)
        else:
            self._log_dir = Path(__file__).parent.parent.parent / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._log_dir / "accuracy_log.jsonl"
        self._privacy_enabled = privacy_enabled

    @property
    def privacy_enabled(self) -> bool:
        return self._privacy_enabled

    @privacy_enabled.setter
    def privacy_enabled(self, value: bool):
        self._privacy_enabled = value

    def log_interaction(self, entry: Dict):
        """
        Log a single interaction entry.

        Expected keys:
            input_mode, transcript, detected_intent, confidence_scores,
            selected_backend, response_type, fallback_used, correction,
            error_state
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "input_mode": entry.get("input_mode", "unknown"),
            "detected_intent": entry.get("detected_intent", ""),
            "confidence_scores": entry.get("confidence_scores", {}),
            "selected_backend": entry.get("selected_backend", "unknown"),
            "response_type": entry.get("response_type", ""),
            "fallback_used": entry.get("fallback_used", False),
            "correction": entry.get("correction", None),
            "error_state": entry.get("error_state", None),
        }

        # Only log transcript if privacy allows
        if self._privacy_enabled:
            record["transcript"] = entry.get("transcript", "")
            record["response_text"] = entry.get("response_text", "")[:500]
        else:
            record["transcript"] = "[redacted]"
            record["response_text"] = "[redacted]"

        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("Failed to log interaction: %s", e)

    def get_recent(self, n: int = 50) -> List[Dict]:
        """Return the last N log entries."""
        try:
            if not self._log_path.exists():
                return []
            lines = []
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            lines.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            return lines[-n:]
        except Exception:
            return []

    def get_summary(self) -> Dict:
        """
        Return aggregate accuracy statistics from the log.

        Returns:
            Dict with total interactions, average confidence per category,
            correction_count, fallback_count, error_count.
        """
        entries = self._load_all()
        total = len(entries)

        if total == 0:
            return {
                "total_interactions": 0,
                "avg_transcript_confidence": 0.0,
                "avg_intent_confidence": 0.0,
                "avg_response_confidence": 0.0,
                "avg_safety_confidence": 0.0,
                "avg_tool_confidence": 0.0,
                "avg_overall_confidence": 0.0,
                "correction_count": 0,
                "fallback_count": 0,
                "error_count": 0,
                "low_confidence_count": 0,
            }

        # Accumulate confidence scores
        sums = {
            "transcript_confidence": 0.0,
            "intent_confidence": 0.0,
            "response_confidence": 0.0,
            "safety_confidence": 0.0,
            "tool_confidence": 0.0,
            "overall_confidence": 0.0,
        }
        correction_count = 0
        fallback_count = 0
        error_count = 0
        low_conf_count = 0

        for entry in entries:
            scores = entry.get("confidence_scores", {})
            for key in sums:
                sums[key] += scores.get(key, 0.0)

            if entry.get("correction"):
                correction_count += 1
            if entry.get("fallback_used"):
                fallback_count += 1
            if entry.get("error_state"):
                error_count += 1
            if scores.get("is_low_confidence", False):
                low_conf_count += 1

        return {
            "total_interactions": total,
            "avg_transcript_confidence": round(sums["transcript_confidence"] / total, 3),
            "avg_intent_confidence": round(sums["intent_confidence"] / total, 3),
            "avg_response_confidence": round(sums["response_confidence"] / total, 3),
            "avg_safety_confidence": round(sums["safety_confidence"] / total, 3),
            "avg_tool_confidence": round(sums["tool_confidence"] / total, 3),
            "avg_overall_confidence": round(sums["overall_confidence"] / total, 3),
            "correction_count": correction_count,
            "fallback_count": fallback_count,
            "error_count": error_count,
            "low_confidence_count": low_conf_count,
        }

    def clear_log(self):
        """Clear the accuracy log file (for testing)."""
        try:
            if self._log_path.exists():
                self._log_path.unlink()
        except Exception as e:
            logger.warning("Failed to clear log: %s", e)

    # ── Internal ─────────────────────────────────────────────────

    def _load_all(self) -> List[Dict]:
        """Load all log entries."""
        try:
            if not self._log_path.exists():
                return []
            entries = []
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            return entries
        except Exception:
            return []
