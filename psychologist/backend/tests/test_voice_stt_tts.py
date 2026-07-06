"""
Tests for backend STT and TTS engines and API endpoints.

Covers:
  - STT engine initialization and availability
  - STT graceful response when unavailable
  - STT missing file rejection
  - TTS engine initialization and availability
  - TTS empty text rejection
  - TTS graceful response when unavailable
  - Temp audio cleanup
  - Voice engines info endpoint
"""

import os
import pytest
from unittest.mock import patch, MagicMock


# ── STT Engine Tests ──────────────────────────────────────────────────────

class TestSTTEngine:
    """Tests for the STT engine module."""

    def test_stt_engine_init_without_faster_whisper(self):
        """STT engine gracefully handles missing faster-whisper."""
        with patch.dict("sys.modules", {"faster_whisper": None}):
            from backend.voice.stt_engine import STTEngine
            engine = STTEngine()
            assert engine.is_available is False

    def test_stt_engine_info_unavailable(self):
        """STT engine info returns correct status when unavailable."""
        from backend.voice.stt_engine import STTEngine
        engine = STTEngine.__new__(STTEngine)
        engine._model = None
        engine._available = False
        engine._model_size = "tiny"
        info = engine.get_info()
        assert info["available"] is False
        assert info["engine"] == "none"
        assert "tiny" == info["model"]

    def test_stt_transcribe_unavailable(self):
        """STT transcribe returns graceful error when engine unavailable."""
        from backend.voice.stt_engine import STTEngine
        engine = STTEngine.__new__(STTEngine)
        engine._model = None
        engine._available = False
        result = engine.transcribe("nonexistent.wav")
        assert result["success"] is False
        assert result["transcript"] == ""
        assert result["engine"] == "none"
        assert len(result["errors"]) > 0

    def test_stt_transcribe_missing_file(self):
        """STT transcribe returns error for missing audio file."""
        from backend.voice.stt_engine import STTEngine
        engine = STTEngine.__new__(STTEngine)
        engine._model = MagicMock()
        engine._available = True
        result = engine.transcribe("/nonexistent/path/audio.wav")
        assert result["success"] is False
        assert "Audio file not found" in result["errors"][0]

    def test_stt_transcribe_empty_path(self):
        """STT transcribe returns error for empty path."""
        from backend.voice.stt_engine import STTEngine
        engine = STTEngine.__new__(STTEngine)
        engine._model = MagicMock()
        engine._available = True
        result = engine.transcribe("")
        assert result["success"] is False

    def test_cleanup_audio_file(self):
        """cleanup_audio_file removes existing file."""
        import tempfile
        from backend.voice.stt_engine import cleanup_audio_file
        # Create a temp file
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        assert os.path.isfile(path)
        # Clean it up
        result = cleanup_audio_file(path)
        assert result is True
        assert not os.path.isfile(path)

    def test_cleanup_audio_nonexistent(self):
        """cleanup_audio_file handles nonexistent file gracefully."""
        from backend.voice.stt_engine import cleanup_audio_file
        result = cleanup_audio_file("/nonexistent/path/audio.wav")
        assert result is False

    def test_cleanup_audio_empty_path(self):
        """cleanup_audio_file handles empty path."""
        from backend.voice.stt_engine import cleanup_audio_file
        result = cleanup_audio_file("")
        assert result is False


# ── TTS Engine Tests ──────────────────────────────────────────────────────

class TestTTSEngine:
    """Tests for the TTS engine module."""

    def test_tts_engine_init_without_deps(self):
        """TTS engine gracefully handles missing dependencies."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        assert engine.is_available is False

    def test_tts_synthesize_empty_text(self):
        """TTS rejects empty text."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = True  # pretend available
        engine._active_engine = "pyttsx3"
        engine._cache = {}
        result = engine.synthesize("")
        assert result["success"] is False
        assert "Text is empty" in result["errors"][0]

    def test_tts_synthesize_whitespace_text(self):
        """TTS rejects whitespace-only text."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = True
        engine._active_engine = "pyttsx3"
        engine._cache = {}
        result = engine.synthesize("   ")
        assert result["success"] is False

    def test_tts_synthesize_unavailable(self):
        """TTS returns graceful error when engine unavailable."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        result = engine.synthesize("Hello world")
        assert result["success"] is False
        assert "TTS engine not available" in result["errors"][0]

    def test_tts_cache_key_generation(self):
        """TTS cache key is deterministic."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        key1 = engine._make_cache_key("Hello", "en", 1.0)
        key2 = engine._make_cache_key("Hello", "en", 1.0)
        key3 = engine._make_cache_key("World", "en", 1.0)
        assert key1 == key2
        assert key1 != key3

    def test_tts_cache_management(self):
        """TTS cache eviction works correctly."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._cache = {}
        # Add entries
        for i in range(55):
            engine._manage_cache(f"key_{i}", f"/tmp/audio_{i}.wav")
        # Cache should be trimmed to max size
        assert len(engine._cache) <= 50

    def test_tts_engine_info(self):
        """TTS engine info returns correct structure."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        info = engine.get_info()
        assert info["available"] is False
        assert info["engine"] == "none"
        assert info["cache_size"] == 0


# ── API Endpoint Tests ────────────────────────────────────────────────────

class TestVoiceEndpoints:
    """Tests for the voice API endpoints."""

    def test_stt_endpoint_no_file(self, client):
        """STT endpoint returns 400 when no file uploaded."""
        response = client.post("/api/voice/stt")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "No audio file" in data["errors"][0]

    def test_tts_endpoint_empty_text(self, client):
        """TTS endpoint returns 400 for empty text."""
        response = client.post("/api/voice/tts", json={"text": ""})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_tts_endpoint_missing_text(self, client):
        """TTS endpoint returns 400 when text field missing."""
        response = client.post("/api/voice/tts", json={})
        assert response.status_code == 400

    def test_voice_engines_endpoint(self, client):
        """Voice engines endpoint returns STT and TTS status."""
        response = client.get("/api/voice/engines")
        assert response.status_code == 200
        data = response.get_json()
        assert "stt" in data
        assert "tts" in data
        assert "available" in data["stt"]
        assert "available" in data["tts"]
        assert "engine" in data["stt"]
