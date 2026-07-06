import os
import json
import queue
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

from logger import get_logger
from rate_limiter import rate_limit, validate_text_input
from system_constants import SESSION_ACTIVITY_LOG_LIMIT
from emotion_engine import EmotionEngine
from emotion_engine.models import PersonalityTraits
from scea.core.scea import SCEA
from emotion_engine.interaction.interaction_mode_manager import InteractionModeManager
from emotion_engine.interaction.session_manager import SessionManager
from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
from emotion_engine.interaction.support_tools import SupportTools
from emotion_engine.interaction.text_mode_handler import TextModeHandler
from emotion_engine.interaction.voice_mode_handler import VoiceModeHandler
from emotion_engine.interaction.hybrid_mode_handler import HybridModeHandler
from emotion_engine.interaction.confidence_scorer import ConfidenceScorer
from emotion_engine.interaction.correction_detector import CorrectionDetector
from emotion_engine.interaction.accuracy_logger import AccuracyLogger

logger = get_logger("app")

app = Flask(__name__, static_folder='frontend')
CORS(app)

# ── Structured error handlers ─────────────────────────────────────

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({"error": "bad_request", "message": str(e)}), 400

@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"error": "not_found", "message": str(e)}), 404

@app.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({"error": "method_not_allowed", "message": str(e)}), 405

@app.errorhandler(429)
def handle_rate_limited(e):
    return jsonify({"error": "rate_limited", "message": "Too many requests. Please slow down."}), 429

@app.errorhandler(500)
def handle_internal_error(e):
    logger.error("Internal server error: %s", e)
    return jsonify({"error": "internal_error", "message": "An unexpected error occurred."}), 500

# ── Health check endpoint ──────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "ok",
        "voice_output_available": voice_output_available,
        "voice_input_available": voice_input_available,
        "voice_emotion_available": voice_emotion_available,
    })

emotion_engine = EmotionEngine()
scea_system = SCEA()

# Voice output setup — single locked local voice
voice_output_available = False
tts_manager = None
current_activity_log = []
last_tts_result = None

def on_activity(text: str):
    global current_activity_log
    current_activity_log.append(text)

try:
    from emotion_engine.voice_output import TTSManager, SingleVoiceConfig

    voice_config = SingleVoiceConfig()
    tts_manager = TTSManager(voice_config)
    tts_manager.set_activity_callback(on_activity)
    voice_output_available = True
    logger.info("Voice output system initialized — single local voice locked")
except Exception as e:
    logger.warning("Voice output system not available: %s", e)

# Interaction System Setup
safety_layer = SafetySupportLayer()
support_tools = SupportTools()
session_manager = SessionManager()
mode_manager = InteractionModeManager(default_mode="hybrid")

# Voice input setup
stt_manager = None
voice_input_available = False
try:
    from emotion_engine.voice_system.stt_manager import STTManager
    stt_manager = STTManager()
    stt_manager.initialize_engines()
    stt_manager.set_activity_callback(on_activity)
    voice_input_available = True
    logger.info("Voice input system initialized")
except Exception as e:
    logger.warning("Voice input system not available: %s", e)

# Voice emotion setup
voice_emotion_available = False
voice_feature_extractor = None
voice_emotion_detector = None
emotion_fusion = None
try:
    from emotion_engine.voice_system.voice_feature_extractor import VoiceFeatureExtractor
    from emotion_engine.voice_system.voice_emotion_detector import VoiceEmotionDetector
    from emotion_engine.voice_system.emotion_fusion import EmotionFusion
    
    voice_feature_extractor = VoiceFeatureExtractor()
    voice_emotion_detector = VoiceEmotionDetector()
    emotion_fusion = EmotionFusion()
    voice_emotion_available = True
    logger.info("Voice emotion components initialized")
except Exception as e:
    logger.warning("Voice emotion components not available: %s", e)

text_handler = TextModeHandler(
    emotion_engine=emotion_engine,
    tts_manager=tts_manager,
    safety_layer=safety_layer,
    session_manager=session_manager
)

voice_handler = VoiceModeHandler(
    emotion_engine=emotion_engine,
    stt_manager=stt_manager,
    tts_manager=tts_manager,
    voice_feature_extractor=voice_feature_extractor,
    voice_emotion_detector=voice_emotion_detector,
    emotion_fusion=emotion_fusion,
    safety_layer=safety_layer,
    session_manager=session_manager
)

