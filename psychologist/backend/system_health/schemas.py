"""
System Health Schemas

Data structures for the system health intelligence layer:
- SubsystemStatus: health report for one subsystem
- OverallHealth: aggregated health of the entire system
- ResourceSnapshot: CPU/RAM/disk point-in-time
- LatencyEntry: single latency observation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


VALID_STATUSES = ("healthy", "degraded", "unavailable", "unknown")


@dataclass
class SubsystemStatus:
    """Health status of a single subsystem."""

    name: str = ""
    status: str = "unknown"
    latency_ms: float = 0.0
    message: str = ""
    fix: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "fix": self.fix,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubsystemStatus":
        return cls(
            name=data.get("name", ""),
            status=data.get("status", "unknown"),
            latency_ms=data.get("latency_ms", 0.0),
            message=data.get("message", ""),
            fix=data.get("fix"),
            details=data.get("details", {}),
        )


@dataclass
class OverallHealth:
    """Aggregated health of the entire ZARA system."""

    status: str = "unknown"
    subsystems: List[SubsystemStatus] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    uptime_seconds: float = 0.0
    degraded_features: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "subsystems": [s.to_dict() for s in self.subsystems],
            "timestamp": self.timestamp,
            "uptime_seconds": round(self.uptime_seconds, 1),
            "degraded_features": self.degraded_features,
            "recommendations": self.recommendations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OverallHealth":
        return cls(
            status=data.get("status", "unknown"),
            subsystems=[SubsystemStatus.from_dict(s) for s in data.get("subsystems", [])],
            timestamp=data.get("timestamp", ""),
            uptime_seconds=data.get("uptime_seconds", 0.0),
            degraded_features=data.get("degraded_features", []),
            recommendations=data.get("recommendations", []),
        )


@dataclass
class ResourceSnapshot:
    """Point-in-time system resource usage."""

    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: float = 0.0
    disk_percent: float = 0.0
    disk_free_gb: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": round(self.cpu_percent, 1),
            "ram_percent": round(self.ram_percent, 1),
            "ram_used_mb": round(self.ram_used_mb, 1),
            "disk_percent": round(self.disk_percent, 1),
            "disk_free_gb": round(self.disk_free_gb, 2),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceSnapshot":
        return cls(
            cpu_percent=data.get("cpu_percent", 0.0),
            ram_percent=data.get("ram_percent", 0.0),
            ram_used_mb=data.get("ram_used_mb", 0.0),
            disk_percent=data.get("disk_percent", 0.0),
            disk_free_gb=data.get("disk_free_gb", 0.0),
            timestamp=data.get("timestamp", ""),
        )


@dataclass
class LatencyEntry:
    """Single latency observation for an endpoint."""

    endpoint: str = ""
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LatencyEntry":
        return cls(
            endpoint=data.get("endpoint", ""),
            latency_ms=data.get("latency_ms", 0.0),
            timestamp=data.get("timestamp", ""),
            success=data.get("success", True),
        )
