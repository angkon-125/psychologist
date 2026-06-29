# ZARA — Offline AI Emotional Support Companion

ZARA is an **offline-first** emotional support companion built with Python and Flask.
It uses **no large language models, no cloud APIs, and no external data services**.
All emotion analysis, response generation, voice I/O, and session storage happen locally.

## Key Features

- **Emotion Engine** — Keyword-based sentiment analysis, fuzzy logic, Bayesian reasoning, and emotional memory
- **SCEA** (Self-Cognitive & Emotional Architecture) — Neurochemistry simulation, needs, goals, identity, consciousness, meta-cognition
- **Safety Layer** — Crisis detection (self-harm, abuse, panic, medical emergency), diagnosis blocking, safe response templates in English & Bangla
- **Voice I/O** — TTS (Piper → eSpeak → pyttsx3 fallback chain) and STT (Vosk / Whisper)
- **Interaction Modes** — Text, Voice, and Hybrid with session persistence
- **Support Tools** — Pre-authored calming exercises, breathing techniques, journaling prompts, reflection questions, mood check-ins, grounding exercises
- **Bilingual** — Full English and Bangla (Bengali) support
- **Session Management** — JSON file-based persistence with summaries and follow-up suggestions

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
cd psychologist
pip install -r requirements.txt
```

### Running

```bash
python run_app.py
```

The server starts on `http://127.0.0.1:5000` by default.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_HOST` | `127.0.0.1` | Bind address |
| `FLASK_PORT` | `5000` | Listen port |
| `FLASK_DEBUG` | `0` | Set to `1` for debug mode (never use in production) |

### Production Deployment

For production, use a WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run_app:app
```

Set `FLASK_DEBUG=0` and bind to `127.0.0.1` behind a reverse proxy.

## Project Structure

```
psychologist/
├── app.py                  # Flask application & API routes
├── run_app.py              # Entry point with logging setup
├── system_constants.py     # Centralized configuration constants
├── logger.py               # Structured logging (zara.* namespace)
├── rate_limiter.py         # In-memory rate limiting & input validation
├── requirements.txt
├── config/
│   ├── safety_config.yaml       # Crisis keywords & safe templates
│   ├── interaction_config.yaml   # Interaction mode settings
│   ├── tts_config.yaml           # TTS engine configuration
│   ├── voice_config.yaml         # Voice input configuration
│   └── single_voice_tts.yaml     # Locked single voice settings
├── emotion_engine/
│   ├── emotion_engine.py         # Main emotion processing pipeline
│   ├── models.py                 # EmotionalState, PersonalityTraits
│   ├── sentiment_analysis/        # Keyword-based sentiment
│   ├── fuzzy_logic/              # Fuzzy emotion blending
│   ├── bayesian_engine/          # Bayesian emotion updates
│   ├── reasoning_engine/        # Blended reasoning
│   ├── response_generator/      # Template-based responses
│   ├── emotional_memory/        # Short/long-term memory
│   ├── context_engine/          # Conversation context
│   ├── personality_engine/     # Big Five personality model
│   ├── behavior_predictor/      # Behavior prediction
│   ├── state_machine/           # Emotion state transitions
│   ├── interaction/             # Text/Voice/Hybrid handlers, sessions, safety
│   ├── voice_output/            # TTS manager & engine fallback chain
│   ├── voice_system/            # STT manager & voice emotion detection
│   └── visualization_dashboard/ # Optional matplotlib dashboard
├── scea/
│   ├── core/scea.py             # SCEA main orchestrator
│   ├── neurochemistry/           # Dopamine, serotonin, oxytocin, cortisol
│   ├── needs_engine/            # Maslow-style needs hierarchy
│   ├── consciousness_layer/     # Consciousness simulation
│   ├── goal_generation/         # Goal-directed behavior
│   ├── identity_formation/      # Self-identity evolution
│   ├── imagination/             # Creative imagination
│   ├── meta_cognition/          # Self-reflection
│   ├── cognitive_dissonance/    # Cognitive dissonance engine
│   ├── conflict_engine/         # Emotional conflict resolution
│   ├── emotional_evolution/     # Long-term emotional development
│   ├── emotional_physics/       # Emotion interaction physics
│   ├── relationship_engine/     # Relationship modeling
│   └── world_model/             # World model
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── assets/languages/        # i18n: en.json, bn_bd.json
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_api_endpoints.py    # 32 API integration tests
│   ├── test_safety_edge_cases.py # 19 safety layer tests
│   ├── test_session_persistence.py # 28 session lifecycle tests
│   └── test_interaction_pipeline.py # 29 pipeline integration tests
└── docs/
    ├── ARCHITECTURE.md
    └── API.md
```

## Testing

```bash
cd psychologist
python -m pytest tests/ -v
```

108 tests cover API endpoints, safety edge cases, session persistence, and the full interaction pipeline.

### Voice System Tests

Voice subsystem tests require audio hardware/models and are separate:

```bash
python -m pytest emotion_engine/voice_output/tests/ -v
python -m pytest emotion_engine/interaction/tests/ -v
python -m pytest scea/tests/ -v
```

## Configuration

All tunable parameters are centralized in [`system_constants.py`](system_constants.py):

| Constant | Default | Description |
|---|---|---|
| `EMOTION_DECAY_FACTOR` | 0.85 | Emotion decay per cycle |
| `EMOTION_HISTORY_LIMIT` | 100 | Max emotional states in history |
| `MAX_TEXT_RESPONSE_LENGTH` | 500 | Max text response chars |
| `MAX_VOICE_RESPONSE_LENGTH` | 200 | Max voice response chars |
| `MAX_INPUT_LENGTH` | 5000 | Max user input chars |
| `SESSION_HISTORY_LIMIT` | 50 | Max stored session files |
| `RATE_LIMIT_REQUESTS` | 60 | Default API rate limit |
| `RATE_LIMIT_STRICT_REQUESTS` | 30 | Strict endpoint rate limit |

## Safety

ZARA is **not** a replacement for professional mental health care. The safety layer:

1. **Detects crisis signals** — self-harm, harm to others, abuse, panic, medical emergencies (English & Bangla)
2. **Blocks diagnoses** — Prevents the system from making medical claims
3. **Provides crisis templates** — Pre-authored safe responses with emergency guidance
4. **Filters responses** — Removes any diagnosis language from generated responses
5. **Reminds about professional help** — Built-in disclaimers

Crisis keywords and safe templates are configured in [`config/safety_config.yaml`](config/safety_config.yaml).

## Limitations

- Keyword-based emotion detection (no ML models)
- Template-based response generation (no LLM)
- Single-process rate limiting (not suitable for multi-worker without shared backend)
- Session storage is file-based (no database)
- Voice models must be downloaded separately for Vosk/Whisper/Piper

## License

This project is provided as-is for educational and development purposes.
