"""
VAD Adapter

Adapts the legacy VAD module to the voice agent framework.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from emotion_engine.voice_system.vad import VoiceActivityDetector
except ImportError:
    class VoiceActivityDetector:
        def __init__(self, **kwargs):
            pass
        def is_speech(self, audio) -> bool:
            return False
        def detect_speech_regions(self, audio, **kwargs):
            return []
