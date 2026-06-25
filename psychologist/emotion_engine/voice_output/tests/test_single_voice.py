"""
Tests for the single-voice TTS system.

Covers:
  - SingleVoiceConfig loading and defaults
  - VoiceLock locking / unlocking behavior
  - VoiceStyleMapper clamped emotion output
  - TTSManager initialization and safety filter
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


# ── SingleVoiceConfig ────────────────────────────────────────────

class TestSingleVoiceConfig:
    def _make_config(self, tmp_path):
        from emotion_engine.voice_output.single_voice_config import SingleVoiceConfig
        cfg_file = tmp_path / "test_config.yaml"
        return SingleVoiceConfig(config_path=str(cfg_file))

    def test_defaults_loaded(self, tmp_path):
        cfg = self._make_config(tmp_path)
        assert cfg.is_enabled is True
        assert cfg.mode == "single_voice"
        assert cfg.primary_engine == "piper"
        assert cfg.fallback_engine == "espeak"
        assert cfg.backup_engine == "pyttsx3"
        assert cfg.voice_id == "default_local_voice"

    def test_voice_locked_by_default(self, tmp_path):
        cfg = self._make_config(tmp_path)
        assert cfg.is_locked is True
        assert cfg.allow_switching is False

    def test_safety_defaults(self, tmp_path):
        cfg = self._make_config(tmp_path)
        assert cfg.offline_only is True
        assert cfg.allow_cloud_tts is False
        assert cfg.allow_voice_cloning is False

    def test_emotion_style_retrieval(self, tmp_path):
        cfg = self._make_config(tmp_path)
        happy = cfg.get_emotion_style("happy")
        assert happy["speed"] == 1.08
        assert happy["volume"] == 0.95
        # Unknown emotion returns defaults
        unknown = cfg.get_emotion_style("rage")
        assert unknown["speed"] == 1.0

    def test_max_change_limits(self, tmp_path):
        cfg = self._make_config(tmp_path)
        assert cfg.max_speed_change == 0.12
        assert cfg.max_volume_change == 0.15
        assert cfg.max_pitch_change == 0.05


# ── VoiceLock ────────────────────────────────────────────────────

class TestVoiceLock:
    def _make_lock(self):
        from emotion_engine.voice_output.voice_lock import VoiceLock
        return VoiceLock()

    def test_initial_state(self):
        lock = self._make_lock()
        assert lock.is_locked is False  # not locked until .lock() called

    def test_lock(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        assert lock.is_locked is True
        assert lock.voice_id == "test_voice"
        assert lock.engine_name == "piper"

    def test_reject_voice_change_when_locked(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        assert lock.validate_voice_change("other_voice") is False
        assert lock.validate_voice_change("test_voice") is True

    def test_reject_engine_change_when_locked(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        assert lock.validate_voice_change(requested_engine="espeak") is False
        assert lock.validate_voice_change(requested_engine="piper") is True

    def test_developer_mode_allows_change(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        lock.unlock_developer()
        assert lock.is_locked is False
        assert lock.validate_voice_change("any_voice") is True

    def test_re_lock_developer(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        lock.unlock_developer()
        lock.lock_developer()
        assert lock.is_locked is True

    def test_emotion_change_always_allowed(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        assert lock.validate_emotion_change("happy") is True
        assert lock.validate_emotion_change("sad") is True

    def test_status_label(self):
        lock = self._make_lock()
        lock.lock("test_voice", "piper")
        status = lock.get_status()
        assert status["label"] == "Local Voice Locked"
        lock.unlock_developer()
        status = lock.get_status()
        assert status["label"] == "Voice Unlocked"


# ── VoiceStyleMapper ─────────────────────────────────────────────

class TestVoiceStyleMapper:
    def _make_mapper(self, tmp_path):
        from emotion_engine.voice_output.single_voice_config import SingleVoiceConfig
        from emotion_engine.voice_output.voice_style_mapper import VoiceStyleMapper
        cfg = SingleVoiceConfig(config_path=str(tmp_path / "cfg.yaml"))
        return VoiceStyleMapper(cfg)

    def test_calm_is_neutral(self, tmp_path):
        mapper = self._make_mapper(tmp_path)
        style = mapper.get_style("calm")
        assert style.speed_multiplier == 1.0
        assert style.pitch_multiplier == 1.0
        assert style.volume_multiplier == 0.9

    def test_happy_faster_louder(self, tmp_path):
        mapper = self._make_mapper(tmp_path)
        style = mapper.get_style("happy")
        assert style.speed_multiplier > 1.0
        assert style.volume_multiplier > 0.9

    def test_sad_slower_softer(self, tmp_path):
        mapper = self._make_mapper(tmp_path)
        style = mapper.get_style("sad")
        assert style.speed_multiplier < 1.0
        assert style.volume_multiplier < 0.9

    def test_unknown_emotion_returns_neutral(self, tmp_path):
        mapper = self._make_mapper(tmp_path)
        style = mapper.get_style("rage")
        assert style.speed_multiplier == 1.0
        assert style.volume_multiplier == 0.9

    def test_speed_clamped(self, tmp_path):
        mapper = self._make_mapper(tmp_path)
        style = mapper.get_style("happy")
        # max_speed_change is 0.12, so speed must be <= 1.12
        assert style.speed_multiplier <= 1.12
        assert style.speed_multiplier >= 0.88


# ── TTSManager (unit, with mocked engines) ───────────────────────

class TestTTSManager:
    def test_safety_blocks_clone_requests(self):
        from emotion_engine.voice_output.tts_manager import TTSManager
        assert TTSManager._check_safety("please clone my voice") is True
        assert TTSManager._check_safety("impersonate someone") is True
        assert TTSManager._check_safety("upload voice sample for cloning") is True
        assert TTSManager._check_safety("hello how are you") is False

    def test_safety_blocks_celebrity_requests(self):
        from emotion_engine.voice_output.tts_manager import TTSManager
        assert TTSManager._check_safety("make it sound like this celebrity") is True
        assert TTSManager._check_safety("generate speech as a real public figure") is True
