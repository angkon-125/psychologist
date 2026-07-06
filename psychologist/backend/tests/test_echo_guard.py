"""
Echo Guard tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.voice.echo_guard import EchoGuard


@pytest.fixture
def guard():
    return EchoGuard()


def test_initial_state(guard):
    """Guard starts disarmed."""
    assert guard.is_armed is False
    assert guard.is_echo("anything") is False


def test_arm_and_detect_echo(guard):
    """Echo detected when transcript matches spoken text."""
    guard.arm("Hello, how are you feeling today?")
    assert guard.is_armed is True
    assert guard.is_echo("Hello how are you") is True


def test_no_echo_different_text(guard):
    """No echo when transcript is completely different."""
    guard.arm("Let us try a breathing exercise together")
    assert guard.is_echo("I feel stressed about work") is False


def test_no_echo_when_disarmed(guard):
    """No echo detection when guard is not armed."""
    assert guard.is_echo("Hello how are you") is False


def test_disarm(guard):
    """Disarming clears the guard."""
    guard.arm("Hello, how are you feeling today?")
    assert guard.is_armed is True
    guard.disarm()
    assert guard.is_armed is False
    assert guard.is_echo("Hello how are you") is False


def test_short_text_not_armed(guard):
    """Text too short does not arm the guard."""
    guard.arm("Hi")
    assert guard.is_armed is False


def test_empty_text_not_armed(guard):
    """Empty text does not arm the guard."""
    guard.arm("")
    assert guard.is_armed is False


def test_partial_echo_above_threshold(guard):
    """Partial overlap above threshold is detected as echo."""
    guard.arm("Remember to breathe in slowly and then breathe out")
    assert guard.is_echo("breathe in slowly breathe out") is True


def test_status_dict(guard):
    """Status returns correct diagnostic info."""
    guard.arm("Hello world test sentence here")
    status = guard.get_status()
    assert status["armed"] is True
    assert status["spoken_word_count"] > 0
    assert len(status["spoken_text_preview"]) > 0
