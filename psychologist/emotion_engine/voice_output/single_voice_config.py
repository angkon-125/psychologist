"""
Single Voice Configuration Module

Loads and enforces the single-voice TTS configuration.
All voice output must pass through this config to ensure
only one fixed local voice is ever used.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class SingleVoiceConfig:
    """Configuration enforcing a single locked local voice for all TTS output."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = (
                Path(__file__).parent.parent.parent / "config" / "single_voice_tts.yaml"
            )
        self._config: Dict[str, Any] = {}
        self._locked = False
        self._load_config()

    def _load_config(self):
        """Load configuration from the single_voice_tts.yaml file."""
        defaults = self._get_defaults()

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                self._config = self._merge(defaults, loaded)
            except Exception as e:
                print(f"Warning: Could not load single voice config: {e}")
                self._config = defaults
        else:
            self._config = defaults
            # Write defaults to disk so the file always exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(defaults, f, allow_unicode=True,
                              default_flow_style=False, sort_keys=False)
            except Exception as e:
                print(f"Warning: Could not write default config: {e}")

    @staticmethod
    def _get_defaults() -> Dict[str, Any]:
        return {
            "tts": {
                "enabled": True,
                "mode": "single_voice",
                "primary_engine": "piper",
                "fallback_engine": "espeak",
                "backup_engine": "pyttsx3",
                "auto_play": True,
                "save_audio": True,
                "output_directory": "audio_outputs",
                "max_text_length": 1000,
            },
            "single_voice": {
                "voice_id": "default_local_voice",
                "voice_model_path": "models/tts/default_voice.onnx",
                "voice_config_path": "models/tts/default_voice.onnx.json",
                "language": "en",
                "locked": True,
                "allow_switching": False,
            },
            "voice": {
                "mode": "single_voice",
                "voice_name": "default_local_voice",
                "language": "en",
                "engine": "piper",
                "allow_voice_switching": False,
                "allow_voice_cloning": False,
                "allow_online_tts": False,
                "speed": 1.0,
                "pitch": 1.0,
                "volume": 0.9,
            },
            "style": {
                "emotion_style_enabled": True,
                "max_speed_change": 0.12,
                "max_volume_change": 0.15,
                "max_pitch_change": 0.05,
                "calm": {"speed": 1.0, "pitch": 1.0, "volume": 0.9, "pause": 1.0},
                "happy": {"speed": 1.08, "pitch": 1.03, "volume": 0.95, "pause": 0.9},
                "sad": {"speed": 0.88, "pitch": 0.97, "volume": 0.75, "pause": 1.15},
                "supportive": {"speed": 0.90, "pitch": 0.98, "volume": 0.82, "pause": 1.1},
                "serious": {"speed": 0.92, "pitch": 0.98, "volume": 0.88, "pause": 1.05},
            },
            "safety": {
                "offline_only": True,
                "allow_cloud_tts": False,
                "allow_voice_cloning": False,
                "allow_voice_imitation": False,
                "allow_uploaded_voice_training": False,
            },
        }

    def _merge(self, base: Dict, overlay: Dict) -> Dict:
        merged = base.copy()
        for key, value in overlay.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    # ── Public API ────────────────────────────────────────────────

    def get(self, dotted_key: str, default=None):
        """Retrieve a config value by dotted key path (e.g. 'tts.enabled')."""
        keys = dotted_key.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    @property
    def is_enabled(self) -> bool:
        return self.get("tts.enabled", True)

    @property
    def mode(self) -> str:
        return self.get("tts.mode", "single_voice")

    @property
    def primary_engine(self) -> str:
        return self.get("tts.primary_engine", "piper")

    @property
    def fallback_engine(self) -> str:
        return self.get("tts.fallback_engine", "espeak")

    @property
    def backup_engine(self) -> str:
        return self.get("tts.backup_engine", "pyttsx3")

    @property
    def voice_id(self) -> str:
        return self.get("single_voice.voice_id", "default_local_voice")

    @property
    def voice_model_path(self) -> str:
        return self.get("single_voice.voice_model_path", "models/tts/default_voice.onnx")

    @property
    def voice_config_path(self) -> str:
        return self.get("single_voice.voice_config_path", "models/tts/default_voice.onnx.json")

    @property
    def language(self) -> str:
        return self.get("single_voice.language", "en")

    @property
    def is_locked(self) -> bool:
        return self.get("single_voice.locked", True)

    @property
    def allow_switching(self) -> bool:
        return self.get("single_voice.allow_switching", False)

    @property
    def auto_play(self) -> bool:
        return self.get("tts.auto_play", True)

    @property
    def save_audio(self) -> bool:
        return self.get("tts.save_audio", True)

    @property
    def output_directory(self) -> str:
        return self.get("tts.output_directory", "audio_outputs")

    @property
    def max_text_length(self) -> int:
        return self.get("tts.max_text_length", 1000)

    @property
    def emotion_style_enabled(self) -> bool:
        return self.get("style.emotion_style_enabled", True)

    @property
    def max_speed_change(self) -> float:
        return self.get("style.max_speed_change", 0.12)

    @property
    def max_volume_change(self) -> float:
        return self.get("style.max_volume_change", 0.15)

    @property
    def max_pitch_change(self) -> float:
        return self.get("style.max_pitch_change", 0.05)

    @property
    def offline_only(self) -> bool:
        return self.get("safety.offline_only", True)

    @property
    def allow_cloud_tts(self) -> bool:
        return self.get("safety.allow_cloud_tts", False)

    @property
    def allow_voice_cloning(self) -> bool:
        return self.get("safety.allow_voice_cloning", False)

    def get_emotion_style(self, emotion: str) -> Dict[str, float]:
        """Return style params for a given emotion, with clamped deltas."""
        defaults = {"speed": 1.0, "pitch": 1.0, "volume": 0.9, "pause": 1.0}
        style = self.get(f"style.{emotion}", defaults)
        if not isinstance(style, dict):
            return defaults
        return {
            "speed": style.get("speed", 1.0),
            "pitch": style.get("pitch", 1.0),
            "volume": style.get("volume", 0.9),
            "pause": style.get("pause", 1.0),
        }
