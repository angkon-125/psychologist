## Overview

ZARA uses Python's built-in `logging` module with a centralized configuration pattern. There are no external logging frameworks or dependencies — the system relies entirely on the standard library.

## Architecture

### Central Logger Factory (`psychologist/logger.py`)

The entire logging system is anchored in a single module that provides two functions:

- **`setup_logging(level=logging.INFO)`** — Configures the root `zara` logger at application startup. Creates a single `StreamHandler` writing to `sys.stdout` with a structured format. Prevents duplicate handlers and disables propagation to avoid double-output.
- **`get_logger(name: str)`** — Returns child loggers under the `zara.<name>` namespace (e.g., `zara.app`, `zara.safety`, `zara.session`).

### Log Format

```
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

With date format: `%Y-%m-%d %H:%M:%S`

Example output:
```
2026-06-24 17:25:15 [INFO] zara.app: Voice output system initialized — single local voice locked
2026-06-24 17:28:01 [ERROR] zara.session: Failed to save session: Permission denied
```

### Namespace Hierarchy

All loggers follow the `zara.<subsystem>` convention:

| Logger Name | Module | Purpose |
|---|---|---|
| `zara.run_app` | `run_app.py` | Application launcher, startup/shutdown events |
| `zara.app` | `app.py` | Flask route handlers, initialization failures |
| `zara.safety` | `safety_support_layer.py` | Safety config loading warnings |
| `zara.session` | `session_manager.py` | Session persistence errors |
| `zara.dashboard` | `dashboard.py` | Visualization plotting errors |

## Key Files

- **`psychologist/logger.py`** — Core logging configuration (72 lines). The single source of truth for all logging setup.
- **`psychologist/run_app.py`** — Calls `setup_logging()` before importing `app`, ensuring all modules inherit the configured logger.
- **`psychologist/app.py`** — Primary consumer using `get_logger("app")`. Logs initialization status, error handling in API endpoints.

## Conventions and Rules

### 1. Always use `get_logger()` from `logger.py`

Modules should never call `logging.getLogger()` directly with arbitrary names. Instead:

```python
from logger import get_logger
logger = get_logger("my_module")  # Produces 'zara.my_module'
```

A few existing modules (`safety_support_layer.py`, `session_manager.py`, `dashboard.py`) bypass this helper and call `logging.getLogger("zara.xxx")` directly. This works but is inconsistent with the intended pattern.

### 2. Call `setup_logging()` once at startup

`run_app.py` invokes `setup_logging()` before any other imports. The function guards against duplicate handler attachment via `if not root_logger.handlers`.

### 3. Use parameterized log messages

All observed logging calls use printf-style formatting:

```python
logger.error("TTS speak failed: %s", e)  # Correct
logger.error(f"TTS speak failed: {e}")   # Avoid — evaluated even if level is disabled
```

### 4. Log levels in use

- **`INFO`** — Normal operational events (initialization success, mode switches)
- **`WARNING`** — Non-fatal issues (config load failures, unavailable subsystems)
- **`ERROR`** — Request processing failures, persistence errors

No `DEBUG` or `CRITICAL` usage was found in the codebase, though `setup_logging()` accepts any standard level.

### 5. No file-based logging

Despite the presence of an empty `logs/` directory and an `app_log.txt` file (which contains raw Flask/Werkzeug access logs, not structured application logs), the application does **not** write structured logs to files. All output goes to `stdout` only. The `app_log.txt` appears to be a manual capture of console output, not a programmatically managed log file.

### 6. No structured/JSON logging

Log output is plain text. There is no JSON formatter, no additional context fields (e.g., request IDs, user IDs, session IDs), and no correlation identifiers embedded in log messages.

## Gaps and Observations

- The `logs/` directory exists but is unused by the application code.
- Some modules still use direct `logging.getLogger()` calls instead of the `get_logger()` helper, creating minor inconsistency.
- No log rotation, file sinks, or persistent log storage is implemented.
- Flask's built-in access logs (visible in `app_log.txt`) are separate from the application's structured logging and go through Werkzeug's own logger, not the `zara` namespace.