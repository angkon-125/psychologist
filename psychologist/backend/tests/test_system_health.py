"""
Tests for System Health Intelligence (Phase 4)

Tests cover:
- Schemas (SubsystemStatus, OverallHealth, ResourceSnapshot, LatencyEntry)
- HealthMonitor (aggregation, caching, overall status)
- ModelChecker (Ollama checks, default model)
- ResourceMonitor (CPU/RAM/disk collection)
- LatencyTracker (record, average, rolling window)
- DependencyChecker (subsystem checks with mocked agents)
- DegradationManager (rules, fallback advice)
- System Health Routes (API endpoints)
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch

from backend.system_health.schemas import (
    SubsystemStatus,
    OverallHealth,
    ResourceSnapshot,
    LatencyEntry,
)
from backend.system_health.health_monitor import HealthMonitor
from backend.system_health.model_checker import ModelChecker
from backend.system_health.resource_monitor import ResourceMonitor
from backend.system_health.latency_tracker import LatencyTracker
from backend.system_health.dependency_checker import DependencyChecker
from backend.system_health.degradation import DegradationManager


# ─── Schemas ──────────────────────────────────────────────────────────────


class TestSubsystemStatus:
    def test_creation(self):
        status = SubsystemStatus(
            name="ollama",
            status="healthy",
            latency_ms=150.5,
            message="Ollama is running",
        )
        assert status.name == "ollama"
        assert status.status == "healthy"
        assert status.latency_ms == 150.5
        assert status.message == "Ollama is running"

    def test_to_dict(self):
        status = SubsystemStatus(
            name="stt",
            status="degraded",
            latency_ms=2500.0,
            message="STT is slow",
            fix="Install faster-whisper",
        )
        d = status.to_dict()
        assert d["name"] == "stt"
        assert d["status"] == "degraded"
        assert d["latency_ms"] == 2500.0
        assert d["message"] == "STT is slow"
        assert d["fix"] == "Install faster-whisper"

    def test_from_dict(self):
        data = {
            "name": "tts",
            "status": "unavailable",
            "latency_ms": 0.0,
            "message": "TTS not available",
            "fix": "Install pyttsx3",
            "details": {"engine": "piper"},
        }
        status = SubsystemStatus.from_dict(data)
        assert status.name == "tts"
        assert status.status == "unavailable"
        assert status.details["engine"] == "piper"

    def test_status_values(self):
        for status_val in ["healthy", "degraded", "unavailable", "unknown"]:
            s = SubsystemStatus(name="test", status=status_val)
            assert s.status == status_val


class TestOverallHealth:
    def test_creation(self):
        subsystems = [
            SubsystemStatus(name="ollama", status="healthy"),
            SubsystemStatus(name="stt", status="degraded"),
        ]
        health = OverallHealth(
            status="degraded",
            subsystems=subsystems,
            uptime_seconds=3600.0,
            degraded_features=["Voice input degraded"],
            recommendations=["Install faster-whisper"],
        )
        assert health.status == "degraded"
        assert len(health.subsystems) == 2
        assert health.uptime_seconds == 3600.0
        assert len(health.degraded_features) == 1
        assert len(health.recommendations) == 1

    def test_to_dict(self):
        health = OverallHealth(
            status="healthy",
            subsystems=[],
            uptime_seconds=100.0,
            degraded_features=[],
            recommendations=[],
        )
        d = health.to_dict()
        assert d["status"] == "healthy"
        assert d["uptime_seconds"] == 100.0
        assert "subsystems" in d
        assert "degraded_features" in d


class TestResourceSnapshot:
    def test_creation(self):
        snap = ResourceSnapshot(
            cpu_percent=45.5,
            ram_percent=60.2,
            ram_used_mb=4096.0,
            disk_percent=75.0,
            disk_free_gb=50.0,
        )
        assert snap.cpu_percent == 45.5
        assert snap.ram_percent == 60.2
        assert snap.ram_used_mb == 4096.0

    def test_serialization(self):
        snap = ResourceSnapshot(
            cpu_percent=10.0,
            ram_percent=20.0,
            ram_used_mb=1024.0,
            disk_percent=30.0,
            disk_free_gb=100.0,
        )
        d = snap.to_dict()
        assert d["cpu_percent"] == 10.0
        assert d["ram_percent"] == 20.0


class TestLatencyEntry:
    def test_creation(self):
        entry = LatencyEntry(
            endpoint="/api/chat",
            latency_ms=250.0,
            success=True,
        )
        assert entry.endpoint == "/api/chat"
        assert entry.latency_ms == 250.0
        assert entry.success is True

    def test_serialization(self):
        entry = LatencyEntry(
            endpoint="/api/voice",
            latency_ms=500.0,
            success=False,
        )
        d = entry.to_dict()
        assert d["endpoint"] == "/api/voice"
        assert d["latency_ms"] == 500.0
        assert d["success"] is False


# ─── HealthMonitor ─────────────────────────────────────────────────────────


class TestHealthMonitor:
    def test_initialization(self):
        monitor = HealthMonitor(specialists={}, db_path="test.db", ollama_url="http://localhost:11434")
        assert monitor.model_checker is not None
        assert monitor.resource_monitor is not None
        assert monitor.latency_tracker is not None
        assert monitor.dependency_checker is not None
        assert monitor.degradation_manager is not None

    def test_check_all_returns_overall_health(self):
        monitor = HealthMonitor(specialists={}, db_path="test.db")
        health = monitor.check_all(use_cache=False)
        assert isinstance(health, OverallHealth)
        assert health.status in ["healthy", "degraded", "unavailable", "unknown"]
        assert isinstance(health.subsystems, list)

    def test_caching(self):
        monitor = HealthMonitor(specialists={}, db_path="test.db")
        health1 = monitor.check_all(use_cache=True)
        time.sleep(0.1)
        health2 = monitor.check_all(use_cache=True)
        # Should return cached result (same object)
        assert health1 is health2

    def test_cache_expiry(self):
        monitor = HealthMonitor(specialists={}, db_path="test.db")
        health1 = monitor.check_all(use_cache=True)
        time.sleep(6)  # Wait for cache to expire (> 5s TTL)
        health2 = monitor.check_all(use_cache=True)
        # Should return new result (different object)
        assert health1 is not health2

    def test_overall_status_healthy(self):
        monitor = HealthMonitor(specialists={})
        subsystems = [
            SubsystemStatus(name="test1", status="healthy"),
            SubsystemStatus(name="test2", status="healthy"),
        ]
        status = monitor._determine_overall_status(subsystems)
        assert status == "healthy"

    def test_overall_status_degraded(self):
        monitor = HealthMonitor(specialists={})
        subsystems = [
            SubsystemStatus(name="test1", status="healthy"),
            SubsystemStatus(name="test2", status="degraded"),
        ]
        status = monitor._determine_overall_status(subsystems)
        assert status == "degraded"

    def test_overall_status_unavailable(self):
        monitor = HealthMonitor(specialists={})
        subsystems = [
            SubsystemStatus(name="test1", status="healthy"),
            SubsystemStatus(name="test2", status="unavailable"),
        ]
        status = monitor._determine_overall_status(subsystems)
        assert status == "unavailable"

    def test_check_subsystem(self):
        monitor = HealthMonitor(specialists={})
        status = monitor.check_subsystem("ollama")
        assert isinstance(status, SubsystemStatus)
        assert status.name == "ollama"

    def test_check_unknown_subsystem(self):
        monitor = HealthMonitor(specialists={})
        status = monitor.check_subsystem("nonexistent")
        assert status.status == "unknown"
        assert "Unknown subsystem" in status.message


# ─── ModelChecker ──────────────────────────────────────────────────────────


class TestModelChecker:
    def test_initialization(self):
        checker = ModelChecker(base_url="http://localhost:11434")
        assert checker._base_url == "http://localhost:11434"

    @patch("urllib.request.urlopen")
    def test_check_ollama_healthy(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2"}]}'
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        checker = ModelChecker(base_url="http://localhost:11434")
        with patch("time.perf_counter", side_effect=[0, 1.0]):  # 1 second latency
            status = checker.check_ollama()
        
        assert status.name == "ollama"
        assert status.status == "healthy"
        assert status.latency_ms > 0

    @patch("urllib.request.urlopen")
    def test_check_ollama_degraded(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2"}]}'
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        checker = ModelChecker(base_url="http://localhost:11434")
        with patch("time.perf_counter", side_effect=[0, 2.5]):  # 2.5 second latency
            status = checker.check_ollama()
        
        assert status.status == "degraded"
        # Message may contain "slow" or latency info
        assert status.latency_ms > 2000

    @patch("urllib.request.urlopen")
    def test_check_ollama_unavailable(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")
        
        checker = ModelChecker(base_url="http://localhost:11434")
        status = checker.check_ollama()
        
        assert status.status == "unavailable"
        # Message contains error info
        assert status.message is not None and len(status.message) > 0

    @patch("urllib.request.urlopen")
    def test_get_available_models(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2"}, {"name": "mistral"}]}'
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        checker = ModelChecker(base_url="http://localhost:11434")
        models = checker.get_available_models()
        
        assert "llama2" in models
        assert "mistral" in models

    @patch("urllib.request.urlopen")
    def test_check_default_model_healthy(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2"}]}'
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        with patch("backend.config.config.DEFAULT_MODEL", "llama2"):
            checker = ModelChecker(base_url="http://localhost:11434")
            status = checker.check_default_model()
        
        assert status.name == "default_model"
        assert status.status == "healthy"


# ─── ResourceMonitor ───────────────────────────────────────────────────────


class TestResourceMonitor:
    def test_initialization(self):
        monitor = ResourceMonitor()
        assert monitor is not None

    def test_get_resources(self):
        monitor = ResourceMonitor()
        snapshot = monitor.get_resources()
        assert isinstance(snapshot, ResourceSnapshot)
        assert snapshot.cpu_percent >= 0.0
        assert snapshot.ram_percent >= 0.0 or snapshot.ram_percent == 0.0  # May be 0 on failure
        assert snapshot.disk_percent >= 0.0

    def test_cpu_collection(self):
        monitor = ResourceMonitor()
        cpu = monitor._get_cpu()
        assert isinstance(cpu, float)
        assert cpu >= 0.0

    def test_disk_collection(self):
        monitor = ResourceMonitor()
        disk_percent = monitor._get_disk_percent()
        disk_free_gb = monitor._get_disk_free_gb()
        assert isinstance(disk_percent, float)
        assert isinstance(disk_free_gb, float)
        assert disk_percent >= 0.0
        assert disk_free_gb >= 0.0


# ─── LatencyTracker ────────────────────────────────────────────────────────


class TestLatencyTracker:
    def test_initialization(self):
        tracker = LatencyTracker()
        assert tracker is not None

    def test_record_and_average(self):
        tracker = LatencyTracker()
        tracker.record("/api/chat", 100.0, success=True)
        tracker.record("/api/chat", 200.0, success=True)
        avg = tracker.get_average("/api/chat")
        assert avg == 150.0

    def test_rolling_window(self):
        tracker = LatencyTracker(max_per_endpoint=3)
        tracker.record("/api/test", 100.0, success=True)
        tracker.record("/api/test", 200.0, success=True)
        tracker.record("/api/test", 300.0, success=True)
        tracker.record("/api/test", 400.0, success=True)  # Should push out 100.0
        avg = tracker.get_average("/api/test")
        assert avg == 300.0  # (200+300+400)/3

    def test_get_all_averages(self):
        tracker = LatencyTracker()
        tracker.record("/api/chat", 100.0, success=True)
        tracker.record("/api/voice", 200.0, success=True)
        averages = tracker.get_all_averages()
        assert "/api/chat" in averages
        assert "/api/voice" in averages
        assert averages["/api/chat"] == 100.0
        assert averages["/api/voice"] == 200.0

    def test_get_recent(self):
        tracker = LatencyTracker()
        tracker.record("/api/test", 100.0, success=True)
        tracker.record("/api/test", 200.0, success=True)
        recent = tracker.get_recent(5)
        assert len(recent) == 2
        assert all(isinstance(e, LatencyEntry) for e in recent)

    def test_get_slow_endpoints(self):
        tracker = LatencyTracker()
        tracker.record("/api/fast", 50.0, success=True)
        tracker.record("/api/slow", 500.0, success=True)
        slow = tracker.get_slow_endpoints(threshold_ms=200.0)
        # Returns list of dicts with 'endpoint' key
        slow_endpoints = [s["endpoint"] for s in slow]
        assert "/api/slow" in slow_endpoints
        assert "/api/fast" not in slow_endpoints

    def test_clear(self):
        tracker = LatencyTracker()
        tracker.record("/api/test", 100.0, success=True)
        tracker.clear()
        avg = tracker.get_average("/api/test")
        assert avg == 0.0


# ─── DependencyChecker ─────────────────────────────────────────────────────


class TestDependencyChecker:
    def test_initialization(self):
        checker = DependencyChecker(specialists={}, db_path="test.db")
        assert checker is not None

    def test_check_stt_no_voice_agent(self):
        checker = DependencyChecker(specialists={}, db_path="test.db")
        status = checker.check_stt()
        assert status.name == "stt"
        # Returns "unknown" when voice agent not present
        assert status.status in ["unavailable", "unknown"]

    def test_check_stt_healthy(self):
        mock_voice = Mock()
        mock_stt = Mock()
        mock_stt.is_available = True
        mock_voice._stt_engine = mock_stt
        checker = DependencyChecker(specialists={"voice": mock_voice}, db_path="test.db")
        status = checker.check_stt()
        assert status.status == "healthy"

    def test_check_tts_no_voice_agent(self):
        checker = DependencyChecker(specialists={}, db_path="test.db")
        status = checker.check_tts()
        assert status.name == "tts"
        # Returns "unknown" when voice agent not present
        assert status.status in ["unavailable", "unknown"]

    def test_check_sqlite_memory_no_memory_agent(self):
        checker = DependencyChecker(specialists={}, db_path="test.db")
        status = checker.check_sqlite_memory()
        assert status.name == "sqlite_memory"
        assert status.status == "unavailable"

    def test_check_all(self):
        checker = DependencyChecker(specialists={}, db_path="test.db")
        statuses = checker.check_all()
        assert isinstance(statuses, list)
        assert len(statuses) > 0
        assert all(isinstance(s, SubsystemStatus) for s in statuses)


# ─── DegradationManager ────────────────────────────────────────────────────


class TestDegradationManager:
    def test_initialization(self):
        manager = DegradationManager()
        assert manager is not None

    def test_evaluate_no_degradation(self):
        manager = DegradationManager()
        subsystems = [
            SubsystemStatus(name="ollama", status="healthy"),
            SubsystemStatus(name="stt", status="healthy"),
        ]
        degraded = manager.evaluate(subsystems)
        assert len(degraded) == 0

    def test_evaluate_with_degradation(self):
        manager = DegradationManager()
        subsystems = [
            SubsystemStatus(name="ollama", status="unavailable"),
            SubsystemStatus(name="stt", status="healthy"),
        ]
        degraded = manager.evaluate(subsystems)
        assert len(degraded) > 0
        # Check that fallback description is present
        assert "EmotionEngine" in degraded[0] or "LLM" in degraded[0]

    def test_get_fallback_advice(self):
        manager = DegradationManager()
        subsystems = [SubsystemStatus(name="stt", status="unavailable")]
        manager.evaluate(subsystems)
        advice = manager.get_fallback_advice("stt")
        assert isinstance(advice, str)
        assert len(advice) > 0

    def test_is_degraded(self):
        manager = DegradationManager()
        subsystems = [SubsystemStatus(name="tts", status="unavailable")]
        manager.evaluate(subsystems)
        assert manager.is_degraded("tts") is True
        assert manager.is_degraded("stt") is False

    def test_get_fix_suggestion(self):
        manager = DegradationManager()
        fix = manager.get_fix_suggestion("ollama")
        assert isinstance(fix, str)
        assert "ollama" in fix.lower()

    def test_get_recommendations(self):
        manager = DegradationManager()
        subsystems = [
            SubsystemStatus(name="ollama", status="unavailable"),
            SubsystemStatus(name="stt", status="degraded"),
        ]
        manager.evaluate(subsystems)
        recs = manager.get_recommendations()
        assert isinstance(recs, list)
        assert len(recs) > 0


# ─── System Health Routes ──────────────────────────────────────────────────


class TestSystemHealthRoutes:
    @pytest.fixture
    def client(self):
        from backend.main import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_full_health_endpoint(self, client):
        response = client.get("/api/system/health/full")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "status" in data
        assert "subsystems" in data

    def test_model_health_endpoint(self, client):
        response = client.get("/api/system/health/models")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "ollama" in data
        assert "default_model" in data

    def test_resource_health_endpoint(self, client):
        response = client.get("/api/system/health/resources")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "cpu_percent" in data
        assert "ram_percent" in data
        assert "disk_percent" in data

    def test_degraded_health_endpoint(self, client):
        response = client.get("/api/system/health/degraded")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "overall_status" in data
        assert "degraded_features" in data

    def test_latency_endpoint(self, client):
        response = client.get("/api/system/latency")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "averages" in data
        assert "slow_endpoints" in data
        assert "recent" in data
