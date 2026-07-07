"""
Dependency Checker — System Health

Checks health of all ZARA subsystem dependencies:
STT, TTS, SQLite memory, episodic memory, graph memory,
vector store, tools registry, safety config, backend API.
"""

import time
import logging
from typing import Dict, List, Optional

from .schemas import SubsystemStatus

logger = logging.getLogger("zara.health.dependency_checker")


class DependencyChecker:
    """
    Checks health of ZARA subsystem dependencies.

    Usage:
        checker = DependencyChecker(specialists)
        statuses = checker.check_all()
    """

    def __init__(self, specialists: Optional[Dict] = None, db_path: str = ""):
        self._specialists = specialists or {}
        self._db_path = db_path

    def set_specialists(self, specialists: Dict) -> None:
        """Update specialists reference."""
        self._specialists = specialists

    def set_db_path(self, db_path: str) -> None:
        """Update database path."""
        self._db_path = db_path

    def check_stt(self) -> SubsystemStatus:
        """Check STT engine status."""
        try:
            voice = self._specialists.get("voice")
            if not voice:
                return SubsystemStatus(
                    name="stt", status="unknown",
                    message="Voice agent not registered",
                )
            # Check if voice agent has STT info
            info = voice.get_info() if hasattr(voice, "get_info") else {}
            stt_available = info.get("stt_available", False)
            # Try checking the STT engine directly
            if hasattr(voice, "_stt_engine") and voice._stt_engine:
                stt_available = voice._stt_engine.is_available
                engine_name = "faster-whisper" if stt_available else "none"
                return SubsystemStatus(
                    name="stt",
                    status="healthy" if stt_available else "degraded",
                    message="STT engine ready" if stt_available else "STT engine unavailable",
                    fix=None if stt_available else "Install faster-whisper for speech recognition",
                    details={"engine": engine_name},
                )
            return SubsystemStatus(
                name="stt",
                status="healthy" if stt_available else "degraded",
                message="STT status from voice agent info",
                details=info,
            )
        except Exception as e:
            return SubsystemStatus(
                name="stt", status="unknown",
                message=f"STT check failed: {e}",
            )

    def check_tts(self) -> SubsystemStatus:
        """Check TTS engine status."""
        try:
            voice = self._specialists.get("voice")
            if not voice:
                return SubsystemStatus(
                    name="tts", status="unknown",
                    message="Voice agent not registered",
                )
            if hasattr(voice, "_tts_engine") and voice._tts_engine:
                tts_available = voice._tts_engine.is_available
                info = voice._tts_engine.get_info() if hasattr(voice._tts_engine, "get_info") else {}
                return SubsystemStatus(
                    name="tts",
                    status="healthy" if tts_available else "degraded",
                    message="TTS engine ready" if tts_available else "TTS engine unavailable",
                    fix=None if tts_available else "Install pyttsx3 or Piper for voice output",
                    details=info,
                )
            return SubsystemStatus(
                name="tts", status="degraded",
                message="TTS engine not initialized",
                fix="Initialize voice agent",
            )
        except Exception as e:
            return SubsystemStatus(
                name="tts", status="unknown",
                message=f"TTS check failed: {e}",
            )

    def check_sqlite_memory(self) -> SubsystemStatus:
        """Check SQLite memory database connectivity."""
        start = time.perf_counter()
        try:
            memory = self._specialists.get("memory")
            if not memory or not hasattr(memory, "db") or not memory.db:
                return SubsystemStatus(
                    name="sqlite_memory", status="unavailable",
                    message="Memory agent or database not initialized",
                    fix="Initialize memory agent",
                )
            # Try a simple query
            import sqlite3
            db_path = self._db_path
            if not db_path and hasattr(memory.db, "_db_path"):
                db_path = memory.db._db_path
            if db_path:
                conn = sqlite3.connect(db_path, timeout=2)
                conn.execute("SELECT 1").fetchone()
                conn.close()
            elapsed = (time.perf_counter() - start) * 1000
            return SubsystemStatus(
                name="sqlite_memory", status="healthy",
                latency_ms=elapsed,
                message="SQLite memory responding",
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return SubsystemStatus(
                name="sqlite_memory", status="degraded",
                latency_ms=elapsed,
                message=f"SQLite check issue: {e}",
                fix="Check database file permissions",
            )

    def check_episodic_memory(self) -> SubsystemStatus:
        """Check episodic memory subsystem."""
        try:
            memory = self._specialists.get("memory")
            if not memory:
                return SubsystemStatus(
                    name="episodic_memory", status="unknown",
                    message="Memory agent not registered",
                )
            if hasattr(memory, "episode_store") and memory.episode_store:
                return SubsystemStatus(
                    name="episodic_memory", status="healthy",
                    message="Episodic memory active",
                )
            return SubsystemStatus(
                name="episodic_memory", status="degraded",
                message="Episodic memory not initialized",
                fix="Memory agent needs re-initialization",
            )
        except Exception as e:
            return SubsystemStatus(
                name="episodic_memory", status="unknown",
                message=f"Episodic check failed: {e}",
            )

    def check_graph_memory(self) -> SubsystemStatus:
        """Check graph memory subsystem."""
        try:
            memory = self._specialists.get("memory")
            if not memory:
                return SubsystemStatus(
                    name="graph_memory", status="unknown",
                    message="Memory agent not registered",
                )
            if hasattr(memory, "graph_memory") and memory.graph_memory:
                return SubsystemStatus(
                    name="graph_memory", status="healthy",
                    message="Graph memory active",
                )
            return SubsystemStatus(
                name="graph_memory", status="degraded",
                message="Graph memory not initialized",
            )
        except Exception as e:
            return SubsystemStatus(
                name="graph_memory", status="unknown",
                message=f"Graph check failed: {e}",
            )

    def check_vector_store(self) -> SubsystemStatus:
        """Check vector store status."""
        try:
            memory = self._specialists.get("memory")
            if not memory:
                return SubsystemStatus(
                    name="vector_store", status="unknown",
                    message="Memory agent not registered",
                )
            if hasattr(memory, "vector_store") and memory.vector_store:
                vs_type = type(memory.vector_store).__name__
                is_stub = "Stub" in vs_type
                return SubsystemStatus(
                    name="vector_store",
                    status="degraded" if is_stub else "healthy",
                    message=f"Vector store: {vs_type}" + (" (keyword fallback)" if is_stub else ""),
                    details={"type": vs_type, "is_stub": is_stub},
                )
            return SubsystemStatus(
                name="vector_store", status="degraded",
                message="Vector store not initialized",
            )
        except Exception as e:
            return SubsystemStatus(
                name="vector_store", status="unknown",
                message=f"Vector store check failed: {e}",
            )

    def check_tools_registry(self) -> SubsystemStatus:
        """Check tools registry."""
        try:
            tool = self._specialists.get("tool")
            if not tool:
                return SubsystemStatus(
                    name="tools", status="degraded",
                    message="Tool agent not registered",
                )
            info = tool.get_info() if hasattr(tool, "get_info") else {}
            initialized = info.get("initialized", False)
            return SubsystemStatus(
                name="tools",
                status="healthy" if initialized else "degraded",
                message="Tools registry active" if initialized else "Tools not initialized",
                details=info,
            )
        except Exception as e:
            return SubsystemStatus(
                name="tools", status="unknown",
                message=f"Tools check failed: {e}",
            )

    def check_safety_config(self) -> SubsystemStatus:
        """Check safety agent configuration."""
        try:
            safety = self._specialists.get("safety")
            if not safety:
                return SubsystemStatus(
                    name="safety", status="degraded",
                    message="Safety agent not registered",
                    fix="Register safety agent with orchestrator",
                )
            info = safety.health_check() if hasattr(safety, "health_check") else {}
            initialized = info.get("initialized", False)
            return SubsystemStatus(
                name="safety",
                status="healthy" if initialized else "degraded",
                message="Safety agent active" if initialized else "Safety agent not initialized",
                details=info,
            )
        except Exception as e:
            return SubsystemStatus(
                name="safety", status="unknown",
                message=f"Safety check failed: {e}",
            )

    def check_backend_api(self) -> SubsystemStatus:
        """Check if the backend API is self-consistent (always healthy if running)."""
        return SubsystemStatus(
            name="backend_api",
            status="healthy",
            message="Backend API is running",
        )

    def check_all(self) -> List[SubsystemStatus]:
        """Run all dependency checks and return list of statuses."""
        checks = [
            self.check_stt,
            self.check_tts,
            self.check_sqlite_memory,
            self.check_episodic_memory,
            self.check_graph_memory,
            self.check_vector_store,
            self.check_tools_registry,
            self.check_safety_config,
            self.check_backend_api,
        ]
        results = []
        for check_fn in checks:
            try:
                results.append(check_fn())
            except Exception as e:
                logger.debug("Check %s failed: %s", check_fn.__name__, e)
                results.append(SubsystemStatus(
                    name=check_fn.__name__.replace("check_", ""),
                    status="unknown",
                    message=f"Check failed: {e}",
                ))
        return results
