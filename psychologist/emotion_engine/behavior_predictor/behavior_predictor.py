from ..models import EmotionalState, PersonalityTraits, ConversationContext
from ..emotional_memory import EmotionalMemory
from typing import Dict, List, Tuple
import math


class BehaviorPredictor:
    def __init__(self):
        self.escalation_patterns = {
            'anger': ['frustration', 'anger', 'rage'],
            'fear': ['anxiety', 'fear', 'panic'],
            'sadness': ['sadness', 'loneliness', 'depression'],
            'stress': ['stress', 'anxiety', 'burnout']
        }

    def predict_emotional_escalation(self, current_state: EmotionalState, history: List[EmotionalState]) -> Dict:
        if len(history) < 3:
            return {'risk': 0.0, 'likely_next': 'stable', 'timeframe': 'unknown'}
        
        recent = history[-3:]
        risk_scores = {}
        
        for emotion in ['anger', 'fear', 'sadness', 'stress']:
            values = []
            for state in recent:
                if emotion in state.primary_emotions:
                    values.append(state.primary_emotions[emotion])
                elif emotion in state.advanced_emotions:
                    values.append(state.advanced_emotions[emotion])
                else:
                    values.append(0.0)
            
            if len(values) >= 2:
                trend = values[-1] - values[0]
                risk_scores[emotion] = trend
        
        max_risk = max(risk_scores.values()) if risk_scores else 0.0
        risk = max(0.0, min(1.0, (max_risk + 0.5)))
        
        likely_emotion = max(risk_scores.items(), key=lambda x: x[1])[0] if risk_scores else None
        
        timeframe = 'immediate' if risk > 0.7 else 'soon' if risk > 0.4 else 'low'
        
        return {
            'risk': risk,
            'likely_emotion': likely_emotion,
            'timeframe': timeframe,
            'recommended_action': 'intervene' if risk > 0.6 else 'monitor'
        }

    def predict_emotional_recovery(self, current_state: EmotionalState, personality: PersonalityTraits) -> Dict:
        recovery_factors = {
            'resilience': (1 - personality.neuroticism) * 0.4 + personality.conscientiousness * 0.3 + personality.optimism * 0.3,
            'social_support': personality.agreeableness * 0.5 + personality.extraversion * 0.5,
            'current_intensity': current_state.intensity
        }
        
        recovery_score = recovery_factors['resilience'] * 0.6 + recovery_factors['social_support'] * 0.4
        recovery_score = recovery_score * (1 - recovery_factors['current_intensity'] * 0.5)
        
        time_estimate = self._estimate_recovery_time(recovery_score, current_state.intensity)
        
        return {
            'recovery_score': max(0.0, min(1.0, recovery_score)),
            'estimated_time': time_estimate,
            'factors': recovery_factors
        }

    def _estimate_recovery_time(self, recovery_score: float, intensity: float) -> str:
        if recovery_score > 0.8 and intensity < 0.3:
            return 'minutes'
        elif recovery_score > 0.6 and intensity < 0.5:
            return 'hours'
        elif recovery_score > 0.4:
            return 'days'
        else:
            return 'weeks'

    def predict_next_emotion(self, current_state: EmotionalState, context: ConversationContext) -> List[Tuple[str, float]]:
        predictions = []
        all_emotions = {**current_state.primary_emotions, **current_state.secondary_emotions}
        
        dominant = current_state.get_dominant_emotion()
        if dominant:
            transitions = {
                'happiness': [('excitement', 0.4), ('gratitude', 0.3), ('pride', 0.2)],
                'sadness': [('loneliness', 0.4), ('anxiety', 0.3)],
                'anger': [('frustration', 0.5), ('sadness', 0.2)],
                'fear': [('anxiety', 0.5), ('stress', 0.3)],
                'surprise': [('happiness', 0.4), ('curiosity', 0.3)],
                'disgust': [('anger', 0.3), ('sadness', 0.2)]
            }
            if dominant in transitions:
                predictions.extend(transitions[dominant])
        
        if context.sentiment > 0.5:
            predictions.append(('happiness', 0.3))
        elif context.sentiment < -0.5:
            predictions.append(('sadness', 0.3))
        
        return sorted(predictions, key=lambda x: x[1], reverse=True)[:3]

    def predict_engagement_level(self, history: List[EmotionalState], context: ConversationContext) -> float:
        if not history:
            return 0.5
        
        recent = history[-5:]
        avg_intensity = sum(s.intensity for s in recent) / len(recent)
        sentiment_trend = context.emotional_trend[-3:] if len(context.emotional_trend) else [0]
        avg_sentiment = sum(sentiment_trend) / len(sentiment_trend)
        
        engagement = avg_intensity * 0.5 + (avg_sentiment + 1) / 2 * 0.5
        
        return max(0.0, min(1.0, engagement))

    def predict_motivation_level(self, current_state: EmotionalState, personality: PersonalityTraits) -> float:
        motivation = (
            current_state.secondary_emotions.get('hope', 0) * 0.3 +
            current_state.secondary_emotions.get('confidence', 0) * 0.3 +
            personality.optimism * 0.2 +
            personality.confidence * 0.2
        )
        return max(0.0, min(1.0, motivation))

    def get_full_prediction(self, current_state: EmotionalState, personality: PersonalityTraits, context: ConversationContext, history: List[EmotionalState]) -> Dict:
        return {
            'escalation': self.predict_emotional_escalation(current_state, history),
            'recovery': self.predict_emotional_recovery(current_state, personality),
            'next_emotions': self.predict_next_emotion(current_state, context),
            'engagement': self.predict_engagement_level(history, context),
            'motivation': self.predict_motivation_level(current_state, personality)
        }
