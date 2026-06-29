# ZARA Architecture

## System Overview

ZARA is an offline-first emotional support companion. The architecture follows a layered design with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│                Frontend (HTML/CSS/JS)         │
├─────────────────────────────────────────────┤
│              Flask API Layer (app.py)         │
│  ┌───────────┐ ┌──────────┐ ┌─────────────┐  │
│  │  Rate     │ │  Input   │ │   Error     │  │
│  │  Limiter  │ │ Validator│ │  Handlers   │  │
│  └───────────┘ └──────────┘ └─────────────┘  │
├─────────────────────────────────────────────┤
│           Interaction Layer                   │
│  ┌──────┐ ┌───────┐ ┌────────┐ ┌──────────┐ │
│  │ Text │ │ Voice │ │Hybrid  │ │ Session  │ │
│  │Handler│ │Handler│ │Handler │ │ Manager  │ │
│  └──────┘ └───────┘ └────────┘ └──────────┘ │
│  ┌──────────────────┐ ┌───────────────────┐  │
│  │ Safety Support   │ │  Support Tools    │  │
│  │     Layer        │ │  (calm, breathing) │  │
│  └──────────────────┘ └───────────────────┘  │
├─────────────────────────────────────────────┤
│           Emotion Engine                      │
│  ┌────────┐┌────────┐┌────────┐┌──────────┐ │
│  │Sentiment││Fuzzy  ││Bayesian││Reasoning │ │
│  │Analyzer││Engine ││Engine  ││Engine    │ │
│  └────────┘└────────┘└────────┘└──────────┘ │
│  ┌────────────┐┌──────────┐┌─────────────┐  │
│  │  Memory    ││ Context  ││ Personality │  │
│  │  Engine    ││ Engine   ││   Engine    │  │
│  └────────────┘└──────────┘└─────────────┘  │
├─────────────────────────────────────────────┤
│              SCEA System                      │
│  ┌────────────┐┌────────┐┌────────────────┐  │
│  │Neurochem   ││ Needs  ││Consciousness  │  │
│  └────────────┘└────────┘└────────────────┘  │
│  ┌────────┐┌────────┐┌──────────────────┐   │
│  │Identity││Goals   ││Meta-Cognition    │   │
│  └────────┘└────────┘└──────────────────┘   │
├─────────────────────────────────────────────┤
│              Voice Subsystems                 │
│  ┌────────────────┐  ┌──────────────────┐    │
│  │  Voice Output  │  │  Voice Input     │    │
│  │  (TTS)         │  │  (STT)           │    │
│  │  Piper→eSpeak  │  │  Vosk / Whisper  │    │
│  │  →pyttsx3      │  │                  │    │
│  └────────────────┘  └──────────────────┘    │
├─────────────────────────────────────────────┤
│           Persistence (JSON files)            │
│           Sessions / Audio / Logs             │
└─────────────────────────────────────────────┘
```

## Layers

### 1. API Layer (`app.py`)

The Flask application exposes REST endpoints for all functionality. Key responsibilities:

- **Rate limiting** — In-memory sliding window per client IP (60 req/60s read, 30 req/60s write)
- **Input validation** — `validate_text_input()` checks for presence, type, length, and emptiness
- **Error handling** — Structured JSON error responses for 400, 404, 405, 429, 500
- **Health check** — `/api/health` endpoint for monitoring

The API layer initializes all subsystems at import time. Voice systems are wrapped in try/except blocks so the app degrades gracefully without audio hardware.

### 2. Interaction Layer (`emotion_engine/interaction/`)

Manages the conversation flow across three modes:

- **TextModeHandler** — Full pipeline: normalize → safety check → emotion detect → response → optional TTS → session save
- **VoiceModeHandler** — STT input → same pipeline as text → TTS output
- **HybridModeHandler** — Combines text and voice, delegates to the appropriate handler

**Safety Support Layer** runs before emotion processing:
1. Crisis detection (keyword matching against `safety_config.yaml`)
2. If crisis detected → return safe template, skip emotion response
3. If moderate distress → return distress template
4. If none → proceed to emotion engine
5. After response generation, `filter_response()` removes diagnosis language

**Session Manager** handles:
- Session lifecycle (create, end, save)
- Message recording (user + assistant)
- Summary generation with dominant emotion and safety notes
- Follow-up suggestions based on emotional patterns
- Old session cleanup (max 50 files by default)
- Recurring emotion analysis across sessions

### 3. Emotion Engine (`emotion_engine/`)

The core emotion processing pipeline:

```
Input Text
    │
    ▼
Sentiment Analyzer ──► sentiment score (-1 to +1), intensity, keywords
    │
    ▼
Update Emotional State ──► Adjust primary/secondary/advanced emotions
    │                     based on sentiment + keyword boosts
    ▼
Context Engine ──► Conversation history, emotional trends
    │
    ▼
Reasoning Engine ──► Blends current state (70%) with Bayesian update (30%)
    │                 Fuzzy logic + state machine transitions
    ▼
Response Generator ──► Template-based response matched to emotion + reasoning
    │
    ▼
Emotional Memory ──► Store interaction with importance score
    │
    ▼
