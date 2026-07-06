"""
ZARA Centralized Configuration

All configuration values are read from environment variables with safe defaults.
No secrets are hardcoded. Every setting can be overridden at runtime.

Usage:
    from backend.config import config
    if config.USE_OLLAMA:
        ...
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional


def _env_bool(key: str, default: bool = False) -> bool:
    """Read a boolean from an environment variable."""
    return os.environ.get(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    """Read an integer from an environment variable."""
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_str(key: str, default: str = "") -> str:
    """Read a string from an environment variable."""
    return os.environ.get(key, default)


@dataclass
class ZARAConfig:
    """Centralized configuration for the ZARA multi-agent system."""

    # ── LLM / Ollama ─────────────────────────────────────────────
    USE_OLLAMA: bool = field(default_factory=lambda: _env_bool("USE_OLLAMA", False))
    OLLAMA_BASE_URL: str = field(
        default_factory=lambda: _env_str("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    DEFAULT_MODEL: str = field(
        default_factory=lambda: _env_str("OLLAMA_MODEL", "llama3.2")
    )
    OLLAMA_TIMEOUT_SECONDS: float = field(
        default_factory=lambda: float(_env_str("OLLAMA_TIMEOUT", "5.0"))
    )

    # ── Feature Toggles ──────────────────────────────────────────
    ENABLE_VOICE: bool = field(default_factory=lambda: _env_bool("ENABLE_VOICE", True))
    ENABLE_MEMORY: bool = field(default_factory=lambda: _env_bool("ENABLE_MEMORY", True))
    ENABLE_TOOLS: bool = field(default_factory=lambda: _env_bool("ENABLE_TOOLS", True))
    ENABLE_PREDICTION: bool = field(
        default_factory=lambda: _env_bool("ENABLE_PREDICTION", True)
    )
    ENABLE_EVALUATION: bool = field(
        default_factory=lambda: _env_bool("ENABLE_EVALUATION", True)
    )

    # ── Voice Thresholds (milliseconds) ──────────────────────────
    SILENCE_FINAL_MS: int = field(
        default_factory=lambda: _env_int("SILENCE_FINAL_MS", 6000)
    )
    SILENCE_THINKING_MS: int = field(
        default_factory=lambda: _env_int("SILENCE_THINKING_MS", 3500)
    )

    # ── Tool Execution ───────────────────────────────────────────
    MAX_TOOL_TIMEOUT: int = field(
        default_factory=lambda: _env_int("MAX_TOOL_TIMEOUT", 30)
    )

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = field(
        default_factory=lambda: _env_str("LOG_LEVEL", "INFO")
    )

    # ── Server ───────────────────────────────────────────────────
    HOST: str = field(default_factory=lambda: _env_str("FLASK_HOST", "127.0.0.1"))
    PORT: int = field(default_factory=lambda: _env_int("FLASK_PORT", 5000))
    DEBUG: bool = field(default_factory=lambda: _env_bool("FLASK_DEBUG", False))

    # ── Memory ───────────────────────────────────────────────────
    MEMORY_DB_PATH: str = field(
        default_factory=lambda: _env_str("MEMORY_DB_PATH", "data/zara_memory.db")
    )
    MAX_SHORT_TERM_MEMORY: int = field(
        default_factory=lambda: _env_int("MAX_SHORT_TERM_MEMORY", 50)
    )
    MAX_LONG_TERM_MEMORY: int = field(
        default_factory=lambda: _env_int("MAX_LONG_TERM_MEMORY", 5000)
    )

    # ── Privacy ──────────────────────────────────────────────────
    LOG_EMOTIONAL_CONTENT: bool = field(
        default_factory=lambda: _env_bool("LOG_EMOTIONAL_CONTENT", False)
    )

    # ── Voice Engine ──────────────────────────────────────────────
    ZARA_PIPER_MODEL_PATH: str = field(
        default_factory=lambda: _env_str("ZARA_PIPER_MODEL_PATH", "")
    )
    ZARA_PIPER_CONFIG_PATH: str = field(
        default_factory=lambda: _env_str("ZARA_PIPER_CONFIG_PATH", "")
    )
    ZARA_DEFAULT_VOICE_PROFILE: str = field(
        default_factory=lambda: _env_str("ZARA_DEFAULT_VOICE_PROFILE", "zara_soft")
    )

    def get_log_level(self) -> int:
        """Convert LOG_LEVEL string to logging constant."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(self.LOG_LEVEL.upper(), logging.INFO)

    def to_dict(self) -> dict:
        """Return a safe dict representation (no secrets)."""
        return {
            "use_ollama": self.USE_OLLAMA,
            "ollama_base_url": self.OLLAMA_BASE_URL,
            "default_model": self.DEFAULT_MODEL,
            "enable_voice": self.ENABLE_VOICE,
            "enable_memory": self.ENABLE_MEMORY,
            "enable_tools": self.ENABLE_TOOLS,
            "enable_prediction": self.ENABLE_PREDICTION,
            "enable_evaluation": self.ENABLE_EVALUATION,
            "silence_final_ms": self.SILENCE_FINAL_MS,
            "silence_thinking_ms": self.SILENCE_THINKING_MS,
            "max_tool_timeout": self.MAX_TOOL_TIMEOUT,
            "log_level": self.LOG_LEVEL,
            "host": self.HOST,
            "port": self.PORT,
            "memory_db_path": self.MEMORY_DB_PATH,
        }


# Singleton config instance
config = ZARAConfig()
