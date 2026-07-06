"""
Voice routes Blueprint

Handles transcript, state machine, playback control, STT, and TTS endpoints.
"""

import os
import time
import logging
import tempfile
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file
from backend.agent.schemas import AgentRequest
from .shared import orchestrator

logger = logging.getLogger("zara.api.voice")

voice_bp = Blueprint("voice_bp", __name__)

# Lazy-initialized STT/TTS engine singletons
_stt_engine = None
_tts_engine = None


def _get_stt_engine():
    """Lazy-init the STT engine singleton."""
    global _stt_engine
    if _stt_engine is None:
        from backend.voice.stt_engine import STTEngine
        _stt_engine = STTEngine()
    return _stt_engine


def _get_tts_engine():
    """Lazy-init the TTS engine singleton."""
    global _tts_engine
    if _tts_engine is None:
        from backend.voice.tts_engine import TTSEngine
        _tts_engine = TTSEngine()
    return _tts_engine

@voice_bp.route("/api/voice/transcript", methods=["POST"])
def voice_transcript():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    session_id = data.get("session_id", "")
    language = data.get("language", "en")
    
    # Save user speech transcript using memory agent
    memory_agent = orchestrator.specialists.get("memory")
    if memory_agent:
        memory_agent.safe_process(AgentRequest(
            text=text,
            session_id=session_id,
            metadata={"purpose": "save_interaction", "intent": "voice_speech"}
        ))
        
    return jsonify({"success": True, "message": "Transcript recorded successfully."})

@voice_bp.route("/api/voice/state", methods=["POST", "GET"])
def voice_state():
    voice_agent = orchestrator.specialists.get("voice")
    if not voice_agent:
        return jsonify({"success": False, "errors": ["Voice Agent not registered."]}), 503
        
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        to_state = data.get("state", "")
        reason = data.get("reason", "API request")
        
        req = AgentRequest(
            text="",
            metadata={"purpose": "transition", "to_state": to_state, "reason": reason}
        )
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    # GET method
    req = AgentRequest(text="", metadata={"purpose": "get_state"})
    res = voice_agent.safe_process(req)
    return jsonify(res.to_dict())

@voice_bp.route("/api/voice/playback", methods=["POST"])
def voice_playback():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "") # "speak" | "stop" | "pause" | "resume"
    text = data.get("text", "")
    language = data.get("language", "en")
    
    voice_agent = orchestrator.specialists.get("voice")
    if not voice_agent:
        return jsonify({"success": False, "errors": ["Voice Agent not registered."]}), 503
        
    if action == "speak":
        req = AgentRequest(text=text, language=language, metadata={"purpose": "speak"})
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    elif action == "stop":
        req = AgentRequest(text="", metadata={"purpose": "stop_playback"})
        res = voice_agent.safe_process(req)
        return jsonify(res.to_dict())
        
    return jsonify({"success": False, "errors": [f"Unknown action: {action}"]}), 400


# ── STT Endpoint ────────────────────────────────────────────────────────

