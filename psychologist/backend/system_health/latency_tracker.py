"""
Latency Tracker — System Health

Thread-safe rolling window of API call latencies.
Tracks per-endpoint averages and identifies slow endpoints.
"""

import threading
import logging
from collections import defaultdict
from typing import Dict, List

from .schemas import LatencyEntry

logger = logging.getLogger("zara.health.latency_tracker")

_MAX_ENTRIES_PER_ENDPOINT = 100


class LatencyTracker:
    """
    Thread-safe rolling window latency tracker.

    Usage:
        tracker = LatencyTracker()
        tracker.record("/api/chat", 42.5, success=True)
        avg = tracker.get_average("/api/chat")
    """

    def __init__(self, max_per_endpoint: int = _MAX_ENTRIES_PER_ENDPOINT):
        self._lock = threading.Lock()
        self._entries: Dict[str, List[LatencyEntry]] = defaultdict(list)
        self._max = max_per_endpoint

    def record(self, endpoint: str, latency_ms: float, success: bool = True) -> None:
        """Record a latency observation."""
        entry = LatencyEntry(
            endpoint=endpoint,
            latency_ms=latency_ms,
            success=success,
        )
        with self._lock:
            entries = self._entries[endpoint]
            entries.append(entry)
            # Trim to max
            if len(entries) > self._max:
                self._entries[endpoint] = entries[-self._max:]

    def get_average(self, endpoint: str) -> float:
        """Get average latency for an endpoint. Returns 0.0 if no data."""
        with self._lock:
            entries = self._entries.get(endpoint, [])
            if not entries:
                return 0.0
            successful = [e for e in entries if e.success]
            if not successful:
                return 0.0
            return sum(e.latency_ms for e in successful) / len(successful)

    def get_all_averages(self) -> Dict[str, float]:
        """Get average latency for all tracked endpoints."""
        with self._lock:
            result = {}
            for endpoint, entries in self._entries.items():
                successful = [e for e in entries if e.success]
                if successful:
                    result[endpoint] = sum(e.latency_ms for e in successful) / len(successful)
                else:
                    result[endpoint] = 0.0
            return result

    def get_recent(self, n: int = 10) -> List[LatencyEntry]:
        """Get the most recent N entries across all endpoints."""
        with self._lock:
            all_entries = []
            for entries in self._entries.values():
                all_entries.extend(entries)
            all_entries.sort(key=lambda e: e.timestamp, reverse=True)
            return all_entries[:n]

    def get_slow_endpoints(self, threshold_ms: float = 500.0) -> List[Dict]:
        """Get endpoints with average latency above threshold."""
        averages = self.get_all_averages()
        slow = []
        for endpoint, avg in averages.items():
            if avg > threshold_ms:
                slow.append({"endpoint": endpoint, "avg_latency_ms": round(avg, 2)})
        slow.sort(key=lambda x: x["avg_latency_ms"], reverse=True)
        return slow

    def clear(self) -> None:
        """Clear all tracked entries."""
        with self._lock:
            self._entries.clear()
