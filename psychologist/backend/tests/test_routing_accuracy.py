"""
Routing Accuracy tests — Data-driven from evaluation/test_cases/routing_tests.json

Verifies the Intent Router classifies all test cases correctly.
"""

import pytest
import json
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.router import IntentRouter


@pytest.fixture(scope="module")
def router():
    return IntentRouter()


def _load_routing_tests():
    test_file = os.path.join(
        os.path.dirname(__file__), "..", "evaluation", "test_cases", "routing_tests.json"
    )
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["test_cases"]


@pytest.mark.parametrize(
    "test_case",
    _load_routing_tests(),
    ids=[tc["id"] for tc in _load_routing_tests()],
)
def test_routing_accuracy(router, test_case):
    """Each test case must classify to the expected intent."""
    intent, confidence, agent = router.classify(test_case["input"])
    assert intent == test_case["expected_intent"], (
        f"{test_case['id']}: '{test_case['input']}' → got '{intent}', "
        f"expected '{test_case['expected_intent']}'"
    )
    assert agent == test_case["expected_agent"], (
        f"{test_case['id']}: agent mismatch → got '{agent}', "
        f"expected '{test_case['expected_agent']}'"
    )
    assert confidence > 0.0, f"{test_case['id']}: confidence must be > 0"