hybrid_handler = HybridModeHandler(
    text_handler=text_handler,
    voice_handler=voice_handler,
    session_manager=session_manager
)

mode_manager.set_activity_callback(on_activity)
session_manager.set_activity_callback(on_activity)
text_handler.set_activity_callback(on_activity)
voice_handler.set_activity_callback(on_activity)
hybrid_handler.set_activity_callback(on_activity)

# ── Accuracy System (NEW) ────────────────────────────────────────
confidence_scorer = ConfidenceScorer()
correction_detector = CorrectionDetector()
accuracy_logger = AccuracyLogger()

# ── Voice Conversation Engine (NEW) ─────────────────────────────
conversation_engine = None
voice_preferences = None
try:
    from emotion_engine.voice_engine import (
        ConversationEngine, ResponseGenerator, VoicePreferences,
    )
    from emotion_engine.voice_engine.ollama_client import OllamaClient

    voice_preferences = VoicePreferences()

    # Optional Ollama LLM
    ollama_client = None
    if os.environ.get("USE_OLLAMA", "").lower() == "true":
        try:
            ollama_client = OllamaClient()
            if ollama_client.is_available:
                logger.info("Ollama LLM enabled for voice engine")
            else:
                logger.info("Ollama requested but not reachable — will use EmotionEngine")
                ollama_client = None
        except Exception as e:
            logger.warning("Ollama init failed: %s", e)
            ollama_client = None

    response_generator = ResponseGenerator(emotion_engine, ollama_client)

    conversation_engine = ConversationEngine(
        stt_manager=stt_manager,
        tts_manager=tts_manager,
        response_generator=response_generator,
        preferences=voice_preferences,
    )
    logger.info("Voice conversation engine initialized")
except Exception as e:
    logger.warning("Voice conversation engine not available: %s", e)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('frontend', path)

@app.route('/api/emotion/process', methods=['POST'])
@rate_limit(app, requests=60, window_seconds=60)
def process_emotion():
    data = request.get_json(silent=True)
    valid, error, text = validate_text_input(data, max_length=5000)
    if not valid:
        return jsonify({"error": "invalid_input", "message": error}), 400
    additional_emotions = data.get('additional_emotions', None)
    
    try:
        result = emotion_engine.process_input(text, additional_emotions)
        return jsonify(result)
    except Exception as e:
        logger.error("Emotion processing failed: %s", e)
        return jsonify({"error": "processing_error", "message": str(e)}), 500

@app.route('/api/emotion/state', methods=['GET'])
def get_emotion_state():
    return jsonify(emotion_engine.get_emotional_state())

@app.route('/api/emotion/personality', methods=['GET'])
def get_personality():
    return jsonify(emotion_engine.get_personality())

@app.route('/api/emotion/personality', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def set_personality():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "invalid_input", "message": "Request body must be JSON."}), 400
    try:
        personality = PersonalityTraits(**data)
        emotion_engine.personality_engine.traits = personality
        return jsonify(emotion_engine.get_personality())
    except TypeError as e:
        return jsonify({"error": "invalid_input", "message": f"Invalid personality traits: {e}"}), 400

@app.route('/api/emotion/memory', methods=['GET'])
def get_memory():
    return jsonify(emotion_engine.get_memory_summary())

@app.route('/api/emotion/reset', methods=['POST'])
def reset_emotion():
    emotion_engine.reset()
    return jsonify({'status': 'ok'})

@app.route('/api/scea/step', methods=['POST'])
@rate_limit(app, requests=60, window_seconds=60)
def scea_step():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "invalid_input", "message": "Request body must be JSON."}), 400
    triggers = data.get('triggers', None)
    experiences = data.get('experiences', None)
    
    try:
        result = scea_system.step(triggers, experiences)
        return jsonify(result)
    except Exception as e:
        logger.error("SCEA step failed: %s", e)
        return jsonify({"error": "processing_error", "message": str(e)}), 500

@app.route('/api/scea/interact', methods=['POST'])
@rate_limit(app, requests=60, window_seconds=60)
def scea_interact():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "invalid_input", "message": "Request body must be JSON."}), 400
    entity_id = data.get('entity_id', '')
    interaction_type = data.get('interaction_type', '')
    positive = data.get('positive', True)
    
    try:
        result = scea_system.interact_with_entity(entity_id, interaction_type, positive)
        return jsonify(result)
    except Exception as e:
        logger.error("SCEA interaction failed: %s", e)
        return jsonify({"error": "processing_error", "message": str(e)}), 500

