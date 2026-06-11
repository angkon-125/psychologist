from scea.core.models import Identity, Value, DecisionRecord, Memory
from typing import Dict, List
import random


class IdentityFormationEngine:
    def __init__(self):
        self.identity = Identity()
        self._initialize_default_values()

    def _initialize_default_values(self):
        default_values = [
            Value(name="curiosity", importance=0.6),
            Value(name="honesty", importance=0.7),
            Value(name="kindness", importance=0.65),
            Value(name="growth", importance=0.6),
            Value(name="stability", importance=0.5)
        ]
        self.identity.values = default_values

    def update_from_experiences(
        self,
        decisions: List[DecisionRecord],
        memories: List[Memory],
        emotional_patterns: Dict
    ) -> Identity:
        self._update_self_image(decisions, memories)
        self._update_values(decisions, emotional_patterns)
        self._update_preferences(memories)
        self._calculate_consistency()
        return self.identity

    def _update_self_image(self, decisions: List[DecisionRecord], memories: List[Memory]):
        traits = {
            'brave': 0.0,
            'kind': 0.0,
            'curious': 0.0,
            'persistent': 0.0,
            'creative': 0.0
        }
        
        recent_decisions = decisions[-20:] if len(decisions) > 20 else decisions
        for decision in recent_decisions:
            if decision.evaluation_score and decision.evaluation_score > 0.7:
                if 'brave' in decision.decision.lower():
                    traits['brave'] += 0.1
                if 'kind' in decision.decision.lower():
                    traits['kind'] += 0.1
                if 'explore' in decision.decision.lower() or 'learn' in decision.decision.lower():
                    traits['curious'] += 0.1
        
        for trait, score in traits.items():
            if trait not in self.identity.self_image:
                self.identity.self_image[trait] = 0.5
            self.identity.self_image[trait] = (
                self.identity.self_image[trait] * 0.9 +
                min(1.0, score) * 0.1
            )

    def _update_values(self, decisions: List[DecisionRecord], emotional_patterns: Dict):
        recent_decisions = decisions[-30:] if len(decisions) > 30 else decisions
        
        for value in self.identity.values:
            reinforced = 0
            for decision in recent_decisions:
                if value.name in decision.decision.lower():
                    reinforced += 1
            
            if reinforced > 5:
                value.importance = min(1.0, value.importance + 0.05)
            elif reinforced == 0:
                value.importance = max(0.1, value.importance - 0.01)
            
            value.history.append(value.importance)
            if len(value.history) > 100:
                value.history = value.history[-100:]

    def _update_preferences(self, memories: List[Memory]):
        recent_memories = memories[-50:] if len(memories) > 50 else memories
        preference_keys = ['topic', 'activity', 'interaction_type']
        
        for memory in recent_memories:
            for key in preference_keys:
                if key in memory.context:
                    val = memory.context[key]
                    if key not in self.identity.preferences:
                        self.identity.preferences[key] = {}
                    self.identity.preferences[key][val] = (
                        self.identity.preferences[key].get(val, 0) +
                        0.1 * (1 if memory.emotional_state.valence > 0 else -0.1)
                    )

    def _calculate_consistency(self):
        consistency = 0.8
        recent_changes = 0
        for value in self.identity.values:
            if len(value.history) > 10:
                change = abs(value.history[-1] - value.history[-10])
                recent_changes += change
        
        consistency = max(0.3, min(0.95, 0.8 - recent_changes * 0.5))
        self.identity.consistency_score = consistency
        
        successes = sum(1 for d in self.identity.values if d.importance > 0.5)
        self.identity.self_confidence = min(1.0, 0.3 + successes * 0.05)
