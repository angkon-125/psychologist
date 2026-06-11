from typing import Dict, List, Optional
import random


class EmotionStateMachine:
    def __init__(self):
        self.current_state = 'neutral'
        self.state_history = ['neutral']
        self.transition_probabilities = self._init_transitions()

    def _init_transitions(self) -> Dict[str, Dict[str, float]]:
        return {
            'neutral': {
                'happiness': 0.2, 'sadness': 0.15, 'anger': 0.1, 'fear': 0.1,
                'surprise': 0.15, 'excitement': 0.1, 'anxiety': 0.1, 'curiosity': 0.1
            },
            'happiness': {
                'happiness': 0.5, 'excitement': 0.2, 'pride': 0.15, 'gratitude': 0.1, 'neutral': 0.05
            },
            'sadness': {
                'sadness': 0.5, 'loneliness': 0.2, 'anxiety': 0.15, 'neutral': 0.15
            },
            'anger': {
                'anger': 0.4, 'frustration': 0.3, 'neutral': 0.2, 'sadness': 0.1
            },
            'fear': {
                'fear': 0.4, 'anxiety': 0.35, 'stress': 0.15, 'neutral': 0.1
            },
            'surprise': {
                'surprise': 0.2, 'happiness': 0.3, 'fear': 0.2, 'curiosity': 0.2, 'neutral': 0.1
            },
            'excitement': {
                'excitement': 0.45, 'happiness': 0.3, 'curiosity': 0.15, 'neutral': 0.1
            },
            'anxiety': {
                'anxiety': 0.5, 'stress': 0.25, 'fear': 0.15, 'neutral': 0.1
            },
            'frustration': {
                'frustration': 0.4, 'anger': 0.3, 'sadness': 0.2, 'neutral': 0.1
            },
            'stress': {
                'stress': 0.45, 'anxiety': 0.25, 'burnout': 0.15, 'frustration': 0.1, 'neutral': 0.05
            },
            'burnout': {
                'burnout': 0.5, 'emotional_fatigue': 0.3, 'sadness': 0.1, 'emotional_recovery': 0.1
            },
            'curiosity': {
                'curiosity': 0.4, 'excitement': 0.3, 'hope': 0.15, 'neutral': 0.15
            }
        }

    def transition(self, trigger_emotion: Optional[str] = None, intensity: float = 0.5) -> str:
        if trigger_emotion and trigger_emotion in self.transition_probabilities:
            if random.random() < intensity:
                self.current_state = trigger_emotion
                self.state_history.append(self.current_state)
                return self.current_state
        
        if self.current_state in self.transition_probabilities:
            transitions = self.transition_probabilities[self.current_state]
            states = list(transitions.keys())
            probabilities = list(transitions.values())
            next_state = random.choices(states, weights=probabilities, k=1)[0]
            self.current_state = next_state
            self.state_history.append(self.current_state)
            if len(self.state_history) > 50:
                self.state_history = self.state_history[-50:]
            return next_state
        
        return self.current_state

    def get_most_likely_next(self) -> List[str]:
        if self.current_state not in self.transition_probabilities:
            return []
        transitions = self.transition_probabilities[self.current_state]
        sorted_states = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
        return [state for state, prob in sorted_states[:3]]

    def reset(self):
        self.current_state = 'neutral'
        self.state_history = ['neutral']

    def add_custom_transition(self, from_state: str, to_state: str, probability: float):
        if from_state not in self.transition_probabilities:
            self.transition_probabilities[from_state] = {}
        self.transition_probabilities[from_state][to_state] = probability
        total = sum(self.transition_probabilities[from_state].values())
        for state in self.transition_probabilities[from_state]:
            self.transition_probabilities[from_state][state] /= total
