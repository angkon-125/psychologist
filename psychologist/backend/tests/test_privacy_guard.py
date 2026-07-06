"""
Privacy Guard tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.safety.privacy_guard import PrivacyGuard


@pytest.fixture
def guard():
    return PrivacyGuard()


def test_no_pii_in_clean_text(guard):
    """Clean text passes through without redaction."""
    result = guard.scan_text("I feel happy today")
    assert result["has_pii"] is False
    assert result["redacted_text"] == "I feel happy today"
    assert result["match_count"] == 0


def test_email_detected_and_redacted(guard):
    """Email addresses are detected and redacted."""
    result = guard.scan_text("My email is john@example.com and I feel sad")
    assert result["has_pii"] is True
    assert "email" in result["detected_types"]
    assert "john@example.com" not in result["redacted_text"]
    assert "[REDACTED]" in result["redacted_text"]


def test_credit_card_detected(guard):
    """Credit card numbers are detected."""
    result = guard.scan_text("My card is 4111-1111-1111-1111")
    assert result["has_pii"] is True
    assert "credit_card" in result["detected_types"]


def test_ssn_detected(guard):
    """SSN patterns are detected."""
    result = guard.scan_text("My SSN is 123-45-6789")
    assert result["has_pii"] is True
    assert "ssn" in result["detected_types"]


def test_password_pattern_detected(guard):
    """Password assignments are detected."""
    result = guard.scan_text("password: mySecret123")
    assert result["has_pii"] is True
    assert "password_pattern" in result["detected_types"]


def test_sanitize_for_storage(guard):
    """Full sanitization pipeline redacts all PII."""
    sanitized = guard.sanitize_for_storage("Contact me at test@mail.com or call 555-1234")
    assert "test@mail.com" not in sanitized
    assert "[REDACTED]" in sanitized


def test_blocked_fields(guard):
    """Sensitive field names are blocked."""
    assert guard.is_field_blocked("password") is True
    assert guard.is_field_blocked("api_key") is True
    assert guard.is_field_blocked("secret") is True
    assert guard.is_field_blocked("name") is False
    assert guard.is_field_blocked("intent") is False


def test_sanitize_metadata(guard):
    """Metadata sanitization removes blocked fields and redacts PII."""
    metadata = {
        "intent": "emotional_support",
        "password": "secret123",
        "note": "Email is test@mail.com",
    }
    sanitized = guard.sanitize_metadata(metadata)
    assert "password" not in sanitized
    assert "intent" in sanitized
    assert "test@mail.com" not in sanitized["note"]


def test_empty_text(guard):
    """Empty text returns clean result."""
    result = guard.scan_text("")
    assert result["has_pii"] is False
    assert result["redacted_text"] == ""


def test_log_safety(guard):
    """Log sanitization removes PII from log messages."""
    sanitized = guard.check_log_safety("User token=abc123xyz said hello")
    assert "abc123xyz" not in sanitized
