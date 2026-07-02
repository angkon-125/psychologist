"""
Journaling prompts handler.
"""

from typing import Dict, Any, Optional
from emotion_engine.interaction.support_tools import SupportTools

class JournalingHandler:
    def __init__(self, support_tools: SupportTools):
        self._tools = support_tools

    def get_prompt(self, language: str = "en", emotion: Optional[str] = None) -> Dict[str, Any]:
        action = self._tools.journaling_prompt(language, emotion)
        return action.to_dict()