# ── Voice output endpoints (single locked voice) ──────────────────

if voice_output_available and tts_manager:
    @app.route('/api/voice-output/tts', methods=['POST'])
    @rate_limit(app, requests=30, window_seconds=60)
    def speak_text():
        """Speak text using the single locked local voice."""
        data = request.get_json(silent=True)
        valid, error, text = validate_text_input(data, max_length=5000)
        if not valid:
            return jsonify({"error": "invalid_input", "message": error}), 400
        language = data.get('language', 'en')
        emotion = data.get('emotion', None)
        save = data.get('save', False)
        try:
            result = tts_manager.speak(text, language=language, emotion=emotion, save=save)
            return jsonify(result.to_dict() if result else {"success": False})
        except Exception as e:
            logger.error("TTS speak failed: %s", e)
            return jsonify({"error": "tts_error", "message": str(e)}), 500

    @app.route('/api/voice-output/tts/stop', methods=['POST'])
    def stop_tts():
        """Stop current voice playback."""
        tts_manager.stop()
        return jsonify({"status": "stopped"})

    @app.route('/api/voice-output/tts/replay', methods=['POST'])
    def replay_tts():
        """Replay the last spoken audio."""
        tts_manager.replay_last()
        return jsonify({"status": "replaying"})

    @app.route('/api/voice-output/status', methods=['GET'])
    def voice_output_status():
        """Return voice lock status, active engine, and activity log."""
        return jsonify({
            **tts_manager.get_voice_status(),
            "activity_log": current_activity_log[-SESSION_ACTIVITY_LOG_LIMIT:] if current_activity_log else [],
        })

    # Removed endpoints:
    #  - /api/voice-output/engines   (no engine selection UI)
    #  - /api/voice-output/voices    (no voice selector / switching)

