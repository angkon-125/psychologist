"""
STT Engine — Offline Speech-to-Text using faster-whisper

Provides a clean API for transcribing audio files using faster-whisper
with graceful fallback when the library is unavailable.

Usage:
    engine = STTEngine()
    result = engine.transcribe("path/to/audio.wav")
    # {"success": True, "transcript": "...", "confidence": 0.92, ...}
"""

import os
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("zara.voice.stt")

# Timeout for transcription (seconds)
_TRANSCRIBE_TIMEOUT = 30


class STTEngine:
    """
    Offline Speech-to-Text engine using faster-whisper.

    Features:
      - faster-whisper transcription with model auto-detection
      - English and Bangla support (model-dependent)
      - Confidence estimation from segment scores
      - Temporary file cleanup
      - Timeout protection
      - Graceful degradation when unavailable
    """

    # Default model size — tiny for speed, base for accuracy
    DEFAULT_MODEL = "tiny"

    # Supported language codes
    SUPPORTED_LANGUAGES = {"en", "bn", "bn_bd"}

    def __init__(self, model_size: Optional[str] = None):
        self._model_size = model_size or self.DEFAULT_MODEL
        self._model = None
        self._available = False
        self._initialize()

    def _initialize(self):
        """Attempt to load faster-whisper model."""
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
            )
            self._available = True
            logger.info("STT engine ready: faster-whisper (%s)", self._model_size)
        except ImportError:
            logger.warning("faster-whisper not installed. STT engine unavailable.")
            self._available = False
        except Exception as e:
            logger.warning("STT model load failed: %s", e)
            self._available = False

    @property
    def is_available(self) -> bool:
        """Whether the STT engine is ready to transcribe."""
        return self._available and self._model is not None

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        timeout: int = _TRANSCRIBE_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file (wav, webm, mp3, etc.)
            language: Optional language hint ("en", "bn", "bn_bd")
            timeout: Maximum seconds for transcription

        Returns:
            Dict with keys: success, transcript, language, confidence,
            duration_ms, engine, (errors if failed)
        """
        start_time = time.perf_counter()

        if not self.is_available:
            return {
                "success": False,
                "transcript": "",
                "language": language or "en",
                "confidence": 0.0,
                "duration_ms": 0,
                "engine": "none",
                "errors": ["STT engine not available. Install faster-whisper."],
            }

        if not audio_path or not os.path.isfile(audio_path):
            return {
                "success": False,
                "transcript": "",
                "language": language or "en",
                "confidence": 0.0,
                "duration_ms": 0,
                "engine": "faster-whisper",
                "errors": ["Audio file not found."],
            }

        # Normalize language code
        lang_code = language
        if lang_code == "bn_bd":
            lang_code = "bn"

        try:
            # Run transcription with timeout protection
            import signal

            class TimeoutError(Exception):
                pass

            def _timeout_handler(signum, frame):
                raise TimeoutError("Transcription timed out")

            # Set timeout (only works on main thread on Unix)
            old_handler = None
            use_signal = hasattr(signal, "SIGALRM")
            if use_signal:
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(timeout)

            try:
                segments, info = self._model.transcribe(
                    audio_path,
                    language=lang_code if lang_code else None,
                    beam_size=5,
                    vad_filter=True,
                )

                transcript_parts = []
                confidence_scores = []
                for segment in segments:
                    transcript_parts.append(segment.text.strip())
                    if hasattr(segment, "avg_logprob") and segment.avg_logprob is not None:
                        # Convert log probability to 0-1 confidence
                        import math
                        conf = math.exp(segment.avg_logprob)
                        confidence_scores.append(max(0.0, min(1.0, conf)))

                transcript = " ".join(transcript_parts)
                avg_confidence = (
                    sum(confidence_scores) / len(confidence_scores)
                    if confidence_scores
                    else 0.5
                )

                elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                return {
                    "success": True,
                    "transcript": transcript,
                    "language": info.language if hasattr(info, "language") else (language or "en"),
                    "confidence": round(avg_confidence, 3),
                    "duration_ms": elapsed_ms,
                    "engine": "faster-whisper",
                }

            finally:
                if use_signal:
                    signal.alarm(0)
                    if old_handler is not None:
                        signal.signal(signal.SIGALRM, old_handler)

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("STT transcription failed: %s", e)
            return {
                "success": False,
                "transcript": "",
                "language": language or "en",
                "confidence": 0.0,
                "duration_ms": elapsed_ms,
                "engine": "faster-whisper",
                "errors": [str(e)],
            }

    def get_info(self) -> Dict[str, Any]:
        """Return STT engine status info."""
        return {
            "available": self.is_available,
            "engine": "faster-whisper" if self.is_available else "none",
            "model": self._model_size,
            "supported_languages": list(self.SUPPORTED_LANGUAGES),
        }


def cleanup_audio_file(path: str) -> bool:
    """
    Safely delete a temporary audio file.

    Args:
        path: Path to the audio file

    Returns:
        True if deleted, False otherwise
    """
    try:
        if path and os.path.isfile(path):
            os.remove(path)
            logger.debug("Cleaned up audio file: %s", path)
            return True
    except OSError as e:
        logger.warning("Failed to clean up audio file %s: %s", path, e)
    return False
