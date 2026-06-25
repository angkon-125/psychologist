
import yaml
import os
from typing import Optional, Dict
from pathlib import Path


class AudioConfig:
    DEFAULT_CONFIG = {
        "speech_recognition": {
            "default_engine": "vosk",
            "fallback_engine": "whisper",
            "language": "en",
            "sample_rate": 16000,
            "continuous_listening": False,
            "save_raw_audio": False
        },
        "tts": {
            "default_engine": "piper",
            "fallback_engine": "espeak",
            "voice_id": "default",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 0.9,
            "save_output": True
        },
        "voice_emotion": {
            "enabled": True,
            "fusion_enabled": True,
            "text_weight": 0.55,
            "voice_weight": 0.35,
            "memory_weight": 0.10,
            "confidence_threshold": 0.45
        },
        "privacy": {
            "offline_only": True,
            "allow_cloud_audio": False,
            "allow_voice_cloning": False,
            "store_audio_files": False
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(Path(__file__).parent.parent.parent / "config" / "voice_config.yaml")
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or self.DEFAULT_CONFIG
            except Exception:
                return self.DEFAULT_CONFIG
        else:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG

    def _save_config(self, config: Dict):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")

    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self.config)

    @property
    def stt_default_engine(self) -> str:
        return self.get("speech_recognition.default_engine", "vosk")

    @property
    def tts_default_engine(self) -> str:
        return self.get("tts.default_engine", "piper")

    @property
    def voice_emotion_enabled(self) -> bool:
        return self.get("voice_emotion.enabled", True)