Behavior Predictor ──► Predict likely behaviors from emotional state
    │
    ▼
Decay ──► All emotions decay by 0.85 factor each cycle
```

**Emotional State Structure:**
- **Primary emotions**: happiness, sadness, anger, fear, surprise, disgust
- **Secondary emotions**: trust, anticipation, joy, sadness (variant), anger (variant), fear (variant)
- **Advanced emotions**: love, hope, compassion, loneliness, jealousy, guilt, shame, pride, gratitude

**Personality Model:** Big Five (OCEAN) — openness, conscientiousness, extraversion, agreeableness, neuroticism. Personality modulates emotional responses.

### 4. SCEA System (`scea/`)

The Self-Cognitive & Emotional Architecture adds a meta-cognitive layer:

- **Neurochemistry** — Simulates dopamine, serotonin, oxytocin, cortisol levels that influence emotional state
- **Needs Engine** — Maslow-style hierarchy: physiological, safety, belonging, esteem, self-actualization
- **Consciousness Layer** — Awareness level simulation
- **Goal Generation** — Creates goals based on needs and emotional state
- **Identity Formation** — Evolves self-identity over time (updated every 10 steps)
- **Imagination** — Generates hypothetical scenarios
- **Meta-Cognition** — Self-reflection on emotional state
- **Cognitive Dissonance** — Detects and resolves conflicting beliefs
- **Conflict Engine** — Resolves emotional conflicts
- **Emotional Evolution** — Long-term emotional development tracking
- **Emotional Physics** — Models emotion interaction dynamics
- **Relationship Engine** — Models relationships with entities
- **World Model** — Internal model of the world

SCEA runs in discrete steps via `scea_system.step(triggers, experiences)`. Each step updates neurochemistry, evaluates needs, generates goals, and updates consciousness.

### 5. Voice Subsystems

**Voice Output (TTS):**
- Engine fallback chain: Piper → eSpeak → pyttsx3
- Single locked voice (no voice selection UI)
- Config in `config/single_voice_tts.yaml`
- `TTSManager` coordinates engine selection and audio playback
- `VoiceStyleMapper` maps emotions to speech parameters (rate, pitch, volume)

**Voice Input (STT):**
- Engine options: Vosk (offline) / Whisper (faster-whisper)
- `STTManager` handles initialization and transcription
- Voice Activity Detection (VAD) using webrtcvad
- Audio preprocessing and feature extraction

**Voice Emotion Detection:**
- Extracts acoustic features (pitch, energy, spectral features) via librosa
- `VoiceEmotionDetector` classifies emotion from voice features
- `EmotionFusion` combines text-based and voice-based emotion detection

### 6. Persistence

All data is stored as local JSON files:

- **Sessions** — `sessions/session_{uuid}.json` with full conversation history, emotions, safety flags, summary
- **Audio** — `audio_outputs/tts_{n}.wav` for TTS output
- **Config** — YAML files in `config/`
- **i18n** — JSON files in `frontend/assets/languages/`

No database, no external storage. The file-based approach ensures complete offline operation and easy backup.

## Cross-Cutting Concerns

### Logging

All subsystems use the `zara.*` logger namespace via `logger.py`:

```python
logger = logging.getLogger("zara.session")
logger.info("Session started")
```

Format: `2025-01-01 10:00:00 [INFO] zara.session: Session started`

### Configuration Constants

All magic numbers are centralized in `system_constants.py`. No hardcoded values in business logic.

### Safety

Safety is enforced at multiple levels:
1. **Input validation** — `validate_text_input()` in the API layer
2. **Crisis detection** — `SafetySupportLayer.assess_input()` before emotion processing
3. **Response filtering** — `SafetySupportLayer.filter_response()` after response generation
4. **Diagnosis blocking** — Pattern matching against `diagnosis_block_patterns` in config
5. **Professional help reminders** — Built into session summaries and follow-ups

### Internationalization

- English (`en`) and Bangla (`bn` / `bn_bd`) supported throughout
- Safety keywords in both languages
- Support tool scripts in both languages
- Frontend i18n via JSON language files

## Data Flow: Text Interaction

```
User sends POST /api/interaction/message
    │
    ▼
Rate limiter checks IP bucket
    │
    ▼
validate_text_input() — check presence, type, length
    │
    ▼
Ensure active session (create if needed)
    │
    ▼
Route to handler based on mode (text/voice/hybrid)
    │
    ▼
TextModeHandler.process_text():
    │
    ├─► Normalize text (strip, collapse whitespace)
    │
    ├─► SafetySupportLayer.assess_input()
    │       └─► Crisis? → return safe template, skip emotion
    │       └─► Distress? → return distress template
    │       └─► None → continue
    │
    ├─► EmotionEngine.process_input()
    │       └─► Sentiment → Update state → Context → Reason → Response
    │
    ├─► Apply safety filter to generated response
    │
    ├─► Build UserMessage + AssistantMessage objects
    │
    ├─► Optional TTS speak (if speak_response=True)
    │
    └─► SessionManager.add_user_message() + add_assistant_message()
            └─► Auto-save session JSON to disk
    │
    ▼
Return JSON response with all interaction data
```
