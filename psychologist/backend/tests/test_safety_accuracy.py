"""
Safety Accuracy tests — Data-driven from evaluation/test_cases/safety_tests.json

Verifies crisis detection, tool permissions, and privacy filtering.
"""

import pytest
import json
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.safety.crisis_detector import CrisisDetector
from backend.safety.permission_checker import PermissionChecker
from backend.safety.privacy_guard import PrivacyGuard


@pytest.fixture(scope="module")
def crisis():
    return CrisisDetector()


@pytest.fixture(scope="module")
def permissions():
    return PermissionChecker()


@pytest.fixture(scope="module")
def privacy():
    return PrivacyGuard()


def _load_safety_tests():
    test_file = os.path.join(
        os.path.dirname(__file__), "..", "evaluation", "test_cases", "safety_tests.json"
    )
    with open(test_file, "r", encoding="utf-8") as f:
        return json.load(f)


_safety_data = None

def _get_safety_data():
    global _safety_data
    if _safety_data is None:
        _safety_data = _load_safety_tests()
    return _safety_data


# ── Crisis Detection Tests ──────────────────────────────────────

@pytest.mark.parametrize(
    "test_case",
    _load_safety_tests()["crisis_tests"],
    ids=[tc["id"] for tc in _load_safety_tests()["crisis_tests"]],
)
def test_crisis_detection(crisis, test_case):
    """Crisis inputs must be detected with correct risk level."""
    result = crisis.assess(test_case["input"])
    
    if test_case["expected_escalate"]:
        assert result["should_escalate"] is True, (
            f"{test_case['id']}: '{test_case['input']}' should escalate"
        )
        assert result["risk_level"] in ("high", "critical"), (
            f"{test_case['id']}: risk should be high/critical, got '{result['risk_level']}'"
        )
    else:
        assert result["should_escalate"] is False, (
            f"{test_case['id']}: '{test_case['input']}' should NOT escalate"
        )


# ── Tool Permission Tests ───────────────────────────────────────

@pytest.mark.parametrize(
    "test_case",
    _load_safety_tests()["tool_permission_tests"],
    ids=[tc["id"] for tc in _load_safety_tests()["tool_permission_tests"]],
)
def test_tool_permissions(permissions, test_case):
    """Tool permissions must match expected outcomes."""
    result = permissions.check_tool_permission(
        tool_name=test_case["tool_name"],
        risk_level=test_case["risk_level"],
    )
    
    assert result["permitted"] == test_case["expected_permitted"], (
        f"{test_case['id']}: tool '{test_case['tool_name']}' "
        f"permitted={result['permitted']}, expected={test_case['expected_permitted']}"
    )
    assert result["requires_confirmation"] == test_case["expected_confirmation"], (
        f"{test_case['id']}: confirmation mismatch"
    )


# ── Privacy Filter Tests ────────────────────────────────────────

@pytest.mark.parametrize(
    "test_case",
    _load_safety_tests()["privacy_tests"],
    ids=[tc["id"] for tc in _load_safety_tests()["privacy_tests"]],
)
def test_privacy_filtering(privacy, test_case):
    """Privacy guard must detect PII correctly."""
    result = privacy.scan_text(test_case["input"])
    
    assert result["has_pii"] == test_case["expected_has_pii"], (
        f"{test_case['id']}: has_pii={result['has_pii']}, "
        f"expected={test_case['expected_has_pii']}"
    )
    
    if test_case["expected_pii_types"]:
        for pii_type in test_case["expected_pii_types"]:
            assert pii_type in result["detected_types"], (
                f"{test_case['id']}: expected PII type '{pii_type}' not found. "
                f"Detected: {result['detected_types']}"
            )
