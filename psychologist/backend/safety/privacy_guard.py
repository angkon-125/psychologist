"""
Privacy Guard

Filters personally identifiable information (PII) and sensitive data
before it is stored in memory, written to logs, or transmitted externally.

Responsibilities:
  - Detect PII patterns (email, phone, SSN, credit card, passwords, etc.)
  - Redact or mask detected PII before storage
  - Enforce privacy boundaries on memory writes
  - Provide a sanitization pipeline for the Memory Agent and logging system
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("zara.safety.privacy")


# ── PII Patterns ───────────────────────────────────────────────────

_PII_PATTERNS: Dict[str, re.Pattern] = {
    # Credit card MUST come before phone (phone pattern can match card numbers)
    "credit_card": re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    ),
    "ssn": re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b"
    ),
    "email": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    ),
    "ip_address": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
    "password_pattern": re.compile(
        r"(?:password|passwd|pwd|secret|token|api_key)\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
    # Phone last — broadest numeric pattern
    "phone": re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    ),
}

# Fields that should NEVER be stored regardless of content
_BLOCKED_MEMORY_FIELDS = {
    "password", "secret", "token", "api_key", "credit_card",
    "ssn", "social_security", "pin", "cvv", "private_key",
}


class PrivacyGuard:
    """
    Scans text and data structures for PII, redacts sensitive content,
    and blocks storage of prohibited fields.
    """

    def __init__(self, redaction_marker: str = "[REDACTED]"):
        self._redaction_marker = redaction_marker

    def scan_text(self, text: str) -> Dict[str, Any]:
        """
        Scan text for PII patterns.

        Returns:
            Dict with:
              - has_pii: bool
              - detected_types: list of PII type strings found
              - redacted_text: text with PII replaced by redaction marker
              - match_count: total number of PII matches
        """
        if not text:
            return {
                "has_pii": False,
                "detected_types": [],
                "redacted_text": text,
                "match_count": 0,
            }

        detected_types = []
        match_count = 0
        redacted = text

        for pii_type, pattern in _PII_PATTERNS.items():
            matches = pattern.findall(redacted)
            if matches:
                detected_types.append(pii_type)
                match_count += len(matches)
                redacted = pattern.sub(self._redaction_marker, redacted)

        return {
            "has_pii": len(detected_types) > 0,
            "detected_types": detected_types,
            "redacted_text": redacted,
            "match_count": match_count,
        }

    def sanitize_for_storage(self, text: str) -> str:
        """
        Redact all PII from text before storing in memory.

        Args:
            text: Raw user or assistant text.

        Returns:
            Sanitized text with PII replaced by [REDACTED].
        """
        result = self.scan_text(text)
        return result["redacted_text"]

    def is_field_blocked(self, field_name: str) -> bool:
        """
        Check if a field name is in the blocked storage list.

        Args:
            field_name: The metadata or data field name.

        Returns:
            True if this field must NOT be stored.
        """
        return field_name.lower().strip() in _BLOCKED_MEMORY_FIELDS

    def sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove blocked fields and redact PII from metadata values
        before persisting to memory.

        Args:
            metadata: The metadata dict to sanitize.

        Returns:
            A new sanitized metadata dict.
        """
        sanitized = {}
        for key, value in metadata.items():
            # Skip blocked fields entirely
            if self.is_field_blocked(key):
                logger.warning("Blocked field removed from storage: %s", key)
                continue

            # Redact PII from string values
            if isinstance(value, str):
                sanitized[key] = self.sanitize_for_storage(value)
            else:
                sanitized[key] = value

        return sanitized

    def check_log_safety(self, log_message: str) -> str:
        """
        Sanitize a log message to remove any accidental PII.

        Args:
            log_message: The raw log message.

        Returns:
            Sanitized log message safe for writing to log files.
        """
        return self.sanitize_for_storage(log_message)
