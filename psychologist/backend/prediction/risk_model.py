"""
Risk assessment model for trajectory analysis.
"""

from typing import Dict, Any, List

class RiskModel:
    """Evaluates psychological and systemic risks based on current emotional states."""

    def evaluate_risk(self, current_emotion: str, intensity: float, history: List[Dict]) -> Dict[str, Any]:
        risk_level = "low"
        triggers = []
        
        # Calculate risk level based on intensity and emotions
        if current_emotion in ("sadness", "fear", "anger") and intensity > 0.8:
            risk_level = "high"
            triggers.append(f"High intensity {current_emotion} detected")
        elif current_emotion in ("sadness", "fear", "anger") and intensity > 0.5:
            risk_level = "medium"
            triggers.append(f"Moderate {current_emotion} detected")
            
        # Check emotional instability in history
        if len(history) >= 3:
            recent_intensities = [h.get("intensity", 0.0) for h in history[-3:]]
            if sum(recent_intensities) / 3 > 0.7:
                risk_level = "high"
                triggers.append("Sustained high intensity emotional state")
                
        return {
            "risk_level": risk_level,
            "reasons": triggers,
            "confidence": 0.8
        }
