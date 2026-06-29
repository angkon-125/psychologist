"""
Voice Config — Legacy Compatibility Wrapper

Wraps SingleVoiceConfig to maintain backward compatibility with
existing code that uses the TTSConfig interface.  New code should
use SingleVoiceConfig directly.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("zara.tts.config")


class TTSConfig:
    """
    Backward-compatible config loader.

    Reads from config/single_voice_tts.yaml (preferred) falling back
    to config/tts_config.yaml for legacy setups.  Exposes the same
    .get() / .set() API that existing callers expect.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            base = Path(__file__).parent.parent.parent / "config"
            # Prefer the new single-voice config
            new_path = base / "single_voice_tts.yaml"
            legacy_path = base / "tts_config.yaml"
            self.config_path = new_path if new_path.exists() else legacy_path

        self.config = self._load_default_config()
        self._ensure_config_file()
        self._load_config()

    def _load_default_config(self) -> Dict[str, Any]:
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

    def _ensure_config_file(self):
        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_config(self.config)

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    self.config = self._merge_dicts(self.config, loaded)
        except Exception as e:
            logger.warning("Could not load TTS config: %s", e)

    def _save_config(self, config: Dict[str, Any]):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.warning("Could not save TTS config: %s", e)

    def _merge_dicts(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        merged = base.copy()
        for key, value in overlay.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get(self, key: str, default=None):
        keys = key.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key: str, value):
        keys = key.split('.')
        cfg = self.config
        for k in keys[:-1]:
            if k not in cfg:
                cfg[k] = {}
            cfg = cfg[k]
        cfg[keys[-1]] = value
        self._save_config(self.config)
