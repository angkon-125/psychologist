"""
Conversation Engine — Main Orchestrator

Wires together all voice interaction components into a continuous
conversation loop:
  idle -> listening -> pause_analysis -> thinking -> speaking -> listening ...

Supports:
  - Smart pause detection (configurable thresholds)
  - Live partial transcripts
  - Barge-in / interruption during TTS
  - SSE event streaming to frontend
  - Automatic return to listening after response
"""

import threading
import time
import numpy as np
import wave
import json
import queue
import logging
from pathlib import Path
from typing import Dict, Optional, List, Callable
from datetime import datetime

from .conversation_state import ConversationState, ConversationStateMachine
from .pause_detector import SmartPauseDetector, PauseState
from .barge_in import BargeInDetector
from .response_generator import ResponseGenerator
from .voice_preferences import VoicePreferences
from .wake_word import WakeWordDetector

logger = logging.getLogger("zara.voice.conversation_engine")


class ConversationEngine:
    """
    Main voice conversation engine.

    Usage:
        engine = ConversationEngine(
            stt_manager=stt_manager,
            tts_manager=tts_manager,
            response_generator=response_generator,
            preferences=voice_preferences,
        )
        engine.register_event_queue(client_id, queue)
        engine.start_conversation()
    """

    def __init__(
        self,
        stt_manager=None,
        tts_manager=None,
        response_generator: Optional[ResponseGenerator] = None,
        preferences: Optional[VoicePreferences] = None,
        wake_word_detector: Optional[WakeWordDetector] = None,
    ):
        # Core components
        self._stt_manager = stt_manager
        self._tts_manager = tts_manager
        self._response_gen = response_generator
        self._preferences = preferences or VoicePreferences()
        self._wake_word = wake_word_detector or WakeWordDetector()

        # Sub-systems
        self._state_machine = ConversationStateMachine()
        self._pause_detector = SmartPauseDetector(
            thresholds=self._preferences.pause_thresholds
        )
        self._barge_in = BargeInDetector(
            enabled=self._preferences.barge_in_enabled
        )

        # Microphone (from existing voice_system)
        self._microphone = None
        self._init_microphone()

        # Threading
        self._listen_thread: Optional[threading.Thread] = None
        self._speak_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # SSE event queues (client_id -> queue)
        self._event_queues: Dict[int, queue.Queue] = {}
        self._event_lock = threading.Lock()

        # State
        self._current_transcript = ""
        self._partial_transcript = ""
        self._last_response_text = ""
        self._language = self._preferences.language
        self._turn_count = 0
        self._max_turns = 50

        # Whisper engine reference (for direct STT access)
        self._whisper_engine = None
        self._vosk_engine = None
        self._init_stt_engines()

        # Wire state machine callbacks
        self._state_machine.on_any_transition(self._on_state_transition)

    # ── Initialization ─────────────────────────────────────────────

    def _init_microphone(self):
        """Initialize the microphone from existing voice_system."""
        try:
            from ..voice_system.microphone import Microphone
            from ..voice_system.models import AudioInputConfig
            self._microphone = Microphone(AudioInputConfig(
                sample_rate=16000,
                channels=1,
                chunk_size=4096,
            ))
        except Exception as e:
            logger.warning("Microphone not available: %s", e)

    def _init_stt_engines(self):
        """Get references to STT engines for direct access."""
        if self._stt_manager:
            if hasattr(self._stt_manager, 'whisper_engine'):
                self._whisper_engine = self._stt_manager.whisper_engine
            # Check for vosk
            try:
                from ..voice_system.vosk_engine import VoskEngine
                self._vosk_engine = VoskEngine()
                self._vosk_engine.initialize()
            except Exception:
                pass

    # ── Public API ─────────────────────────────────────────────────

    def start_conversation(self) -> Dict:
        """Start the voice conversation (idle -> listening)."""
        if self._state_machine.state != ConversationState.IDLE:
            return {
                "status": "already_active",
                "state": self._state_machine.state_name,
            }

        if not self._microphone:
            return {"status": "error", "message": "Microphone not available"}

        self._stop_event.clear()
        self._current_transcript = ""
        self._partial_transcript = ""
        self._turn_count = 0
        self._pause_detector.reset()

        # Start the conversation loop in a background thread
        self._listen_thread = threading.Thread(
            target=self._conversation_loop,
            daemon=True,
            name="voice-conversation",
        )
        self._listen_thread.start()

        return {
            "status": "started",
            "state": "listening",
        }

    def stop_conversation(self) -> Dict:
        """Stop the voice conversation and return to idle."""
        self._stop_event.set()

        # Stop microphone
        if self._microphone and self._microphone.is_recording:
            self._microphone.stop_recording()

        # Stop any TTS
        if self._tts_manager:
            self._tts_manager.stop()

        # Wait for threads
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
        if self._speak_thread and self._speak_thread.is_alive():
            self._speak_thread.join(timeout=2.0)

        self._state_machine.reset()
        self._emit_event("state_change", {
            "state": "idle",
            "message": "Voice mode ended.",
        })

        return {"status": "stopped", "state": "idle"}

    def interrupt(self) -> Dict:
        """Interrupt current TTS playback and return to listening."""
        if self._tts_manager:
            self._tts_manager.stop()

        if self._state_machine.state == ConversationState.SPEAKING:
            self._state_machine.transition_to(
                ConversationState.LISTENING, reason="user_interrupt"
            )
            self._emit_event("state_change", {
                "state": "listening",
                "message": "Interrupted. I'm listening...",
            })

        return {
            "status": "interrupted",
            "state": self._state_machine.state_name,
        }

    def get_state(self) -> Dict:
        """Return current conversation state and metadata."""
        return {
            "state": self._state_machine.state_name,
            "message": self._state_machine.message,
            "transcript": self._current_transcript,
            "partial_transcript": self._partial_transcript,
            "last_response": self._last_response_text,
            "turn_count": self._turn_count,
            "language": self._language,
            "wake_word_available": self._wake_word.is_available(),
        }

    # ── SSE Event System ───────────────────────────────────────────

    def register_event_queue(self, client_id: int, q: queue.Queue):
        """Register a client's SSE event queue."""
        with self._event_lock:
            self._event_queues[client_id] = q

    def unregister_event_queue(self, client_id: int):
        """Unregister a client's SSE event queue."""
        with self._event_lock:
            self._event_queues.pop(client_id, None)

    def _emit_event(self, event_type: str, data: Dict):
        """Push an event to all registered SSE clients."""
        event = {"type": event_type, "data": data}
        with self._event_lock:
            dead_clients = []
            for cid, q in self._event_queues.items():
                try:
                    q.put_nowait(event)
                except queue.Full:
                    dead_clients.append(cid)
            for cid in dead_clients:
                self._event_queues.pop(cid, None)

    # ── Main Conversation Loop ─────────────────────────────────────

    def _conversation_loop(self):
        """
        Main conversation loop running in a background thread.

        Flow:
          1. Start microphone
          2. Listen + detect speech + smart pause
          3. On FINISHED -> process speech -> generate response
          4. Speak response (with barge-in monitoring)
          5. Return to listening (if auto_return enabled)
        """
        try:
            self._state_machine.transition_to(
                ConversationState.LISTENING, reason="conversation_start"
            )
            self._start_microphone()

            while not self._stop_event.is_set():
                # ── LISTENING PHASE ──────────────────────────────
                transcript = self._listen_until_finished()

                if self._stop_event.is_set():
                    break

                if not transcript or not transcript.strip():
                    # No speech detected, keep listening
                    self._emit_event("partial_transcript", {
                        "text": "",
                        "is_final": False,
                        "message": "No speech detected. Please try again.",
                    })
                    continue

                self._current_transcript = transcript.strip()
                self._turn_count += 1

                # ── THINKING PHASE ───────────────────────────────
                self._state_machine.transition_to(
                    ConversationState.THINKING, reason="speech_complete"
                )

                # Generate response
                response = self._generate_response(self._current_transcript)
                self._last_response_text = response.get("text", "")

                if not self._last_response_text:
                    self._last_response_text = "I'm not sure what to say. Can you tell me more?"

                # ── SPEAKING PHASE ───────────────────────────────
                self._state_machine.transition_to(
                    ConversationState.SPEAKING, reason="response_ready"
                )

                # Emit response to frontend
                self._emit_event("response", {
                    "text": self._last_response_text,
                    "emotion": response.get("emotion", "neutral"),
                    "source": response.get("source", "emotion_engine"),
                })

                # Speak the response (with barge-in monitoring)
                interrupted = self._speak_response(self._last_response_text)

                if self._stop_event.is_set():
                    break

                # ── RETURN TO LISTENING ──────────────────────────
                if interrupted:
                    # User interrupted, go back to listening immediately
                    self._state_machine.transition_to(
                        ConversationState.LISTENING, reason="barge_in"
                    )
                elif self._preferences.get("auto_return_to_listening", True):
                    self._state_machine.transition_to(
                        ConversationState.LISTENING, reason="response_complete"
                    )
                else:
                    self._state_machine.transition_to(
                        ConversationState.IDLE, reason="response_complete"
                    )
                    break

                # Check max turns
                if self._turn_count >= self._max_turns:
                    logger.info("Max conversation turns reached (%d)", self._max_turns)
                    break

        except Exception as e:
            logger.error("Conversation loop error: %s", e)
            self._state_machine.transition_to(
                ConversationState.ERROR, reason=str(e)
            )
            self._emit_event("error", {"message": str(e)})
        finally:
            self._stop_microphone()

    # ── Listening Phase ────────────────────────────────────────────

    def _listen_until_finished(self) -> str:
        """
        Listen to the microphone until the user finishes speaking
        (FINISHED pause state) or stop is requested.

        Returns the final transcript.
        """
        self._pause_detector.reset()
        self._partial_transcript = ""
        audio_buffer: List[np.ndarray] = []
        speech_detected = False

        while not self._stop_event.is_set():
            # Get audio chunk from microphone
            chunk = self._get_audio_chunk(timeout=0.1)
            if chunk is None:
                continue

            # Emit audio level
            level = float(np.sqrt(np.mean(chunk ** 2)))
            self._emit_event("audio_level", {"level": level})

            # Process through pause detector
            pause_state = self._pause_detector.process_frame(chunk)

            if pause_state == PauseState.SPEECH:
                speech_detected = True
                audio_buffer.append(chunk)

                # Try to get partial transcript
                partial = self._get_partial_transcript(chunk)
                if partial:
                    self._partial_transcript = partial
                    self._emit_event("partial_transcript", {
                        "text": partial,
                        "is_final": False,
                    })

            elif pause_state == PauseState.FINISHED:
                if speech_detected:
                    # User finished speaking
                    break
                # No speech yet, keep waiting

            else:
                # SHORT_PAUSE, THINKING_PAUSE, LONG_PAUSE
                if speech_detected:
                    # Emit pause state message
                    msg = self._pause_detector.message
                    if msg:
                        self._emit_event("state_change", {
                            "state": "listening",
                            "message": msg,
                        })

        # Final transcription of accumulated audio
        if audio_buffer:
            full_audio = np.concatenate(audio_buffer)
            final_text = self._transcribe_audio(full_audio)
            return final_text

        return self._partial_transcript

    # ── Speaking Phase ─────────────────────────────────────────────

    def _speak_response(self, text: str) -> bool:
        """
        Speak the response text via TTS while monitoring for barge-in.

        Returns True if the user interrupted (barge-in detected).
        """
        if not self._tts_manager:
            return False

        self._barge_in.reset()

        # Speak in a separate thread so we can monitor barge-in
        speak_done = threading.Event()
        interrupted = threading.Event()

        def _do_speak():
            try:
                self._tts_manager.speak(
                    text,
                    language=self._language,
                    save=True,
                )
            except Exception as e:
                logger.error("TTS speak error: %s", e)
            finally:
                speak_done.set()

        self._speak_thread = threading.Thread(target=_do_speak, daemon=True)
        self._speak_thread.start()

        # Monitor for barge-in while speaking
        while not speak_done.is_set() and not self._stop_event.is_set():
            chunk = self._get_audio_chunk(timeout=0.05)
            if chunk is not None:
                if self._barge_in.process_audio(chunk):
                    # User interrupted!
                    interrupted.set()
                    self._tts_manager.stop()
                    self._emit_event("state_change", {
                        "state": "listening",
                        "message": "Interrupted. I'm listening...",
                    })
                    break

            # Emit playback state
            if self._tts_manager.is_speaking():
                self._emit_event("playback_state", {
                    "state": "speaking",
                })

        # Wait for speak thread to finish
        if not interrupted.is_set():
            speak_done.wait(timeout=5.0)

        return interrupted.is_set()

    # ── Response Generation ────────────────────────────────────────

    def _generate_response(self, transcript: str) -> Dict:
        """Generate a response using the ResponseGenerator."""
        if self._response_gen:
            return self._response_gen.generate(
                transcript=transcript,
                language=self._language,
            )
        # Fallback if no response generator
        return {
            "text": "I heard you. Tell me more.",
            "emotion": "neutral",
            "source": "fallback",
            "confidence": 0.5,
        }

    # ── Audio Helpers ──────────────────────────────────────────────

    def _start_microphone(self):
        """Start the microphone recording."""
        if self._microphone and not self._microphone.is_recording:
            try:
                self._microphone.clear_queue()
                self._microphone.start_recording()
            except Exception as e:
                logger.error("Failed to start microphone: %s", e)

    def _stop_microphone(self):
        """Stop the microphone recording."""
        if self._microphone and self._microphone.is_recording:
            self._microphone.stop_recording()

    def _get_audio_chunk(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """Get an audio chunk from the microphone."""
        if self._microphone:
            return self._microphone.get_audio_chunk(timeout=timeout)
        return None

    def _get_partial_transcript(self, audio_chunk: np.ndarray) -> Optional[str]:
        """Try to get a partial transcript from the audio chunk."""
        # Try Vosk first (supports partial results natively)
        if self._vosk_engine and self._vosk_engine._initialized:
            try:
                result = self._vosk_engine.process_audio(audio_chunk)
                if result.raw_text:
                    return result.raw_text
            except Exception:
                pass
        return None

    def _transcribe_audio(self, audio: np.ndarray) -> str:
        """Transcribe a complete audio buffer."""
        # Try Whisper first (better accuracy)
        if self._whisper_engine and self._whisper_engine._initialized:
            try:
                temp_path = Path(__file__).parent.parent.parent / "logs" / "conv_temp.wav"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                self._save_wav(temp_path, audio, 16000)
                result = self._whisper_engine.transcribe_audio_file(
                    str(temp_path), self._language
                )
                if result.raw_text:
                    return result.raw_text
            except Exception as e:
                logger.warning("Whisper transcription failed: %s", e)

        # Try Vosk
        if self._vosk_engine and self._vosk_engine._initialized:
            try:
                self._vosk_engine.reset()
                result = self._vosk_engine.process_audio(audio, self._language)
                if result.raw_text:
                    return result.raw_text
            except Exception as e:
                logger.warning("Vosk transcription failed: %s", e)

        # Return partial transcript as fallback
        return self._partial_transcript

    @staticmethod
    def _save_wav(path: Path, audio: np.ndarray, sample_rate: int):
        """Save audio array to a WAV file."""
        wav_file = wave.open(str(path), 'wb')
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        audio_int16 = (audio * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())
        wav_file.close()

    # ── State Transition Handler ───────────────────────────────────

    def _on_state_transition(self, old_state: ConversationState, new_state: ConversationState):
        """Called on every state machine transition."""
        self._emit_event("state_change", {
            "state": new_state.value,
            "message": self._state_machine.message,
        })

    # ── Configuration ──────────────────────────────────────────────

    def set_language(self, language: str):
        self._language = language
        if self._stt_manager:
            self._stt_manager.set_language(language)

    def update_preferences(self, prefs: Dict):
        """Update voice preferences and apply to sub-systems."""
        self._preferences.update(prefs)
        self._preferences.save()

        # Apply to sub-systems
        if "pause_thresholds" in prefs:
            self._pause_detector.update_thresholds(prefs["pause_thresholds"])
        if "barge_in_enabled" in prefs:
            self._barge_in.set_enabled(prefs["barge_in_enabled"])
        if "language" in prefs:
            self._language = prefs["language"]

    def get_info(self) -> Dict:
        """Return full engine info for debugging / frontend."""
        return {
            "state": self._state_machine.state_name,
            "turn_count": self._turn_count,
            "language": self._language,
            "pause_thresholds": self._pause_detector.get_thresholds(),
            "barge_in": self._barge_in.get_config(),
            "wake_word": self._wake_word.get_config(),
            "preferences": self._preferences.get_all(),
            "response_generator": self._response_gen.get_info() if self._response_gen else None,
        }
