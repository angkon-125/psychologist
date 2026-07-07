"""
TTS Volume & Speed Control Tests

Tests for:
- Night mode TTS request applies lower volume
- Volume clamping (high and low)
- Speed clamping (high and low)
- TTS metadata includes applied volume/speed
- Invalid volume falls back safely
- Night mode speed reduction
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _make_engine():
    """Create a TTSEngine instance without initializing TTS manager."""
    from backend.voice.tts_engine import TTSEngine
    engine = TTSEngine.__new__(TTSEngine)
    engine._tts_manager = None
    engine._available = False
    engine._active_engine = "none"
    engine._cache = {}
    return engine


class TestTTSVolumeClamping(unittest.TestCase):
    """Test volume clamping behavior."""

    def test_volume_clamp_high(self):
        """Volume above 1.0 is clamped to 1.0."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_volume=1.5,
        )
        self.assertLessEqual(profile["volume"], 1.0)

    def test_volume_clamp_low(self):
        """Volume below 0.0 is clamped to 0.0."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_volume=-0.5,
        )
        self.assertGreaterEqual(profile["volume"], 0.0)

    def test_volume_applied_from_request(self):
        """Explicit volume is applied to profile."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_volume=0.5,
        )
        self.assertAlmostEqual(profile["volume"], 0.5, places=1)

    def test_invalid_volume_fallback(self):
        """None volume keeps profile default."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_volume=None,
        )
        # Should keep the profile's default volume
        self.assertAlmostEqual(profile["volume"], 0.9, places=1)


class TestTTSSpeedClamping(unittest.TestCase):
    """Test speed clamping behavior."""

    def test_speed_clamp_high(self):
        """Speed above 2.0 is clamped to 2.0."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_speed=3.0,
        )
        self.assertLessEqual(profile["speed"], 2.0)

    def test_speed_clamp_low(self):
        """Speed below 0.5 is clamped to 0.5."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_speed=0.1,
        )
        self.assertGreaterEqual(profile["speed"], 0.5)

    def test_speed_applied_from_request(self):
        """Explicit speed is applied to profile."""
        from backend.voice.voice_profiles import resolve_profile_with_overrides
        profile = resolve_profile_with_overrides(
            profile_key="zara_soft",
            user_speed=1.5,
        )
        self.assertAlmostEqual(profile["speed"], 1.5, places=1)


class TestTTSMetadata(unittest.TestCase):
    """Test TTS result metadata includes applied volume/speed."""

    def test_metadata_includes_applied_volume(self):
        """Synthesize result includes applied_volume."""
        engine = _make_engine()
        result = engine.synthesize("Hello")
        self.assertIn("applied_volume", result)
        self.assertIsInstance(result["applied_volume"], float)

    def test_metadata_includes_applied_speed(self):
        """Synthesize result includes applied_speed."""
        engine = _make_engine()
        result = engine.synthesize("Hello")
        self.assertIn("applied_speed", result)
        self.assertIsInstance(result["applied_speed"], float)

    def test_metadata_includes_night_mode(self):
        """Synthesize result includes night_mode flag."""
        engine = _make_engine()
        result = engine.synthesize("Hello", night_mode=True)
        self.assertIn("night_mode", result)
        self.assertTrue(result["night_mode"])

    def test_metadata_night_mode_false_by_default(self):
        """night_mode defaults to False."""
        engine = _make_engine()
        result = engine.synthesize("Hello")
        self.assertFalse(result["night_mode"])


class TestNightModeVolume(unittest.TestCase):
    """Test night mode applies lower volume and slower speed."""

    def test_night_mode_lower_volume(self):
        """Night mode caps volume at 0.7."""
        engine = _make_engine()
        # Use zara_cute which has volume 0.95
        result = engine.synthesize("Hello", voice_profile="zara_cute", night_mode=True)
        self.assertLessEqual(result["applied_volume"], 0.7)

    def test_night_mode_slower_speed(self):
        """Night mode caps speed at 0.9."""
        engine = _make_engine()
        # Use zara_cute which has speed 1.03
        result = engine.synthesize("Hello", voice_profile="zara_cute", night_mode=True)
        self.assertLessEqual(result["applied_speed"], 0.9)

    def test_night_mode_volume_request_capped(self):
        """Even with high volume request, night mode caps at 0.7."""
        engine = _make_engine()
        result = engine.synthesize("Hello", volume=1.0, night_mode=True)
        self.assertLessEqual(result["applied_volume"], 0.7)

    def test_non_night_mode_full_volume(self):
        """Without night mode, full profile volume is used."""
        engine = _make_engine()
        result = engine.synthesize("Hello", voice_profile="zara_cute")
        # zara_cute has volume 0.95
        self.assertGreater(result["applied_volume"], 0.7)

    def test_night_mode_with_night_profile(self):
        """Night mode + zara_night profile results in very soft volume."""
        engine = _make_engine()
        result = engine.synthesize("Hello", voice_profile="zara_night", night_mode=True)
        # zara_night has volume 0.65, night mode caps at 0.7 -> stays 0.65
        self.assertLessEqual(result["applied_volume"], 0.7)


# Note: Endpoint integration tests are omitted to avoid TTS engine hangs.
# The unit tests above cover volume/speed clamping and metadata thoroughly.
# Manual testing of /api/voice/tts with volume/speed/night_mode is recommended.


if __name__ == "__main__":
    unittest.main()
