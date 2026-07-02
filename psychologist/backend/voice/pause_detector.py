"""
Smart Pause Detector wrapper.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from emotion_engine.voice_engine.pause_detector import SmartPauseDetector, PauseState
except ImportError:
    class PauseState:
        SPEECH = "speech"
        SHORT_PAUSE = "short_pause"
        THINKING_PAUSE = "thinking_pause"
        LONG_PAUSE = "long_pause"
        FINISHED = "finished"

    class SmartPauseDetector:
        def __init__(self, **kwargs):
            pass
        def process_frame(self, frame_ms: float, audio_level: float) -> str:
            return "speech"
