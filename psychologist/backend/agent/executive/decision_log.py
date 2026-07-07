"""
Decision Logger — Executive Brain

Debug-only audit trail for executive decisions.
Appends DecisionRecords to an in-memory list and flushes to JSONL.
Only active when debug mode is enabled.
"""

import json
import logging
import os
from typing import List, Optional

from .schemas import DecisionRecord

logger = logging.getLogger("zara.executive.decision_log")


class DecisionLogger:
    """
    Append-only decision audit log.

    Usage:
        logger = DecisionLogger(debug_mode=True, log_dir="logs")
        logger.log(decision_record)
        recent = logger.get_recent(n=10)
    """

    def __init__(self, debug_mode: bool = False, log_dir: str = "logs"):
        """
        Initialize decision logger.

        Args:
            debug_mode: If False, logging is disabled (no-op)
            log_dir: Directory for JSONL log file
        """
        self.debug_mode = debug_mode
        self.log_dir = log_dir
        self._records: List[DecisionRecord] = []
        self._file_path = os.path.join(log_dir, "decision_log.jsonl")

    def log(self, decision: DecisionRecord) -> None:
        """
        Log a decision record.

        Args:
            decision: DecisionRecord to log
        """
        if not self.debug_mode:
            return

        self._records.append(decision)
        self._flush_to_file(decision)
        logger.debug(
            "Logged decision %s (intent=%s, confidence=%.2f)",
            decision.decision_id, decision.intent, decision.confidence,
        )

    def get_recent(self, n: int = 10) -> List[DecisionRecord]:
        """
        Get the most recent N decision records.

        Args:
            n: Number of records to return

        Returns:
            List of DecisionRecord (most recent last)
        """
        if not self.debug_mode:
            return []
        return self._records[-n:]

    def get_for_request(self, request_id: str) -> Optional[DecisionRecord]:
        """
        Get the decision record for a specific request.

        Args:
            request_id: Request identifier

        Returns:
            DecisionRecord if found, None otherwise
        """
        if not self.debug_mode:
            return None
        for record in reversed(self._records):
            if record.request_id == request_id:
                return record
        return None

    def _flush_to_file(self, decision: DecisionRecord) -> None:
        """Append a single decision to the JSONL file."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self._file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(decision.to_dict()) + "\n")
        except Exception as e:
            logger.error("Failed to write decision log: %s", e)
