"""
Ollama Client Re-export / Wrapper

Provides access to the legacy Ollama client or wraps it for our multi-agent architecture.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from emotion_engine.voice_engine.ollama_client import OllamaClient
except ImportError:
    # Minimal fallback in case of import errors
    class OllamaClient:
        def __init__(self, **kwargs):
            self.is_available = False
        def generate(self, **kwargs):
            return None
        def get_info(self):
            return {"available": False}
