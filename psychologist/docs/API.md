# ZARA API Reference

Base URL: `http://127.0.0.1:5000`

All POST endpoints accept `application/json` and return `application/json`.
All endpoints are rate-limited (60 req/60s for reads, 30 req/60s for writes).

## Health

### GET /api/health

Returns system health and voice subsystem availability.

**Response:**
```json
{
  "status": "ok",
  "voice_output_available": true,
  "voice_input_available": false,
  "voice_emotion_available": false
}
```

## Emotion Engine

### POST /api/emotion/process

Process text through the emotion engine pipeline.

**Request:**
```json
{
  "text": "I'm feeling really happy today!",
  "additional_emotions": {}
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Input text (max 5000 chars) |
| `additional_emotions` | object | No | Direct emotion overrides (e.g. `{"happiness": 0.8}`) |

**Response (200):**
```json
{
  "emotional_state": {
    "primary_emotions": {"happiness": 0.65, "sadness": 0.05},
    "secondary_emotions": {"trust": 0.3},
    "advanced_emotions": {"hope": 0.2},
    "intensity": 0.7
  },
  "sentiment": {"sentiment": 0.8, "intensity": 0.7},
  "context": {"conversation_history": [], "emotional_trend": []},
  "reasoning": {"mode": "supportive", "bayesian_updated": {}},
  "predictions": {},
  "response": "I'm glad you're feeling happy!",
  "dominant_emotion": "happiness"
}
```

**Errors:** 400 (missing/empty/too-long text), 500 (processing error)

### GET /api/emotion/state

Returns the current emotional state snapshot.

**Response (200):**
```json
{
  "primary_emotions": {"happiness": 0.3, "sadness": 0.1},
  "secondary_emotions": {},
  "advanced_emotions": {},
  "intensity": 0.3
}
```

### GET /api/emotion/personality

Returns the current Big Five personality traits.

**Response (200):**
```json
{
  "openness": 0.5,
  "conscientiousness": 0.5,
  "extraversion": 0.5,
  "agreeableness": 0.5,
  "neuroticism": 0.5
}
```

### POST /api/emotion/personality

Update personality traits.

**Request:**
```json
{
  "openness": 0.8,
  "extraversion": 0.6
}
```

Any subset of the five traits is accepted. Values must be 0.0–1.0.

**Response (200):** Returns the updated full personality object.

**Errors:** 400 (invalid field name or value type)

### GET /api/emotion/memory

Returns emotional memory summary.

**Response (200):**
```json
{
  "short_term_count": 15,
  "long_term_count": 3,
  "recent_emotions": ["happiness", "sadness", "neutral"]
}
```

### POST /api/emotion/reset

Resets the emotion engine to default state.

**Response (200):**
```json
{"status": "ok"}
```

## SCEA

### POST /api/scea/step

Advance the SCEA system by one step.

**Request:**
```json
{
  "triggers": ["user_interaction"],
  "experiences": [{"type": "positive", "intensity": 0.5}]
}
```

Both fields are optional. Empty body `{}` is valid.

**Response (200):**
```json
{
  "step": 1,
  "neurochemistry": {"dopamine": 0.5, "serotonin": 0.4},
  "needs": {"physiological": 0.3, "safety": 0.4},
  "decision": {"action": "seek_connection"},
  "consciousness": {"level": 0.6},
  "identity": {"self_concept": "supportive"},
  "goals": [{"description": "help user", "priority": 0.8}]
}
```

### POST /api/scea/interact

Record an interaction with an entity (user, object, concept).

**Request:**
```json
{
  "entity_id": "user_1",
  "interaction_type": "conversation",
  "positive": true
}
```

**Response (200):** Updated relationship state for the entity.

## Session Management

### POST /api/session/start

Start a new interaction session.

**Request:**
```json
{
  "mode": "text",
  "language": "en"
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `mode` | string | current mode | `text`, `voice`, or `hybrid` |
| `language` | string | `en` | `en` or `bn` |

**Response (200):** Full session state object (see GET /api/session/current).

### POST /api/session/end

End the current session. Generates summary and follow-up suggestions, saves to disk.

**Response (200):**
```json
{
  "session_id": "uuid",
  "summary": "Session with 3 interactions. Primary emotional theme: happiness.",
  "follow_up_suggestions": [
    "Remember, reaching out to a trusted person or professional is always a good step."
  ],
  "start_time": "2025-01-01T10:00:00",
  "end_time": "2025-01-01T10:30:00",
  "user_messages": [...],
  "assistant_messages": [...]
}
```

**Errors:** 400 (no active session)

### GET /api/session/current

Returns the current active session, or a status if none.

**Response (200, with session):** Full session state:
```json
{
  "session_id": "uuid",
  "active_mode": "text",
  "start_time": "2025-01-01T10:00:00",
  "end_time": null,
  "current_emotion_state": {},
  "mood_timeline": [],
  "safety_flags": [],
  "user_messages": [],
  "assistant_messages": [],
  "detected_emotions": [],
  "summary": "",
  "language": "en"
}
```

**Response (200, no session):**
```json
{"status": "no_active_session"}
```

### GET /api/session/history

Returns summaries of recent past sessions.

**Response (200):**
```json
[
  {
    "session_id": "uuid",
    "start_time": "2025-01-01T10:00:00",
    "end_time": "2025-01-01T10:30:00",
    "summary": "Session with 3 interactions...",
    "message_count": 3,
    "active_mode": "text",
    "language": "en"
  }
]
```

## Interaction

### POST /api/interaction/message

Process a user message through the full interaction pipeline. This is the primary endpoint for conversation.

**Request:**
```json
{
  "text": "I feel stressed today",
  "language": "en",
  "user_mood": null,
  "speak_response": false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `text` | string | required | User message (max 5000 chars) |
| `language` | string | `en` | `en` or `bn` |
| `user_mood` | string\|null | null | User-selected mood override |
| `speak_response` | boolean | false | If true, TTS speaks the response |

**Response (200):**
```json
{
  "user_message": {
    "message_id": "uuid",
    "raw_text": "I feel stressed today",
    "normalized_text": "I feel stressed today",
    "detected_emotion": "stress",
    "confidence": 0.6,
    "timestamp": "2025-01-01T10:00:00",
    "input_type": "text"
  },
  "assistant_message": {
    "message_id": "uuid",
    "response_text": "I can feel that you're carrying something heavy...",
    "response_type": "supportive",
    "safety_level": "moderate",
    "spoken": false,
    "timestamp": "2025-01-01T10:00:00"
  },
  "emotion_result": {
    "dominant_emotion": "stress",
    "confidence": 0.6,
    "emotional_state": {}
  },
  "safety_assessment": {
    "risk_level": "moderate",
    "detected_signals": ["stressed"],
    "should_escalate": false,
    "safe_response_template": "I can feel that things are heavy..."
  }
}
```

If a crisis is detected, `response_type` becomes `crisis_support` and the safe template replaces the generated response.

### POST /api/interaction/voice/start

Start voice input listening (voice/hybrid modes only).

**Response (200):** Listening status.

**Errors:** 400 (text mode), 500 (voice error)

### POST /api/interaction/voice/stop

Stop listening and process the captured transcript.

**Response (200):** Same format as POST /api/interaction/message, or `{"status": "no_input"}` if no speech detected.

### GET /api/interaction/voice/status

Returns current voice I/O status.

**Response (200):**
```json
{
  "is_listening": false,
  "is_speaking": false,
  "audio_level": 0.0,
  "current_transcript": "",
  "push_to_talk": true,
  "stt_available": true,
  "tts_available": true,
  "mode": "hybrid"
}
```

### GET /api/interaction/voice/level

Returns current audio input level (0.0–1.0).

**Response (200):**
```json
{"audio_level": 0.15}
```

### POST /api/interaction/mode

Switch the interaction mode.

**Request:**
```json
{"mode": "voice"}
```

**Response (200):**
```json
{
  "success": true,
  "previous_mode": "text",
  "current_mode": "voice",
  "config": {
    "mode_name": "voice",
    "voice_input_enabled": true,
    "text_input_enabled": false,
    "voice_output_enabled": true,
    "auto_listen_after_response": false
  }
}
```

### GET /api/interaction/mode

Returns current mode and allowed modes.

**Response (200):**
```json
{
  "current_mode": "hybrid",
  "config": {"mode_name": "hybrid", ...},
  "allowed_modes": ["text", "voice", "hybrid"],
  "mode_history_count": 2
}
```

## Support Tools

All support endpoints accept `{"language": "en"}` and return a `SupportAction` object.

### POST /api/support/calm

Returns a calming exercise script.

### POST /api/support/breathing

Returns a guided breathing exercise (4-7-8, box breathing, or deep breathing).

### POST /api/support/journal

Returns a journaling prompt. Accepts optional `emotion` field for tailored prompts.

**Request:**
```json
{"language": "en", "emotion": "sadness"}
```

### POST /api/support/reflection

Returns self-reflection questions.

### POST /api/support/mood-checkin

Returns a mood check-in prompt (1-5 scale or open-ended).

**Response (all support endpoints):**
```json
{
  "action_type": "breathing_exercise",
  "trigger_reason": "User requested breathing exercise",
  "script_key": "breathing_exercise_en",
  "language": "en",
  "completed": false,
  "timestamp": "2025-01-01T10:00:00",
  "content": "Let's try the 4-7-8 breathing technique..."
}
```

## Safety

### GET /api/safety/status

Returns the safety state of the current session.

**Response (200):**
```json
{
  "risk_level": "none",
  "flags": []
}
```

Risk levels: `none`, `low`, `moderate`, `high`, `critical`.

## Voice Output

These endpoints are only available when TTS is initialized. If unavailable, all return 501.

### POST /api/voice-output/tts

Speak text using the locked local voice.

**Request:**
```json
{
  "text": "Hello, how are you?",
  "language": "en",
  "emotion": "happy",
  "save": false
}
```

**Response (200):**
```json
{
  "success": true,
  "audio_path": "audio_outputs/tts_1.wav",
  "text": "Hello, how are you?",
  "language": "en",
  "emotion": "happy"
}
```

### POST /api/voice-output/tts/stop

Stop current voice playback.

### POST /api/voice-output/tts/replay

Replay the last spoken audio.

### GET /api/voice-output/status

Returns voice lock status and activity log.

## Error Responses

All errors return JSON with `error` and `message` fields:

```json
{"error": "bad_request", "message": "text must not be empty."}
```

| Status | Error | Description |
|---|---|---|
| 400 | `invalid_input` | Missing/empty/invalid field |
| 400 | `bad_request` | Malformed request |
| 404 | `not_found` | Unknown endpoint |
| 405 | `method_not_allowed` | Wrong HTTP method |
| 429 | `rate_limited` | Too many requests |
| 500 | `processing_error` | Internal processing failure |
| 500 | `internal_error` | Unexpected error |
| 501 | - | Voice output not available |
