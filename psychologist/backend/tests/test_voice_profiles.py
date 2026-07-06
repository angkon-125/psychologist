"""
Tests for ZARA Voice Profile System.

Covers:
  - Voice profile resolution (valid, invalid, default fallback)
  - Profile metadata structure
  - Profile speed/volume/pitch values applied to TTS engine
  - pyttsx3 female voice selection does not crash
  - TTS endpoint accepts voice_profile parameter
  - Voice engines endpoint returns profiles
  - Profile override logic
"""

import pytest
from unittest.mock import MagicMock, patch


# ── Voice Profile Module Tests ─────────────────────────────────────────────

class TestVoiceProfiles:
    """Tests for the voice_profiles module."""

    def test_all_profiles_exist(self):
        """All four required profiles are defined."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        expected = {"zara_soft", "zara_cute", "zara_professional", "zara_night"}
        assert set(ZARA_VOICE_PROFILES.keys()) == expected

    def test_profile_metadata_structure(self):
        """Each profile has all required fields."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        required_keys = {"label", "gender", "speed", "pitch", "volume", "emotion", "description"}
        for profile_key, profile in ZARA_VOICE_PROFILES.items():
            for key in required_keys:
                assert key in profile, f"Profile '{profile_key}' missing key '{key}'"

    def test_profile_gender_is_female(self):
        """All ZARA profiles are female."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        for profile_key, profile in ZARA_VOICE_PROFILES.items():
            assert profile["gender"] == "female", f"Profile '{profile_key}' gender is not female"

    def test_profile_speed_in_range(self):
        """All profile speeds are in valid range (0.5 - 2.0)."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        for profile_key, profile in ZARA_VOICE_PROFILES.items():
            speed = profile["speed"]
            assert 0.5 <= speed <= 2.0, f"Profile '{profile_key}' speed {speed} out of range"

    def test_profile_volume_in_range(self):
        """All profile volumes are in valid range (0.0 - 1.0)."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        for profile_key, profile in ZARA_VOICE_PROFILES.items():
            volume = profile["volume"]
            assert 0.0 <= volume <= 1.0, f"Profile '{profile_key}' volume {volume} out of range"

    def test_profile_pitch_in_range(self):
        """All profile pitches are in valid range (0.5 - 2.0)."""
        from backend.voice.voice_profiles import ZARA_VOICE_PROFILES
        for profile_key, profile in ZARA_VOICE_PROFILES.items():
            pitch = profile["pitch"]
            assert 0.5 <= pitch <= 2.0, f"Profile '{profile_key}' pitch {pitch} out of range"

    def test_get_profile_valid(self):
        """get_profile returns correct profile for valid key."""
        from backend.voice.voice_profiles import get_profile
        profile = get_profile("zara_cute")
        assert profile["label"] == "Zara Cute"
        assert profile["speed"] == 1.03
        assert profile["pitch"] == 1.12
        assert profile["volume"] == 0.95

    def test_get_profile_invalid_falls_back_to_default(self):
        """get_profile falls back to default for invalid key."""
        from backend.voice.voice_profiles import get_profile, DEFAULT_VOICE_PROFILE
        profile = get_profile("nonexistent_profile")
        default = get_profile(DEFAULT_VOICE_PROFILE)
        assert profile == default

    def test_get_profile_none_returns_default(self):
        """get_profile returns default when key is None."""
        from backend.voice.voice_profiles import get_profile, DEFAULT_VOICE_PROFILE
        profile = get_profile(None)
        assert profile["label"] == "Zara Soft"  # default is zara_soft

    def test_get_all_profiles(self):
        """get_all_profiles returns all four profiles."""
        from backend.voice.voice_profiles import get_all_profiles
        profiles = get_all_profiles()
        assert len(profiles) == 4
        assert "zara_soft" in profiles
        assert "zara_cute" in profiles
        assert "zara_professional" in profiles
        assert "zara_night" in profiles

    def test_get_profile_keys(self):
        """get_profile_keys returns list of all profile keys."""
        from backend.voice.voice_profiles import get_profile_keys
        keys = get_profile_keys()
        assert len(keys) == 4
        assert "zara_soft" in keys

    def test_resolve_profile_with_overrides_speed(self):
        """User speed override is applied correctly."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_speed=1.5,
        )
        assert profile["speed"] == 1.5

    def test_resolve_profile_with_overrides_volume(self):
        """User volume override is applied correctly."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_night",
            user_volume=0.5,
        )
        assert profile["volume"] == 0.5

    def test_resolve_profile_with_overrides_clamped(self):
        """User overrides are clamped to valid ranges."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_speed=5.0,  # too high
            user_volume=-1.0,  # too low
        )
        assert profile["speed"] == 2.0  # clamped to max
        assert profile["volume"] == 0.0  # clamped to min

    def test_resolve_profile_no_overrides(self):
        """Without overrides, profile values are unchanged."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(profile_key="zara_cute")
        assert profile["speed"] == 1.03
        assert profile["volume"] == 0.95
        assert profile["pitch"] == 1.12

    def test_get_profile_for_mode(self):
        """Mode-to-profile mapping works correctly."""
        from backend.voice.voice_profiles import get_profile_for_mode
        assert get_profile_for_mode("psychologist") == "zara_soft"
        assert get_profile_for_mode("assistant") == "zara_cute"
        assert get_profile_for_mode("coding") == "zara_professional"
        assert get_profile_for_mode("night") == "zara_night"
        assert get_profile_for_mode("unknown_mode") == "zara_soft"  # default

    def test_get_profile_returns_copy(self):
        """get_profile returns a copy, not a reference to the original."""
        from backend.voice.voice_profiles import get_profile, ZARA_VOICE_PROFILES
        profile = get_profile("zara_soft")
        profile["speed"] = 999.0
        # Original should be unchanged
        assert ZARA_VOICE_PROFILES["zara_soft"]["speed"] == 0.92


# ── TTS Engine Profile Integration Tests ────────────────────────────────────

class TestTTSEngineProfileIntegration:
    """Tests for TTS engine with voice profiles."""

    def test_tts_synthesize_with_zara_soft(self):
        """TTS synthesize accepts zara_soft profile without error."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        result = engine.synthesize("Hello", voice_profile="zara_soft")
        # Engine not available, but profile should be in result
        assert result["profile"] == "zara_soft"
        assert result["success"] is False  # engine not available

    def test_tts_synthesize_with_zara_cute(self):
        """TTS synthesize accepts zara_cute profile."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        result = engine.synthesize("Hello", voice_profile="zara_cute")
        assert result["profile"] == "zara_cute"

    def test_tts_synthesize_invalid_profile_falls_back(self):
        """TTS synthesize with invalid profile falls back to default."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = False
        engine._active_engine = "none"
        engine._cache = {}
        result = engine.synthesize("Hello", voice_profile="invalid_profile")
        # Should fall back to default (zara_soft)
        assert result["profile"] == "invalid_profile"  # name is preserved
        assert result["success"] is False

    def test_tts_empty_text_rejected_with_profile(self):
        """TTS empty text is still rejected even with valid profile."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine._tts_manager = None
        engine._available = True
        engine._active_engine = "pyttsx3"
        engine._cache = {}
        result = engine.synthesize("", voice_profile="zara_soft")
        assert result["success"] is False
        assert "Text is empty" in result["errors"][0]
        assert result["profile"] == "zara_soft"

    def test_tts_cache_key_includes_profile(self):
        """Cache key is different for different profiles."""
        from backend.voice.tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        key1 = engine._make_cache_key("Hello", "en", 1.0, "zara_soft")
        key2 = engine._make_cache_key("Hello", "en", 1.0, "zara_cute")
        assert key1 != key2


# ── pyttsx3 Female Voice Selection Tests ─────────────────────────────────────

class TestPyttsx3FemaleVoiceSelection:
    """Tests for pyttsx3 female voice selection logic."""

    def test_select_female_voice_no_voices(self):
        """Returns None when no voices available."""
        from emotion_engine.voice_output.pyttsx3_engine import Pyttsx3Engine
        from emotion_engine.voice_output.models import TTSRequest
        engine = Pyttsx3Engine.__new__(Pyttsx3Engine)
        request = TTSRequest(text="test")
        result = engine._select_female_voice([], request)
        assert result is None

    def test_select_female_voice_finds_zira(self):
        """Selects Microsoft Zira when available."""
        from emotion_engine.voice_output.pyttsx3_engine import Pyttsx3Engine
        from emotion_engine.voice_output.models import TTSRequest
        engine = Pyttsx3Engine.__new__(Pyttsx3Engine)
        mock_voice = MagicMock()
        mock_voice.name = "Microsoft Zira"
        mock_voice.id = "zira_id"
        request = TTSRequest(text="test")
        result = engine._select_female_voice([mock_voice], request)
        assert result == "zira_id"

    def test_select_female_voice_finds_hazel(self):
        """Selects Microsoft Hazel when available."""
        from emotion_engine.voice_output.pyttsx3_engine import Pyttsx3Engine
        from emotion_engine.voice_output.models import TTSRequest
        engine = Pyttsx3Engine.__new__(Pyttsx3Engine)
        mock_voice = MagicMock()
        mock_voice.name = "Microsoft Hazel"
        mock_voice.id = "hazel_id"
        request = TTSRequest(text="test")
        result = engine._select_female_voice([mock_voice], request)
        assert result == "hazel_id"

    def test_select_female_voice_finds_female_tag(self):
        """Selects voice tagged with 'female'."""
        from emotion_engine.voice_output.pyttsx3_engine import Pyttsx3Engine
        from emotion_engine.voice_output.models import TTSRequest
        engine = Pyttsx3Engine.__new__(Pyttsx3Engine)
        mock_voice = MagicMock()
        mock_voice.name = "Some Female Voice"
        mock_voice.id = "female_id"
        request = TTSRequest(text="test")
        result = engine._select_female_voice([mock_voice], request)
        assert result == "female_id"

    def test_select_female_voice_fallback_no_crash(self):
        """Falls back gracefully when no female voice found."""
        from emotion_engine.voice_output.pyttsx3_engine import Pyttsx3Engine
        from emotion_engine.voice_output.models import TTSRequest
        engine = Pyttsx3Engine.__new__(Pyttsx3Engine)
        mock_voice = MagicMock()
        mock_voice.name = "Male Robot Voice"
        mock_voice.id = "robot_id"
        request = TTSRequest(text="test")
        result = engine._select_female_voice([mock_voice], request)
        # Should return None (fallback to default) without crashing
        assert result is None


# ── API Endpoint Profile Tests ──────────────────────────────────────────────

class TestVoiceEndpointProfiles:
    """Tests for voice API endpoints with profile support."""

    def test_voice_engines_endpoint_returns_profiles(self, client):
        """Voice engines endpoint returns profiles dict."""
        response = client.get("/api/voice/engines")
        assert response.status_code == 200
        data = response.get_json()
        assert "profiles" in data
        assert "zara_soft" in data["profiles"]
        assert "zara_cute" in data["profiles"]
        assert "zara_professional" in data["profiles"]
        assert "zara_night" in data["profiles"]

    def test_voice_engines_endpoint_returns_default_profile(self, client):
        """Voice engines endpoint returns default_profile."""
        response = client.get("/api/voice/engines")
        data = response.get_json()
        assert "default_profile" in data
        assert data["default_profile"] == "zara_soft"

    def test_voice_engines_profile_has_metadata(self, client):
        """Each profile in engines response has full metadata."""
        response = client.get("/api/voice/engines")
        data = response.get_json()
        profile = data["profiles"]["zara_soft"]
        assert "label" in profile
        assert "gender" in profile
        assert "speed" in profile
        assert "pitch" in profile
        assert "volume" in profile
        assert "emotion" in profile
        assert "description" in profile

    def test_tts_endpoint_accepts_voice_profile(self, client):
        """TTS endpoint accepts voice_profile parameter."""
        # This will fail with 503 if TTS not available, but should not 400
        response = client.post("/api/voice/tts", json={
            "text": "Hi, I'm Zara.",
            "voice_profile": "zara_cute",
            "language": "en",
        })
        # Should be either 200 (success) or 500/503 (engine unavailable)
        # Should NOT be 400 (bad request) since text is valid
        assert response.status_code in (200, 500, 503)

    def test_tts_endpoint_empty_text_still_rejected(self, client):
        """TTS endpoint still rejects empty text with voice_profile."""
        response = client.post("/api/voice/tts", json={
            "text": "",
            "voice_profile": "zara_soft",
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
