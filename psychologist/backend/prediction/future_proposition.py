"""
Future proposition generation.
"""

from typing import List, Dict, Any

class FuturePropositionGenerator:
    """Generates future check-ins and recommendations based on current trajectory."""

    def generate_propositions(self, dominant_emotion: str, risk_level: str) -> List[Dict[str, Any]]:
        propositions = []
        
        if dominant_emotion == "sadness":
            propositions.append({
                "action": "Gently check mood trajectory tomorrow morning",
                "reason": "Risk of lingering sadness",
                "recommended_preparation": "Suggest journaling before sleep"
            })
        elif dominant_emotion == "anger":
            propositions.append({
                "action": "Suggest structured breathing exercise in 15 minutes",
                "reason": "Need emotional cool-down interval",
                "recommended_preparation": "Keep breathing instructions ready"
            })
        else:
            propositions.append({
                "action": "Routine check-in in 24 hours",
                "reason": "Normal operational follow-up",
                "recommended_preparation": "None required"
            })
            
        return propositions
