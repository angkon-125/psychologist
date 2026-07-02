"""
Session summary handler.
"""

from typing import Dict, Any
from emotion_engine.interaction.support_tools import SupportTools

class SessionSummaryHandler:
    def __init__(self, support_tools: SupportTools):
        self._tools = support_tools

    def get_summary_prompt(self, language: str = "en") -> Dict[str, Any]:
        action = self._tools.session_summary_prompt(language)
        return action.to_dict()
