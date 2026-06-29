The ZARA Offline Emotional Support Companion employs a **hybrid configuration system** that combines static YAML files for complex, structured data (safety rules, TTS styles, interaction modes) with a centralized Python module (`system_constants.py`) for runtime tuning parameters and magic numbers. The system is designed to be fully offline, with no reliance on environment variables for core logic or remote feature flags.

### 1. Configuration Sources & Layers

*   **YAML Configuration Files**: Located in `psychologist/config/`, these files manage complex, hierarchical settings:
    *   `safety_config.yaml`: Defines crisis detection keywords (English/Bangla), diagnosis blocking patterns, and safe response templates.
    *   `interaction_config.yaml`: Controls interaction modes (text/voice/hybrid), session limits, and privacy settings.
    *   `tts_config.yaml` / `single_voice_tts.yaml`: Configures Text-to-Speech engines, voice locking, and emotion-based style modifiers (speed, pitch, volume).
    *   `voice_config.yaml`: General voice input/output settings.
*   **System Constants Module**: `psychologist/system_constants.py` serves as a single source of truth for numeric thresholds and limits used throughout the codebase (e.g., `EMOTION_DECAY_FACTOR`, `SESSION_HISTORY_LIMIT`, `RATE_LIMIT_REQUESTS`). This avoids "magic numbers" scattered across modules.
*   **Environment Variables**: Used sparingly for infrastructure-level settings in `app.py`, specifically `FLASK_HOST`, `FLASK_PORT`, and `FLASK_DEBUG`. These do not influence the emotional engine's logic.

### 2. Configuration Loading Architecture

*   **Lazy/Explicit Loading**: Configuration is not loaded globally at startup. Instead, specific components load their relevant YAML files upon initialization.
    *   `SafetySupportLayer` loads `safety_config.yaml`.
    *   `SingleVoiceConfig` loads `single_voice_tts.yaml`.
*   **Default Fallbacks**: Config loaders (e.g., `SingleVoiceConfig`) implement a `_get_defaults()` method. If a YAML file is missing or malformed, the system falls back to hardcoded defaults and optionally writes the default config to disk. This ensures robustness in offline environments where file I/O might fail or files might be deleted.
*   **Dotted Key Access**: The `SingleVoiceConfig` class provides a `get('dotted.key.path')` method, allowing flexible access to nested YAML structures without exposing the raw dictionary.

### 3. Key Conventions & Rules

*   **Offline-First Safety**: Safety configurations (crisis keywords, blocking patterns) are strictly local. The system explicitly disables cloud TTS and voice cloning in `tts_config.yaml` via `safety.allow_cloud_tts: false`.
*   **Immutable Core Logic**: Core emotional reasoning weights (e.g., `REASONING_BLEND_CURRENT`) are defined in `system_constants.py` and imported directly. They are not exposed to end-user configuration files to prevent destabilizing the emotion engine.
*   **Language-Aware Safety**: Safety configs support multi-language keywords (English and Bangla). The `SafetySupportLayer` dynamically selects keyword sets based on the detected input language.
*   **No Hot-Reloading**: Configuration files are read once during component initialization. Changes to YAML files require a application restart to take effect.