"""
EmotionEngine Adapter

Adapts the existing monolithic EmotionEngine to the BaseAgent structure
for the LLM Agent's fallback mechanism.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root is in sys.path
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from emotion_engine.emotion_engine import EmotionEngine

class EmotionEngineAdapter:
    """
    Adapter pattern to connect the legacy EmotionEngine to our LLM Agent flow.
    """

    def __init__(self):
        self.engine = EmotionEngine()

    def process(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Process the user text through legacy EmotionEngine.
        Returns a dictionary containing emotional state and generated response.
        """
        result = self.engine.process_input(text)
        return {
            "response": result.get("response", ""),
            "dominant_emotion": result.get("dominant_emotion", "neutral"),
            "confidence": result.get("emotional_state", {}).get("intensity", 0.5),
            "state": result.get("emotional_state", {})
        }
