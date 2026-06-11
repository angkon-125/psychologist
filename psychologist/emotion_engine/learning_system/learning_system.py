from typing import Dict, List
import random


class LearningSystem:
    def __init__(self):
        self.response_effectiveness: Dict[str, float] = {}
        self.emotion_transition_history: List[tuple] = []
        self.pattern_weights: Dict[str, float] = {}
        self.learning_rate = 0.1

    def record_response_feedback(self, response_type: str, effectiveness: float):
        if response_type not in self.response_effectiveness:
            self.response_effectiveness[response_type] = 0.5
        old = self.response_effectiveness[response_type]
        self.response_effectiveness[response_type] = (
            old * (1 - self.learning_rate) + effectiveness * self.learning_rate
        )

    def record_emotion_transition(self, from_emotion: str, to_emotion: str, context: str):
        key = (from_emotion, to_emotion, context)
        self.emotion_transition_history.append((from_emotion, to_emotion, context))
        if len(self.emotion_transition_history) > 1000:
            self.emotion_transition_history = self.emotion_transition_history[-1000:]
        
        pattern_key = f"{from_emotion}->{to_emotion}"
        self.pattern_weights[pattern_key] = self.pattern_weights.get(pattern_key, 0.5) + 0.01

    def get_optimal_response_mode(self, current_emotion: str, context: str) -> str:
        modes = ['supportive', 'calming', 'reassuring', 'celebratory', 'encouraging', 'neutral']
        weighted = {}
        for mode in modes:
            base = 0.5
            if mode in self.response_effectiveness:
                base = self.response_effectiveness[mode]
            weighted[mode] = base + random.uniform(-0.1, 0.1)
        return max(weighted.items(), key=lambda x: x[1])[0]

    def predict_transition_probability(self, from_emotion: str, to_emotion: str, context: str) -> float:
        key = f"{from_emotion}->{to_emotion}"
        base = self.pattern_weights.get(key, 0.3)
        return min(1.0, max(0.0, base))

    def adaptive_decay_rate(self, emotion: str, history: List) -> float:
        decay = 0.85
        recent = [h for h in history[-10:] if h.get('dominant') == emotion]
        if len(recent) > 5:
            decay = 0.9
        elif len(recent) < 2:
            decay = 0.75
        return decay

    def get_learning_summary(self) -> Dict:
        return {
            'response_effectiveness': self.response_effectiveness,
            'pattern_count': len(self.pattern_weights),
            'total_transitions': len(self.emotion_transition_history)
        }
