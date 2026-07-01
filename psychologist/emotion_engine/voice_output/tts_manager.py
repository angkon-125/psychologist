"""
TTS Manager — Single Voice Output Orchestrator

Coordinates the full voice output pipeline:
  1. Validate voice lock
  2. Apply emotion style adjustments
  3. Synthesize via Piper → eSpeak → pyttsx3 fallback chain
  4. Play audio
  5. Save audio (optional)
  6. Update activity stream

All output uses one fixed local voice — no switching, no cloning,
no cloud TTS, no voice uploads.
"""

from typing import Dict, Optional, Callable, List
import logging
from .models import TTSRequest, TTSResult
from .single_voice_config import SingleVoiceConfig
from .voice_style_mapper import VoiceStyleMapper
from .voice_lock import VoiceLock
from .audio_player import AudioPlayer
from .base_tts_engine import BaseTTSEngine
from .piper_engine import PiperEngine
from .espeak_engine import ESpeakEngine
from .pyttsx3_engine import Pyttsx3Engine

logger = logging.getLogger("zara.tts")


class TTSManager:
    """
    Central TTS manager that enforces single-voice output.

    Engine priority:
      1. Piper TTS  (primary)
      2. eSpeak NG  (fallback)
      3. pyttsx3    (backup)
    """

    def __init__(self, config: Optional[SingleVoiceConfig] = None):
        self.config = config or SingleVoiceConfig()
        self.style_mapper = VoiceStyleMapper(self.config)
        self.voice_lock = VoiceLock()
        self.audio_player = AudioPlayer()
        self._last_result: Optional[TTSResult] = None
        self._activity_callback: Optional[Callable[[str], None]] = None
        self._engines: Dict[str, BaseTTSEngine] = {}
        self._active_engine_name: Optional[str] = None
        self._initialized = False
        self._initialize()

    # ── Initialization ────────────────────────────────────────────

    def _initialize(self):
        self._log_activity("Loading local voice")

        # Register engines in the configured priority order
        engine_classes: List[type] = [PiperEngine, ESpeakEngine, Pyttsx3Engine]
        for cls in engine_classes:
            try:
                engine = cls()
                if engine.is_available():
                    engine.initialize()
                    self._engines[engine.name] = engine
                    logger.info("TTS engine ready: %s", engine.name)
            except Exception as e:
                logger.debug("TTS engine skipped (%s): %s", cls.name, e)

        # Determine which engine will be used (priority order from config)
        priority = [
            self.config.primary_engine,
            self.config.fallback_engine,
            self.config.backup_engine,
        ]
        for name in priority:
            if name in self._engines:
                self._active_engine_name = name
                break

        # Lock the voice identity
        self.voice_lock.lock(
            voice_id=self.config.voice_id,
            engine_name=self._active_engine_name or "pyttsx3",
        )
        self._log_activity("Voice locked")
        self._initialized = True

    # ── Activity stream ───────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Core speak method ─────────────────────────────────────────

    def speak(
        self,
        text: str,
        language: str = "en",
        emotion: Optional[str] = None,
        save: bool = False,
    ) -> Optional[TTSResult]:
        """
        Speak the given text using the single locked local voice.

        Args:
            text:     The text to synthesize.
            language: Language code (default "en").
            emotion:  Current emotion name for style adjustment.
            save:     Whether to persist the audio file.

        Returns:
            TTSResult on success, or None if TTS is disabled.
        """
        if not self.config.is_enabled:
            return None

        # Safety: reject voice-cloning / imitation content
        if self._check_safety(text):
            return TTSResult(error_message="Blocked: unsafe voice request")

        # Truncate to configured maximum length
        if len(text) > self.config.max_text_length:
            text = text[: self.config.max_text_length]

        self._log_activity("Preparing speech")

        # Apply emotion style (speed / volume / pacing only)
        speed = self.config.get("voice.speed", 1.0)
        pitch = self.config.get("voice.pitch", 1.0)
        volume = self.config.get("voice.volume", 0.9)

        if emotion:
            self._log_activity("Applying emotion style")
            style = self.style_mapper.get_style(emotion)
            speed = style.speed_multiplier
            pitch = style.pitch_multiplier
            volume = style.volume_multiplier

        self._log_activity("Generating local audio")

        request = TTSRequest(
            text=text,
            language=language,
            voice_id=self.config.voice_id,
            speed=speed,
            pitch=pitch,
            volume=volume,
            emotion_style=emotion,
            save_to_file=save or self.config.save_audio,
        )

        result = self._synthesize_with_fallback(request)

        if result.success:
            self._last_result = result
            if result.audio_path and self.config.auto_play:
                self._log_activity("Playing response")
                self.audio_player.play_wav(result.audio_path)
            self._log_activity("Voice output completed")
        else:
            self._log_activity("Voice output failed")

        return result

    # ── Fallback chain ────────────────────────────────────────────

    def _synthesize_with_fallback(self, request: TTSRequest) -> TTSResult:
        """Try engines in priority order: primary → fallback → backup."""
        engine_order = [
            self.config.primary_engine,
            self.config.fallback_engine,
            self.config.backup_engine,
        ]

        for engine_name in engine_order:
            if engine_name and engine_name in self._engines:
                try:
                    result = self._engines[engine_name].synthesize(request)
                    if result.success:
                        result.engine_name = engine_name
                        return result
                    else:
                        logger.warning("Engine %s failed: %s", engine_name, result.error_message)
                except Exception as e:
                    logger.warning("Engine %s exception: %s", engine_name, e)

        return TTSResult(error_message="No TTS engines available")

    # ── Playback controls ─────────────────────────────────────────

    def stop(self):
        """Stop current playback."""
        self.audio_player.stop()
        for engine in self._engines.values():
            engine.stop()

    def pause(self):
        """Pause current playback."""
        self.audio_player.pause()

    def resume(self):
        """Resume paused playback."""
        self.audio_player.resume()

    def fade_out(self, duration_ms: int = 300):
        """Fade out and stop playback (for barge-in)."""
        self.audio_player.fade_out(duration_ms)

    def set_volume(self, volume: float):
        """Set playback volume (0.0 - 1.0)."""
        self.audio_player.set_volume(volume)

    def set_speed(self, speed: float):
        """Set playback speed (0.5 - 2.0)."""
        self.audio_player.set_speed(speed)

    def get_progress(self) -> float:
        """Get playback progress (0.0 - 1.0)."""
        return self.audio_player.get_progress()

    def replay_last(self):
        """Replay the last spoken audio."""
        if self._last_result and self._last_result.audio_path:
            self._log_activity("Replaying last voice output")
            self.audio_player.play_wav(self._last_result.audio_path)

    def is_speaking(self) -> bool:
        return self.audio_player.is_playing()

    def is_paused(self) -> bool:
        return self.audio_player.is_paused()

    # ── Info queries ──────────────────────────────────────────────

    def get_available_engines(self) -> list:
        return list(self._engines.keys())

    def get_voice_status(self) -> dict:
        """Return current voice lock and config status for UI."""
        return {
            **self.voice_lock.get_status(),
            "active_engine": self._active_engine_name,
            "available_engines": list(self._engines.keys()),
            "tts_enabled": self.config.is_enabled,
            "mode": self.config.mode,
        }

    # ── Safety filter ─────────────────────────────────────────────

    @staticmethod
    def _check_safety(text: str) -> bool:
        """Block requests that attempt voice cloning or imitation."""
        unsafe_keywords = [
            "clone this person's voice",
            "make it sound like this celebrity",
            "copy my friend's voice",
            "use this sample to imitate",
            "generate speech as a real public figure",
            "impersonate",
            "voice clone",
            "clone my voice",
            "upload voice sample",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in unsafe_keywords)
