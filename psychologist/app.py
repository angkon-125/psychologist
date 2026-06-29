import os

from flask import Flask, request, jsonify, send_from_directory
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
                session_id=session_id
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
                session_id=session_id
            )
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

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    logger.info("Starting Flask app on %s:%d (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)
