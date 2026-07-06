"""TTS Engine — Offline Text-to-Speech API wrapper

Provides a clean API for synthesizing text to audio using the existing
TTS pipeline (Piper → eSpeak → pyttsx3 fallback chain).
Supports ZARA voice profiles (zara_soft, zara_cute, zara_professional, zara_night).

Usage:
    engine = TTSEngine()
    result = engine.synthesize("Hello world", voice_profile="zara_soft")
    # {"success": True, "audio_path": "...", "engine": "piper", ...}
"""

import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("zara.voice.tts_api")

# Cache directory for TTS audio files
_CACHE_DIR = Path(__file__).parent.parent.parent / "audio_outputs"
_MAX_CACHE_SIZE = 50  # Maximum number of cached audio files


class TTSEngine:
    """
    Offline Text-to-Speech engine for the API layer.

    Features:
      - Piper → eSpeak → pyttsx3 fallback chain
      - Female voice preference
      - Response caching for repeated short texts
      - Audio file output for frontend playback
      - Graceful degradation when unavailable
    """

    def __init__(self):
        self._tts_manager = None
        self._cache: Dict[str, str] = {}  # text_hash -> audio_path
        self._available = False
        self._active_engine = "none"
        self._initialize()

    def _initialize(self):
        """Try to initialize the TTS manager."""
        try:
            from emotion_engine.voice_output.tts_manager import TTSManager
            from emotion_engine.voice_output.single_voice_config import SingleVoiceConfig

            config = SingleVoiceConfig()
            self._tts_manager = TTSManager(config)
            self._available = True

            # Determine active engine
            if hasattr(self._tts_manager, "_active_engine_name"):
                self._active_engine = self._tts_manager._active_engine_name or "unknown"

            logger.info("TTS engine ready: %s", self._active_engine)
        except Exception as e:
            logger.warning("TTS engine not available: %s", e)
            self._available = False
            self._active_engine = "none"

    @property
    def is_available(self) -> bool:
        """Whether the TTS engine can synthesize text."""
        return self._available and self._tts_manager is not None

    def synthesize(
        self,
        text: str,
        voice: str = "female",
        language: str = "en",
        speed: float = 1.0,
        use_cache: bool = True,
        voice_profile: Optional[str] = None,
        speaking_style: Optional[str] = None,
        emotion_context: Optional[str] = None,
        normalize: bool = True,
    ) -> Dict[str, Any]:
        """
        Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice: Voice preference ("female", "male", or specific voice ID)
            language: Language code ("en", "bn", "bn_bd")
            speed: Playback speed multiplier (0.5 - 2.0)
            use_cache: Whether to use response cache
            voice_profile: ZARA voice profile key
                ("zara_soft", "zara_cute", "zara_professional", "zara_night")

        Returns:
            Dict with keys: success, audio_path, engine, duration_ms,
            cached, profile, (errors if failed)
        """
        start_time = time.perf_counter()

        # Resolve voice profile
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key=voice_profile,
            user_speed=speed if speed != 1.0 else None,
        )

        # Resolve speaking style
        from backend.voice.speaking_styles import get_style, get_style_for_emotion
        if speaking_style:
            style = get_style(speaking_style)
        elif emotion_context:
            style = get_style(get_style_for_emotion(emotion_context))
        else:
            style = get_style(None)

        # Apply style speed_factor on top of profile speed
        profile_speed = profile["speed"] * style.get("speed_factor", 1.0)
        profile_volume = profile["volume"]
        profile_pitch = profile["pitch"]
        profile_name = voice_profile or "zara_soft"
        style_name = speaking_style or (get_style_for_emotion(emotion_context) if emotion_context else "calm_support")

        # Normalize text for speech
        normalized_text = text
        chunks = []
        if normalize and text and text.strip():
            from backend.voice.text_normalizer import normalize_for_speech, chunk_for_speech
            normalized_text = normalize_for_speech(text, language=language)
            if normalized_text:
                chunks = chunk_for_speech(
                    normalized_text,
                    max_chars=style.get("max_sentence_chars", 150),
                    chunk_mode=style.get("chunk_mode", "sentence"),
                )

        # Validate input
        if not normalized_text or not normalized_text.strip():
            return {
                "success": False,
                "audio_path": None,
                "engine": self._active_engine,
                "duration_ms": 0,
                "cached": False,
                "profile": profile_name,
                "style": style_name,
                "normalized_text": normalized_text,
                "chunks": chunks,
                "errors": ["Text is empty after normalization."],
            }

        if not self.is_available:
            return {
                "success": False,
                "audio_path": None,
                "engine": "none",
                "duration_ms": 0,
                "cached": False,
                "profile": profile_name,
                "style": style_name,
                "normalized_text": normalized_text,
                "chunks": chunks,
                "errors": ["TTS engine not available."],
            }

        # Check cache for repeated short responses
        text_hash = self._make_cache_key(normalized_text, language, profile_speed, profile_name, style_name)
        if use_cache and text_hash in self._cache:
            cached_path = self._cache[text_hash]
            if os.path.isfile(cached_path):
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                logger.debug("TTS cache hit for: %s (profile=%s)", text[:40], profile_name)
                return {
                    "success": True,
                    "audio_path": cached_path,
                    "engine": self._active_engine,
                    "duration_ms": elapsed_ms,
                    "cached": True,
                    "profile": profile_name,
                    "style": style_name,
                    "normalized_text": normalized_text,
                    "chunks": chunks,
                }
            else:
                # Cached file was deleted
                del self._cache[text_hash]

        try:
            from emotion_engine.voice_output.models import TTSRequest

            request = TTSRequest(
                text=normalized_text.strip(),
                language=language,
                voice_id="female" if voice == "female" else None,
                speed=max(0.5, min(2.0, profile_speed)),
                volume=max(0.0, min(1.0, profile_volume)),
                pitch=max(0.5, min(2.0, profile_pitch)),
                save_to_file=True,
            )

            result = self._tts_manager._synthesize_with_fallback(request)

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            if result.success and result.audio_path:
                # Add to cache
                if use_cache:
                    self._manage_cache(text_hash, result.audio_path)

                return {
                    "success": True,
                    "audio_path": result.audio_path,
                    "engine": self._active_engine,
                    "duration_ms": elapsed_ms,
                    "cached": False,
                    "profile": profile_name,
                    "style": style_name,
                    "normalized_text": normalized_text,
                    "chunks": chunks,
                }
            else:
                error_msg = result.error_message if hasattr(result, "error_message") else "Synthesis failed"
                return {
                    "success": False,
                    "audio_path": None,
                    "engine": self._active_engine,
                    "duration_ms": elapsed_ms,
                    "cached": False,
                    "profile": profile_name,
                    "style": style_name,
                    "normalized_text": normalized_text,
                    "chunks": chunks,
                    "errors": [error_msg],
                }

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("TTS synthesis failed: %s", e)
            return {
                "success": False,
                "audio_path": None,
                "engine": self._active_engine,
                "duration_ms": elapsed_ms,
                "cached": False,
                "profile": profile_name,
                "style": style_name,
                "normalized_text": normalized_text,
                "chunks": chunks,
                "errors": [str(e)],
            }

    def _make_cache_key(self, text: str, language: str, speed: float, profile: str = "", style: str = "") -> str:
        """Generate a cache key for the given synthesis parameters."""
        key_str = f"{text.strip().lower()}|{language}|{speed}|{profile}|{style}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _manage_cache(self, key: str, audio_path: str):
        """Add entry to cache and evict old entries if needed."""
        self._cache[key] = audio_path

        # Evict oldest entries if cache is too large
        if len(self._cache) > _MAX_CACHE_SIZE:
            # Remove oldest entries (first inserted)
            keys_to_remove = list(self._cache.keys())[:len(self._cache) - _MAX_CACHE_SIZE]
            for k in keys_to_remove:
                old_path = self._cache.pop(k, None)
                # Optionally delete the old audio file
                if old_path and os.path.isfile(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

    def stop(self):
        """Stop any ongoing TTS playback."""
        if self._tts_manager and hasattr(self._tts_manager, "audio_player"):
            try:
                self._tts_manager.audio_player.stop()
            except Exception:
                pass

    def get_info(self) -> Dict[str, Any]:
        """Return TTS engine status info."""
        return {
            "available": self.is_available,
            "engine": self._active_engine,
            "cache_size": len(self._cache),
            "max_cache_size": _MAX_CACHE_SIZE,
        }
