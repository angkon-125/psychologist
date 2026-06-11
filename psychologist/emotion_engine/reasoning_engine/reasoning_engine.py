from ..models import EmotionalState, PersonalityTraits, ConversationContext
from ..fuzzy_logic import FuzzyLogicEngine
from ..bayesian_engine import BayesianEngine
from ..state_machine import EmotionStateMachine
from typing import Dict, List


class Rule:
    def __init__(self, name: str, conditions: Dict, actions: Dict, priority: int = 5):
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.priority = priority

    def evaluate(self, emotional_state: EmotionalState, context: ConversationContext, personality: PersonalityTraits) -> bool:
        for key, condition in self.conditions.items():
            if key.startswith('primary_'):
                emotion = key.replace('primary_', '')
                if emotion in emotional_state.primary_emotions:
                    if isinstance(condition, tuple):
                        op, val = condition
                        if op == '>' and not (emotional_state.primary_emotions[emotion] > val):
                            return False
                        if op == '<' and not (emotional_state.primary_emotions[emotion] < val):
                            return False
                        if op == '>=' and not (emotional_state.primary_emotions[emotion] >= val):
                            return False
                        if op == '<=' and not (emotional_state.primary_emotions[emotion] <= val):
                            return False
                    elif emotional_state.primary_emotions[emotion] < condition:
                        return False
            
            elif key.startswith('secondary_'):
                emotion = key.replace('secondary_', '')
                if emotion in emotional_state.secondary_emotions:
                    if isinstance(condition, tuple):
                        op, val = condition
                        if op == '>' and not (emotional_state.secondary_emotions[emotion] > val):
                            return False
                        if op == '<' and not (emotional_state.secondary_emotions[emotion] < val):
                            return False
                    elif emotional_state.secondary_emotions[emotion] < condition:
                        return False
            
            elif key.startswith('advanced_'):
                emotion = key.replace('advanced_', '')
                if emotion in emotional_state.advanced_emotions:
                    if isinstance(condition, tuple):
                        op, val = condition
                        if op == '>' and not (emotional_state.advanced_emotions[emotion] > val):
                            return False
                        if op == '<' and not (emotional_state.advanced_emotions[emotion] < val):
                            return False
                    elif emotional_state.advanced_emotions[emotion] < condition:
                        return False
            
            elif key.startswith('context_'):
                ctx_key = key.replace('context_', '')
                if hasattr(context, ctx_key):
                    ctx_val = getattr(context, ctx_key)
                    if isinstance(condition, tuple):
                        op, val = condition
                        if op == '>' and not (ctx_val > val):
                            return False
                        if op == '<' and not (ctx_val < val):
                            return False
                    elif ctx_val < condition:
                        return False
            
            elif key.startswith('personality_'):
                trait = key.replace('personality_', '')
                if hasattr(personality, trait):
                    trait_val = getattr(personality, trait)
                    if isinstance(condition, tuple):
                        op, val = condition
                        if op == '>' and not (trait_val > val):
                            return False
                        if op == '<' and not (trait_val < val):
                            return False
                    elif trait_val < condition:
                        return False
        
        return True


class ReasoningEngine:
    def __init__(self):
        self.rules: List[Rule] = []
        self.fuzzy_engine = FuzzyLogicEngine()
        self.bayesian_engine = BayesianEngine()
        self.state_machine = EmotionStateMachine()
        self._init_default_rules()

    def _init_default_rules(self):
        self.rules = [
            Rule(
                name="support_mode_sad_lonely",
                conditions={
                    'primary_sadness': ('>', 0.7),
                    'advanced_loneliness': ('>', 0.6)
                },
                actions={'mode': 'supportive', 'empathy': 0.9, 'comfort': 0.8},
                priority=1
            ),
            Rule(
                name="calm_down_angry",
                conditions={
                    'primary_anger': ('>', 0.7),
                    'context_conflict_level': ('>', 0.5)
                },
                actions={'mode': 'calming', 'de_escalation': 0.9},
                priority=1
            ),
            Rule(
                name="reassure_anxious",
                conditions={
                    'secondary_anxiety': ('>', 0.6),
                    'primary_fear': ('>', 0.4)
                },
                actions={'mode': 'reassuring', 'reassurance': 0.85},
                priority=2
            ),
            Rule(
                name="celebrate_happy",
                conditions={
                    'primary_happiness': ('>', 0.7),
                    'secondary_excitement': ('>', 0.5)
                },
                actions={'mode': 'celebratory', 'enthusiasm': 0.9},
                priority=2
            ),
            Rule(
                name="motivate_curiosity",
                conditions={
                    'secondary_curiosity': ('>', 0.6),
                    'context_motivation_opportunity': ('>', 0.4)
                },
                actions={'mode': 'encouraging', 'motivation': 0.8},
                priority=2
            ),
            Rule(
                name="help_stressed",
                conditions={
                    'advanced_stress': ('>', 0.7),
                    'personality_neuroticism': ('>', 0.5)
                },
                actions={'mode': 'stress_relief', 'calmness': 0.85},
                priority=2
            ),
            Rule(
                name="prevent_burnout",
                conditions={
                    'advanced_stress': ('>', 0.8),
                    'advanced_emotional_fatigue': ('>', 0.6)
                },
                actions={'mode': 'recovery', 'urgency': 0.9},
                priority=1
            ),
            Rule(
                name="build_trust",
                conditions={
                    'advanced_trust': ('<', 0.3),
                    'personality_agreeableness': ('>', 0.5)
                },
                actions={'mode': 'trust_building', 'transparency': 0.8},
                priority=3
            )
        ]

    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)

    def evaluate_rules(self, emotional_state: EmotionalState, context: ConversationContext, personality: PersonalityTraits) -> Dict:
        triggered_actions = {}
        for rule in self.rules:
            if rule.evaluate(emotional_state, context, personality):
                for key, value in rule.actions.items():
                    if key in triggered_actions:
                        triggered_actions[key] = max(triggered_actions[key], value)
                    else:
                        triggered_actions[key] = value
        return triggered_actions

    def reason(self, emotional_state: EmotionalState, context: ConversationContext, personality: PersonalityTraits) -> Dict:
        actions = self.evaluate_rules(emotional_state, context, personality)
        
        all_emotions = {**emotional_state.primary_emotions, **emotional_state.secondary_emotions}
        fuzzy_adjusted = self.fuzzy_engine.apply_rules(all_emotions, personality.to_dict())
        
        bayesian_updated = self.bayesian_engine.update_emotion_probabilities(all_emotions)
        
        dominant = emotional_state.get_dominant_emotion()
        if dominant:
            self.state_machine.transition(dominant, emotional_state.intensity)
        
        return {
            'actions': actions,
            'fuzzy_adjusted': fuzzy_adjusted,
            'bayesian_updated': bayesian_updated,
            'current_fsm_state': self.state_machine.current_state,
            'likely_next_states': self.state_machine.get_most_likely_next(),
            'mode': actions.get('mode', 'neutral')
        }
