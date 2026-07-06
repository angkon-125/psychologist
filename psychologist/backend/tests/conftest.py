"""
Shared pytest fixtures for backend test suite.

Provides a Flask test client using the backend multi-agent app.
"""

import sys
from pathlib import Path

import pytest

# Ensure the psychologist package root is importable
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@pytest.fixture(scope="session")
def backend_app():
    """Flask application from the backend multi-agent system."""
    from backend.main import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(backend_app):
    """Flask test client for the backend multi-agent system."""
    return backend_app.test_client()
