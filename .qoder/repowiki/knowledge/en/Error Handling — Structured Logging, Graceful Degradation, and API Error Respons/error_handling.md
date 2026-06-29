## Overview

The ZARA codebase employs an **informal but consistent** error handling strategy built on Python's standard `logging` module, broad `except Exception` blocks, and Flask-level HTTP error handlers. There are **no custom exception types**, no centralized error codes, and no panic/recover mechanism (Python does not use panics). Instead, errors are caught at component boundaries, logged via a structured logger, and translated into JSON error responses for the API layer.

---

## System / Approach

### 1. Centralized Logging (`psychologist/logger.py`)
- A single `setup_logging()` function configures the root `zara` logger with a fixed format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- Child loggers are obtained via `get_logger(name)`, producing names like `zara.app`, `zara.safety`, `zara.tts`, `zara.session`.
- No external logging framework is used — only Python's built-in `logging` module.
- Log propagation is disabled to prevent duplicate messages.

### 2. Broad Exception Catching
- Nearly all error handling uses bare `except Exception as e:` blocks.
- Specific exception types are rarely caught; the one notable exception is `except TypeError` in `app.py` for personality trait validation.
- Errors are logged with `logger.error("...: %s", e)` or `logger.warning("...: %s", e)` and then converted into JSON error responses.

### 3. Flask HTTP Error Handlers
- `app.py` registers handlers for HTTP status codes 400, 404, 405, 429, and 500.
- Each handler returns a JSON object with `error` (a short string key) and `message` (the exception message or a generic description).
- The 500 handler logs the error before returning a generic "An unexpected error occurred" message to avoid leaking internals.

### 4. Graceful Degradation for Optional Subsystems
- Voice output (TTS), voice input (STT), and voice emotion detection are wrapped in `try/except` blocks during startup.
- If initialization fails, the subsystem flag (`voice_output_available`, `voice_input_available`, `voice_emotion_available`) is set to `False`, a warning is logged, and the application continues without that feature.
- Routes for unavailable subsystems return HTTP 501 (Not Implemented) with a clear error message.

### 5. Input Validation Before Processing
- The `rate_limiter.py` module provides `validate_text_input()`, which returns a `(is_valid, error_message, text_value)` tuple.
- Endpoints check this tuple and return HTTP 400 with `{"error": "invalid_input", "message": ...}` if validation fails.
- This pattern avoids exceptions from bad input by validating early.

### 6. Engine Fallback Chains
- The TTS manager (`tts_manager.py`) implements a priority-based fallback chain: Piper → eSpeak → pyttsx3.
- Each engine is tried in order; failures are logged as warnings, and the next engine is attempted.
- If all engines fail, a `TTSResult` with an error message is returned rather than raising an exception.

### 7. Safe Defaults for Edge Cases
- The `SafetySupportLayer.assess_input()` method handles `None`, empty strings, whitespace-only, and non-string inputs by returning a `RiskLevel.NONE` assessment instead of raising.
- Session file loading catches `json.JSONDecodeError` and `OSError`, skipping corrupted files silently.
- Config file loading catches `yaml.YAMLError`, `OSError`, and `ValueError`, falling back to an empty config dict.

---

## Key Files

| File | Role |
|------|------|
| `psychologist/logger.py` | Centralized logging setup; defines `setup_logging()` and `get_logger()` |
| `psychologist/app.py` | Flask error handlers (400/404/405/429/500); try/except blocks around all route logic; graceful subsystem initialization |
| `psychologist/rate_limiter.py` | Input validation helper `validate_text_input()`; rate limiting with 429 responses |
| `psychologist/emotion_engine/interaction/safety_support_layer.py` | Config loading with error handling; graceful handling of None/empty/non-string input |
| `psychologist/emotion_engine/interaction/session_manager.py` | Session persistence with `OSError` handling; JSON decode error handling when reading history |
| `psychologist/emotion_engine/voice_output/tts_manager.py` | Engine fallback chain; per-engine exception catching; safety filtering |
| `psychologist/tests/test_safety_edge_cases.py` | Tests for edge-case error handling (None input, empty strings, non-string types) |

---

## Architecture and Conventions

### Logging Convention
- Every module that needs logging imports `get_logger` from `logger.py` and creates a namespaced logger: `logger = get_logger("subsystem")`.
- Log levels used:
  - `logger.info()` — normal operational events (initialization, state changes)
  - `logger.warning()` — recoverable issues (engine unavailable, config load failure)
  - `logger.error()` — operation failures that cause a request to fail
  - `logger.debug()` — detailed diagnostics (skipped engines)

### Error Response Pattern
All API error responses follow a consistent JSON structure:
```json
{
  "error": "short_error_key",
  "message": "human-readable description"
}
```
Common error keys: `bad_request`, `not_found`, `method_not_allowed`, `rate_limited`, `internal_error`, `invalid_input`, `processing_error`, `tts_error`, `voice_error`.

### No Custom Exceptions
The codebase does **not** define any custom exception classes. All errors are handled via:
1. Bare `except Exception` blocks
2. Specific built-in exceptions (`TypeError`, `ValueError`, `OSError`, `json.JSONDecodeError`, `yaml.YAMLError`)
3. Returning error-indicating data structures (e.g., `TTSResult` with `success=False`)

### Graceful Degradation Over Hard Failures
The system prioritizes availability over strict correctness:
- Missing optional dependencies (Piper, eSpeak, pygame, pyaudio) do not crash the app.
- Corrupted session files are skipped rather than causing startup failure.
- Invalid config files fall back to defaults.

---

## Rules Developers Should Follow

1. **Always use `get_logger()` for logging** — never use `print()` or `logging.getLogger()` directly. Use the `zara.<subsystem>` namespace.

2. **Catch `Exception` broadly at API boundaries** — route handlers should wrap their core logic in `try/except Exception` blocks, log the error, and return a JSON error response with HTTP 500.

3. **Validate input before processing** — use `validate_text_input()` from `rate_limiter.py` for text fields. Return HTTP 400 for invalid input rather than letting exceptions propagate.

4. **Log errors with context** — include a descriptive prefix in log messages (e.g., `"Emotion processing failed: %s"`) so logs are searchable and actionable.

5. **Use graceful degradation for optional features** — wrap optional subsystem initialization in `try/except`, set an availability flag, and provide fallback routes that return HTTP 501.

6. **Handle file I/O errors explicitly** — catch `OSError` and `json.JSONDecodeError` when reading/writing session files or configs. Log the error and continue with safe defaults.

7. **Return error-indicating results instead of raising** — for internal components (like TTS engines), prefer returning a result object with `success=False` and an `error_message` field rather than raising exceptions. This keeps the fallback chain clean.

8. **Test edge cases** — ensure functions handle `None`, empty strings, and wrong types gracefully, as demonstrated in `test_safety_edge_cases.py`.