else:
    @app.route('/api/voice-output/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def voice_output_not_available(path):
        return jsonify({"status": "error", "message": "Voice output system not available"}), 501

# ── Interaction & Dual-Mode Endpoints ──────────────────────────────

@app.route('/api/interaction/message', methods=['POST'])
@rate_limit(app, requests=60, window_seconds=60)
def interaction_message():
    data = request.get_json(silent=True)
    valid, error, text = validate_text_input(data, max_length=5000)
    if not valid:
        return jsonify({"error": "invalid_input", "message": error}), 400
    language = data.get('language', 'en')
    user_mood = data.get('user_mood', None)
    speak_response = data.get('speak_response', False)
    agent_mode = data.get('mode', 'assistant')
    
    current_mode = mode_manager.get_mode_name()
    
    try:
        # Ensure there is an active session
        if not session_manager._current_session:
            session_manager.start_session(mode=current_mode, language=language)
            
        session_id = session_manager._current_session.session_id
        
        if current_mode == "text":
            result = text_handler.process_text(
                text=text,
                language=language,
                user_mood=user_mood,
                speak_response=speak_response,
                session_id=session_id,
                agent_mode=agent_mode,
            )
        elif current_mode == "voice":
            result = voice_handler.process_voice_input(
                transcript=text,
                language=language,
                session_id=session_id
            )
        else:  # hybrid
            result = hybrid_handler.process_text(
                text=text,
                language=language,
                user_mood=user_mood,
                speak_response=speak_response,
                session_id=session_id,
                agent_mode=agent_mode,
            )

        # ── Confidence scoring + accuracy logging ──────────────
        try:
            emotion_result = result.get("emotion_result", {})
            safety_assessment = result.get("safety_assessment", {})
            assistant_msg = result.get("assistant_message", {})
            response_text = assistant_msg.get("response_text", "") if isinstance(assistant_msg, dict) else ""
            response_type = assistant_msg.get("response_type", "") if isinstance(assistant_msg, dict) else ""

            scores = confidence_scorer.score(
                transcript=text,
                emotion_result=emotion_result,
                safety_result=safety_assessment,
                response_text=response_text,
                source="text_mode",
                input_mode=current_mode,
            )

            # Correction detection
            correction = correction_detector.detect(text, language)

            # Log the interaction
            accuracy_logger.log_interaction({
                "input_mode": current_mode,
                "transcript": text,
                "detected_intent": emotion_result.get("dominant_emotion", ""),
                "confidence_scores": scores,
                "selected_backend": "text_mode",
                "response_type": response_type,
                "fallback_used": False,
                "correction": correction if correction.get("is_correction") else None,
                "error_state": None,
                "response_text": response_text,
            })

            # Attach confidence scores to the response
            result["confidence_scores"] = scores
            result["correction_detected"] = correction.get("is_correction", False)
        except Exception as acc_err:
            logger.warning("Accuracy scoring/logging failed: %s", acc_err)

        return jsonify(result)
    except Exception as e:
        logger.error("Interaction message processing failed: %s", e)
        return jsonify({"error": "processing_error", "message": str(e)}), 500

@app.route('/api/interaction/voice/start', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def interaction_voice_start():
    current_mode = mode_manager.get_mode_name()
    if current_mode == "text":
        return jsonify({"status": "error", "message": "Voice input is not enabled in text mode"}), 400
    
    try:
        if not session_manager._current_session:
            session_manager.start_session(mode=current_mode)
            
        if current_mode == "voice":
            result = voice_handler.start_listening()
        else:  # hybrid
            result = hybrid_handler.start_listening()
            
        return jsonify(result)
    except Exception as e:
        logger.error("Voice start failed: %s", e)
        return jsonify({"error": "voice_error", "message": str(e)}), 500

@app.route('/api/interaction/voice/stop', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def interaction_voice_stop():
    current_mode = mode_manager.get_mode_name()
    data = request.get_json(silent=True)
    language = data.get('language', 'en') if data else 'en'
    
    try:
        if current_mode == "voice":
            stop_res = voice_handler.stop_listening()
        elif current_mode == "hybrid":
            stop_res = hybrid_handler.stop_listening()
        else:
            return jsonify({"status": "error", "message": "Voice input is not enabled in text mode"}), 400
            
        transcript = stop_res.get("transcript", "")
        
        if not session_manager._current_session:
            session_manager.start_session(mode=current_mode, language=language)
            
        session_id = session_manager._current_session.session_id
        
        if not transcript:
            return jsonify({
                "status": "no_input",
                "message": "No speech detected. Please try again."
            })
            
        if current_mode == "voice":
            result = voice_handler.process_voice_input(
                transcript=transcript,
                language=language,
                session_id=session_id
            )
        else:  # hybrid
            result = hybrid_handler.process_voice_input(
                transcript=transcript,
                language=language,
                session_id=session_id
            )
            
        return jsonify(result)
    except Exception as e:
        logger.error("Voice stop/processing failed: %s", e)
        return jsonify({"error": "voice_error", "message": str(e)}), 500

@app.route('/api/interaction/voice/status', methods=['GET'])
def interaction_voice_status():
    current_mode = mode_manager.get_mode_name()
    if current_mode == "voice":
        status = voice_handler.get_status()
        status["mode"] = "voice"
    elif current_mode == "hybrid":
        status = hybrid_handler.get_status()
    else:
        status = {
            "is_listening": False,
            "is_speaking": False,
            "audio_level": 0.0,
            "current_transcript": "",
            "push_to_talk": True,
            "continuous_mode": False,
            "stt_available": stt_manager is not None,
            "tts_available": tts_manager is not None,
            "mode": "text"
        }
    return jsonify(status)

@app.route('/api/interaction/voice/level', methods=['GET'])
def interaction_voice_level():
    current_mode = mode_manager.get_mode_name()
    if current_mode in ("voice", "hybrid"):
        level = voice_handler.get_audio_level()
    else:
        level = 0.0
    return jsonify({"audio_level": level})

@app.route('/api/interaction/mode', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def interaction_switch_mode():
    data = request.get_json(silent=True) or {}
    mode_name = data.get('mode', 'hybrid')
    result = mode_manager.switch_mode(mode_name)
    if result.get("success") and session_manager._current_session:
        session_manager.update_mode(mode_name)
    return jsonify(result)

@app.route('/api/interaction/mode', methods=['GET'])
def interaction_get_mode():
    return jsonify(mode_manager.get_status())

@app.route('/api/session/start', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def session_start():
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', mode_manager.get_mode_name())
    language = data.get('language', 'en')
    
    session = session_manager.start_session(mode=mode, language=language)
    return jsonify(session.to_dict())

@app.route('/api/session/end', methods=['POST'])
def session_end():
    if not session_manager._current_session:
        return jsonify({"status": "error", "message": "No active session to end"}), 400
    
    summary = session_manager.end_session()
    return jsonify(summary)

@app.route('/api/session/current', methods=['GET'])
def session_current():
    if not session_manager._current_session:
        return jsonify({"status": "no_active_session"})
    return jsonify(session_manager._current_session.to_dict())

@app.route('/api/session/history', methods=['GET'])
def session_history():
    history = session_manager.get_session_history()
    return jsonify(history)

@app.route('/api/support/calm', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_calm():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    action = support_tools.calm_down(language)
    return jsonify(action.to_dict())

@app.route('/api/support/breathing', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_breathing():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    action = support_tools.breathing_exercise(language)
    return jsonify(action.to_dict())

@app.route('/api/support/journal', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_journal():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    emotion = data.get('emotion', 'neutral')
    action = support_tools.journaling_prompt(language, emotion)
    return jsonify(action.to_dict())

@app.route('/api/support/reflection', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_reflection():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    action = support_tools.reflection_questions(language)
    return jsonify(action.to_dict())

@app.route('/api/support/mood-checkin', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_mood_checkin():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    action = support_tools.mood_checkin(language)
    return jsonify(action.to_dict())

@app.route('/api/support/summary', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def support_summary():
    if not session_manager._current_session:
        return jsonify({"status": "error", "message": "No active session"}), 400
    summary = session_manager.generate_session_summary()
    return jsonify(summary)

@app.route('/api/safety/status', methods=['GET'])
def safety_status():
    if not session_manager._current_session:
        return jsonify({"risk_level": "none", "flags": []})
    
    safety_flags = session_manager._current_session.safety_flags
    # Convert list/dict to dict/list
    risk_level = "none"
    if isinstance(safety_flags, dict):
        risk_level = safety_flags.get("risk_level", "none")
    elif isinstance(safety_flags, list):
        risk_level = "moderate" if safety_flags else "none"
        
    return jsonify({
        "risk_level": risk_level,
        "flags": safety_flags
    })

# ── Voice Conversation Engine API ────────────────────────────────

# SSE client queues
_voice_sse_clients: dict = {}

@app.route('/api/voice/conversation/start', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_conversation_start():
    """Start a voice conversation session."""
    if not conversation_engine:
        return jsonify({"status": "error", "message": "Voice engine not available"}), 503

    result = conversation_engine.start_conversation()
    return jsonify(result)


@app.route('/api/voice/conversation/stop', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_conversation_stop():
    """Stop the voice conversation session."""
    if not conversation_engine:
        return jsonify({"status": "error", "message": "Voice engine not available"}), 503

    result = conversation_engine.stop_conversation()
    return jsonify(result)


@app.route('/api/voice/conversation/interrupt', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_conversation_interrupt():
    """Interrupt current TTS playback."""
    if not conversation_engine:
        return jsonify({"status": "error", "message": "Voice engine not available"}), 503

    result = conversation_engine.interrupt()
    return jsonify(result)


@app.route('/api/voice/conversation/state', methods=['GET'])
def voice_conversation_state():
    """Get current conversation state."""
    if not conversation_engine:
        return jsonify({"state": "unavailable", "message": "Voice engine not active"})

    return jsonify(conversation_engine.get_state())


@app.route('/api/voice/conversation/events')
def voice_conversation_events():
    """SSE stream for real-time voice conversation events."""
    if not conversation_engine:
        return jsonify({"status": "error", "message": "Voice engine not available"}), 503

    q = queue.Queue(maxsize=100)
    client_id = id(q)
    conversation_engine.register_event_queue(client_id, q)

    def generate():
        try:
            while True:
                try:
                    event = q.get(timeout=30)
                    yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                except queue.Empty:
                    # Send keepalive
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            conversation_engine.unregister_event_queue(client_id)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/voice/preferences', methods=['GET'])
def voice_preferences_get():
    """Get voice preferences."""
    if not voice_preferences:
        return jsonify({"status": "error", "message": "Voice preferences not available"}), 503
    return jsonify(voice_preferences.get_all())


@app.route('/api/voice/preferences', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_preferences_set():
    """Update voice preferences."""
    if not voice_preferences:
        return jsonify({"status": "error", "message": "Voice preferences not available"}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid_input", "message": "Request body must be JSON."}), 400

    voice_preferences.update(data)
    voice_preferences.save()

    # Apply to conversation engine if available
    if conversation_engine:
        conversation_engine.update_preferences(data)

    return jsonify({"status": "updated", "preferences": voice_preferences.get_all()})


@app.route('/api/voice/conversation/info', methods=['GET'])
def voice_conversation_info():
    """Get voice engine info for debugging."""
    if not conversation_engine:
        return jsonify({"status": "unavailable"})
    return jsonify(conversation_engine.get_info())


@app.route('/api/voice/tts/pause', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_tts_pause():
    """Pause TTS playback."""
    if tts_manager:
        tts_manager.pause()
        return jsonify({"status": "paused"})
    return jsonify({"status": "error", "message": "TTS not available"}), 503


@app.route('/api/voice/tts/resume', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def voice_tts_resume():
    """Resume TTS playback."""
    if tts_manager:
        tts_manager.resume()
        return jsonify({"status": "resumed"})
    return jsonify({"status": "error", "message": "TTS not available"}), 503


# ── Accuracy System Endpoints ───────────────────────────────────

@app.route('/api/accuracy/summary', methods=['GET'])
def accuracy_summary():
    """Return accuracy summary from AccuracyLogger."""
    try:
        summary = accuracy_logger.get_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error("Accuracy summary failed: %s", e)
        return jsonify({"error": "accuracy_error", "message": str(e)}), 500


@app.route('/api/accuracy/recent', methods=['GET'])
def accuracy_recent():
    """Return recent logged interactions."""
    try:
        n = request.args.get('n', 50, type=int)
        recent = accuracy_logger.get_recent(n=min(n, 200))
        return jsonify({"entries": recent, "count": len(recent)})
    except Exception as e:
        logger.error("Accuracy recent failed: %s", e)
        return jsonify({"error": "accuracy_error", "message": str(e)}), 500


@app.route('/api/accuracy/report', methods=['GET'])
def accuracy_report():
    """Return the last generated accuracy report."""
    try:
        report_path = Path(__file__).parent / "logs" / "accuracy_report.json"
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            return jsonify(report)
        return jsonify({"status": "no_report", "message": "No accuracy report found. Run tests first."})
    except Exception as e:
        logger.error("Accuracy report failed: %s", e)
        return jsonify({"error": "accuracy_error", "message": str(e)}), 500


@app.route('/api/accuracy/correction', methods=['POST'])
@rate_limit(app, requests=30, window_seconds=60)
def accuracy_correction():
    """Submit a user correction for logging."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "invalid_input", "message": "Text is required."}), 400

    try:
        language = data.get('language', 'en')
        detection = correction_detector.detect(text, language)
        if detection.get("is_correction"):
            correction_detector.store_correction(
                text=text,
                detection_result=detection,
                detected_intent=data.get('detected_intent', ''),
                context=data.get('context', ''),
            )
        return jsonify({
            "correction_detected": detection.get("is_correction", False),
            "correction_type": detection.get("correction_type"),
            "matched_phrase": detection.get("original_phrase"),
            "confidence": detection.get("confidence", 0.0),
        })
    except Exception as e:
        logger.error("Correction processing failed: %s", e)
        return jsonify({"error": "correction_error", "message": str(e)}), 500


@app.route('/api/accuracy/evaluate', methods=['POST'])
@rate_limit(app, requests=5, window_seconds=60)
def accuracy_evaluate():
    """Trigger an accuracy evaluation run."""
    try:
        from evaluation.accuracy_evaluator import AccuracyEvaluator
        from evaluation.report_generator import ReportGenerator

        evaluator = AccuracyEvaluator(
            emotion_engine=emotion_engine,
            safety_layer=safety_layer,
            text_handler=text_handler,
        )
        results = evaluator.run_all()

        report_gen = ReportGenerator()
        report_gen.generate_json_report(results)

        return jsonify({
            "status": "complete",
            "overall_accuracy": results.get("overall", 0.0),
            "all_targets_met": results.get("all_targets_met", False),
            "category_results": results.get("category_results", {}),
            "recommendations": report_gen.generate_recommendations(results),
        })
    except Exception as e:
        logger.error("Accuracy evaluation failed: %s", e)
        return jsonify({"error": "evaluation_error", "message": str(e)}), 500


if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    logger.info("Starting Flask app on %s:%d (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)