@voice_bp.route("/api/voice/stt", methods=["POST"])
def voice_stt():
    """
    Speech-to-Text endpoint.

    Accepts an audio file upload (multipart/form-data) and returns
    a transcript using faster-whisper.

    Input:
      - file: audio file (wav, webm, mp3, etc.)
      - language: optional language hint ("en", "bn", "bn_bd")
      - mode: optional ("realtime" | "file")

    Output:
      JSON with success, transcript, language, confidence, duration_ms, engine
    """
    start_time = time.perf_counter()

    # Check for audio file
    if "file" not in request.files:
        return jsonify({
            "success": False,
            "transcript": "",
            "language": "en",
            "confidence": 0.0,
            "duration_ms": 0,
            "engine": "none",
            "errors": ["No audio file provided. Use 'file' field in multipart form."],
        }), 400

    audio_file = request.files["file"]
    if not audio_file or not audio_file.filename:
        return jsonify({
            "success": False,
            "transcript": "",
            "language": "en",
            "confidence": 0.0,
            "duration_ms": 0,
            "engine": "none",
            "errors": ["Empty audio file."],
        }), 400

    language = request.form.get("language", "en")
    mode = request.form.get("mode", "file")

    # Save uploaded file to temp location
    temp_path = None
    try:
        suffix = Path(audio_file.filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            temp_path = tmp.name

        # Transcribe
        engine = _get_stt_engine()
        result = engine.transcribe(temp_path, language=language)

        return jsonify(result)

    except Exception as e:
        logger.error("STT endpoint error: %s", e)
        return jsonify({
            "success": False,
            "transcript": "",
            "language": language,
            "confidence": 0.0,
            "duration_ms": int((time.perf_counter() - start_time) * 1000),
            "engine": "none",
            "errors": [str(e)],
        }), 500

    finally:
        # Clean up temp file
        if temp_path and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ── TTS Endpoint ─────────────────────────────────────────────────────────

@voice_bp.route("/api/voice/tts", methods=["POST"])
def voice_tts():
    """
    Text-to-Speech endpoint.

    Accepts JSON with text to synthesize and returns audio file.

    Input (JSON):
      - text: text to synthesize (required)
      - voice: voice preference ("female", "male") default "female"
      - voice_profile: ZARA voice profile key
          ("zara_soft", "zara_cute", "zara_professional", "zara_night")
          default "zara_soft"
      - language: language code ("en", "bn", "bn_bd") default "en"
      - speed: playback speed (0.5-2.0) default 1.0

    Output:
      Audio file (WAV) with Content-Type audio/wav,
      or JSON error if TTS unavailable.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    voice = data.get("voice", "female")
    voice_profile = data.get("voice_profile", None)
    speaking_style = data.get("speaking_style", None)
    emotion_context = data.get("emotion_context", None)
    language = data.get("language", "en")
    speed = float(data.get("speed", 1.0))

    # Validate text
    if not text or not text.strip():
        return jsonify({
            "success": False,
            "errors": ["Text field is required and must be non-empty."],
        }), 400

    engine = _get_tts_engine()

    if not engine.is_available:
        return jsonify({
            "success": False,
            "errors": ["TTS engine not available. Use browser fallback."],
            "engine": "none",
        }), 503

    result = engine.synthesize(
        text=text,
        voice=voice,
        language=language,
        speed=speed,
        voice_profile=voice_profile,
        speaking_style=speaking_style,
        emotion_context=emotion_context,
    )

    if result["success"] and result.get("audio_path"):
        audio_path = result["audio_path"]
        if os.path.isfile(audio_path):
            # Return the audio file
            response = send_file(
                audio_path,
                mimetype="audio/wav",
                as_attachment=False,
                download_name="tts_response.wav",
            )
            # Add metadata headers
            response.headers["X-TTS-Engine"] = result.get("engine", "unknown")
            response.headers["X-TTS-Cached"] = str(result.get("cached", False)).lower()
            response.headers["X-TTS-Profile"] = result.get("profile", "zara_soft")
            response.headers["X-TTS-Style"] = result.get("style", "calm_support")
            # Include chunks info as JSON header
            import json
            chunks = result.get("chunks", [])
            if chunks:
                response.headers["X-TTS-Chunks"] = json.dumps(chunks[:5])  # first 5 chunks max
            return response

    # If synthesis failed
    return jsonify({
        "success": False,
        "errors": result.get("errors", ["Synthesis failed"]),
        "engine": result.get("engine", "unknown"),
        "profile": result.get("profile", "zara_soft"),
        "style": result.get("style", "calm_support"),
    }), 500


# ── Speaking Styles Endpoint ────────────────────────────────────────────

@voice_bp.route("/api/voice/styles", methods=["GET"])
def voice_styles():
    """Return available speaking styles and default style."""
    from backend.voice.speaking_styles import get_all_styles, DEFAULT_SPEAKING_STYLE
    return jsonify({
        "styles": get_all_styles(),
        "default_style": DEFAULT_SPEAKING_STYLE,
    })


# ── Voice Engine Info Endpoint ────────────────────────────────────────────

@voice_bp.route("/api/voice/engines", methods=["GET"])
def voice_engines():
    """Return status of STT and TTS engines, plus available voice profiles."""
    from backend.voice.voice_profiles import get_all_profiles, DEFAULT_VOICE_PROFILE
    stt = _get_stt_engine()
    tts = _get_tts_engine()
    return jsonify({
        "stt": stt.get_info(),
        "tts": tts.get_info(),
        "profiles": get_all_profiles(),
        "default_profile": DEFAULT_VOICE_PROFILE,
    })
