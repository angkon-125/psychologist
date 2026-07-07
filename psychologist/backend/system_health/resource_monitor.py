"""
Resource Monitor — System Health

Collects CPU, RAM, and disk usage using stdlib with graceful fallbacks.
No external dependencies required.
"""

import os
import sys
import shutil
import logging
from datetime import datetime

from .schemas import ResourceSnapshot

logger = logging.getLogger("zara.health.resource_monitor")


class ResourceMonitor:
    """
    Monitors system resource usage.

    Uses stdlib where possible. Falls back to psutil if available.
    Never crashes — returns 0.0 for unavailable metrics.

    Usage:
        monitor = ResourceMonitor()
        snapshot = monitor.get_resources()
    """

    def get_resources(self) -> ResourceSnapshot:
        """Collect CPU, RAM, and disk metrics."""
        return ResourceSnapshot(
            cpu_percent=self._get_cpu(),
            ram_percent=self._get_ram_percent(),
            ram_used_mb=self._get_ram_used_mb(),
            disk_percent=self._get_disk_percent(),
            disk_free_gb=self._get_disk_free_gb(),
        )

    def _get_cpu(self) -> float:
        """Get CPU load. Uses os.getloadavg() on Unix, 0.0 on Windows."""
        try:
            if hasattr(os, "getloadavg"):
                load1, _, _ = os.getloadavg()
                # Normalize to percentage (assume 1 core minimum)
                cpu_count = os.cpu_count() or 1
                return min((load1 / cpu_count) * 100.0, 100.0)
            # Windows fallback: try psutil
            try:
                import psutil
                return psutil.cpu_percent(interval=0.1)
            except ImportError:
                return 0.0
        except Exception:
            return 0.0

    def _get_ram_percent(self) -> float:
        """Get RAM usage percentage."""
        try:
            # Linux: read /proc/meminfo
            if sys.platform.startswith("linux"):
                with open("/proc/meminfo", "r") as f:
                    lines = f.readlines()
                mem_total = 0
                mem_available = 0
                for line in lines:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])  # kB
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])  # kB
                if mem_total > 0:
                    return ((mem_total - mem_available) / mem_total) * 100.0
            # Windows/macOS: try psutil
            try:
                import psutil
                return psutil.virtual_memory().percent
            except ImportError:
                return 0.0
        except Exception:
            return 0.0

    def _get_ram_used_mb(self) -> float:
        """Get RAM used in MB."""
        try:
            if sys.platform.startswith("linux"):
                with open("/proc/meminfo", "r") as f:
                    lines = f.readlines()
                mem_total = 0
                mem_available = 0
                for line in lines:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])
                return (mem_total - mem_available) / 1024.0  # kB -> MB
            try:
                import psutil
                mem = psutil.virtual_memory()
                return mem.used / (1024 * 1024)
            except ImportError:
                return 0.0
        except Exception:
            return 0.0

    def _get_disk_percent(self) -> float:
        """Get disk usage percentage for the project directory."""
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            usage = shutil.disk_usage(project_root)
            if usage.total > 0:
                return (usage.used / usage.total) * 100.0
            return 0.0
        except Exception:
            return 0.0

    def _get_disk_free_gb(self) -> float:
        """Get free disk space in GB."""
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            usage = shutil.disk_usage(project_root)
            return usage.free / (1024 ** 3)
        except Exception:
            return 0.0
