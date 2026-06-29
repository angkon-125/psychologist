"""
Simple in-memory rate limiter for the ZARA API.

Implements a sliding-window token bucket per client IP.
No external dependencies — suitable for offline-first operation.

Usage in Flask routes:
    from rate_limiter import rate_limit

    @app.route("/api/something", methods=["POST"])
    @rate_limit(app, requests=60, window_seconds=60)
    def some_endpoint():
        ...
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Dict, List, Tuple


class _TokenBucket:
    """Tracks request timestamps for a single client."""

    def __init__(self):
        self._timestamps: List[float] = []

    def allow(self, max_requests: int, window: float) -> bool:
        """Check if a new request is allowed under the rate limit."""
        now = time.monotonic()
        cutoff = now - window
        # Prune expired timestamps
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= max_requests:
            return False
        self._timestamps.append(now)
        return True


class RateLimiter:
    """
    In-memory rate limiter keyed by client identifier (typically IP).

    Not suitable for multi-process deployments without a shared backend,
    but sufficient for the single-process offline-first model.
    """

    def __init__(self):
        self._buckets: Dict[str, _TokenBucket] = defaultdict(_TokenBucket)

    def is_allowed(
        self, client_id: str, max_requests: int = 60, window_seconds: int = 60
    ) -> bool:
        """
        Check whether a request from *client_id* is allowed.

        Parameters
        ----------
        client_id : str
            Unique client identifier (e.g. request.remote_addr).
        max_requests : int
            Maximum number of requests allowed in the window.
        window_seconds : int
            Sliding window length in seconds.

        Returns
        -------
        bool
            True if the request is allowed, False if rate-limited.
        """
        return self._buckets[client_id].allow(max_requests, window_seconds)


def rate_limit(app, requests: int = 60, window_seconds: int = 60):
    """
    Decorator factory for Flask routes.

    Returns a decorator that enforces a per-IP rate limit.
    If the limit is exceeded, a 429 Too Many Requests response is returned.

    Parameters
    ----------
    app : Flask
        The Flask application (used to create the response).
    requests : int
        Max requests per window.
    window_seconds : int
        Window length in seconds.
    """
    limiter = RateLimiter()

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            from flask import request, jsonify

            client_id = request.remote_addr or "unknown"
            if not limiter.is_allowed(client_id, requests, window_seconds):
                return (
                    jsonify(
                        {
                            "error": "rate_limited",
                            "message": "Too many requests. Please slow down.",
                        }
                    ),
                    429,
                )
            return f(*args, **kwargs)

        return wrapped

    return decorator


def validate_text_input(data, field: str = "text", max_length: int = 5000) -> Tuple[bool, str, str]:
    """
    Validate a text field from a JSON request body.

    Parameters
    ----------
    data : dict or None
        The parsed JSON body from request.get_json().
    field : str
        The key to look for in the data dict.
    max_length : int
        Maximum allowed character length.

    Returns
    -------
    tuple
        (is_valid, error_message, text_value)
    """
    if data is None:
        return False, "Request body must be JSON.", ""
    text = data.get(field, "")
    if not isinstance(text, str):
        return False, f"'{field}' must be a string.", ""
    if not text.strip():
        return False, f"'{field}' must not be empty.", ""
    if len(text) > max_length:
        return False, f"'{field}' exceeds maximum length of {max_length} characters.", ""
    return True, "", text.strip()
