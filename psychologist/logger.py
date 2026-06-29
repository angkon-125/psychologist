"""
Centralized logging configuration for ZARA.

Provides a single setup point for structured logging across all subsystems.
No external dependencies — uses Python's built-in logging module.
"""

import logging
import sys


_LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root 'zara' logger and return it.

    Call this once at application startup (e.g. in run_app.py)
    before importing modules that use logging.

    Parameters
    ----------
    level : int
        Logging level (default INFO). Use logging.DEBUG for verbose output.

    Returns
    -------
    logging.Logger
        The configured 'zara' logger instance.
    """
    root_logger = logging.getLogger("zara")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
        )
        root_logger.addHandler(handler)

    # Prevent log propagation to avoid duplicate messages
    root_logger.propagate = False

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the 'zara' namespace.

    Usage:
        logger = get_logger("app")
        logger.info("Server started")
        logger.error("Something failed: %s", error)

    Parameters
    ----------
    name : str
        Subsystem name (e.g. 'app', 'safety', 'tts', 'session').

    Returns
    -------
    logging.Logger
        Logger instance configured under 'zara.<name>'.
    """
    return logging.getLogger(f"zara.{name}")
