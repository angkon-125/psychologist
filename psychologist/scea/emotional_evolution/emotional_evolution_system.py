from scea.core.models import Identity, DecisionRecord, Memory
from typing import Dict, List
import random


class EmotionalEvolutionEngine:
    def __init__(self):
        self.evolution_history: List[Dict] = []
        self.mutation_rate: float = 0.05

    def evolve(
        self,
        identity: Identity,
        decisions: List[DecisionRecord],
        memories: List[Memory]
    ) -> Identity:
        evolved_identity = Identity()
        evolved_identity.values = identity.values.copy()
        evolved_identity.self_image = identity.self_image.copy()
        evolved_identity.preferences = identity.preferences.copy()
        evolved_identity.self_confidence = identity.self_confidence
        evolved_identity.consistency_score = identity.consistency_score
        
        self._evolve_values(evolved_identity, decisions)
        self._evolve_self_image(evolved_identity, memories)
        self._apply_random_mutations(evolved_identity)
        
        self.evolution_history.append({
            'step': len(self.evolution_history),
            'changes': 'values_and_self_image'
        })
        if len(self.evolution_history) > 100:
            self.evolution_history = self.evolution_history[-100:]
        
        return evolved_identity

    def _evolve_values(self, identity: Identity, decisions: List[DecisionRecord]):
        recent_decisions = decisions[-20:] if len(decisions) > 20 else decisions
        
        for value in identity.values:
            success_count = 0
            for decision in recent_decisions:
                if value.name in decision.decision.lower():
                    if decision.evaluation_score and decision.evaluation_score > 0.6:
                        success_count += 1
                    else:
                        success_count -= 0.5
            
            if success_count > 3:
                value.importance = min(1.0, value.importance + 0.05)
            elif success_count < -1:
                value.importance = max(0.1, value.importance - 0.03)

    def _evolve_self_image(self, identity: Identity, memories: List[Memory]):
        recent_memories = memories[-30:] if len(memories) > 30 else memories
        
        for trait in identity.self_image:
            positive = 0
            for memory in recent_memories:
                if memory.emotional_state.valence > 0 and trait in memory.content.lower():
                    positive += 1
                elif memory.emotional_state.valence < 0 and trait in memory.content.lower():
                    positive -= 0.5
            
            if positive > 2:
                identity.self_image[trait] = min(1.0, identity.self_image[trait] + 0.03)
            elif positive < -1:
                identity.self_image[trait] = max(0.0, identity.self_image[trait] - 0.02)

    def _apply_random_mutations(self, identity: Identity):
        if random.random() < self.mutation_rate:
            trait = random.choice(list(identity.self_image.keys()))
            change = random.uniform(-0.05, 0.05)
            identity.self_image[trait] = max(0.0, min(1.0, identity.self_image[trait] + change))
        
        if random.random() < self.mutation_rate and identity.values:
            value = random.choice(identity.values)
            change = random.uniform(-0.05, 0.05)
            value.importance = max(0.1, min(1.0, value.importance + change))
