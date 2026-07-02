"""
Grounding exercises wrapper.
"""

from typing import Dict, Any
from emotion_engine.interaction.support_tools import SupportTools

class GroundingHandler:
    def __init__(self, support_tools: SupportTools):
        self._tools = support_tools

    def get_exercise(self, language: str = "en") -> Dict[str, Any]:
        action = self._tools.grounding_exercise(language)
        return action.to_dict()
