from scea.core.models import (
    SCEAState,
    EmotionVector,
    Memory,
    DecisionRecord
)
from scea.neurochemistry import NeurochemicalSystem
from scea.needs_engine import NeedsEngine
from scea.emotional_physics import EmotionalPhysicsEngine
from scea.world_model import WorldModel
from scea.relationship_engine import RelationshipEngine
from scea.cognitive_dissonance import CognitiveDissonanceEngine
from scea.conflict_engine import EmotionalConflictEngine
from scea.goal_generation import GoalGenerationEngine
from scea.identity_formation import IdentityFormationEngine
from scea.imagination import ImaginationEngine
from scea.meta_cognition import MetaCognitionEngine
from scea.emotional_evolution import EmotionalEvolutionEngine
from scea.consciousness_layer import ConsciousnessLayer
from datetime import datetime


class SCEA:
    def __init__(self):
        self.state = SCEAState()
        
        self.neurochemistry = NeurochemicalSystem()
        self.needs_engine = NeedsEngine()
        self.emotional_physics = EmotionalPhysicsEngine()
        self.world_model = WorldModel()
        self.relationship_engine = RelationshipEngine()
        self.cognitive_dissonance = CognitiveDissonanceEngine()
        self.emotional_conflict = EmotionalConflictEngine()
        self.goal_engine = GoalGenerationEngine()
        self.identity_engine = IdentityFormationEngine()
        self.imagination = ImaginationEngine()
        self.meta_cognition = MetaCognitionEngine()
        self.emotional_evolution = EmotionalEvolutionEngine()
        self.consciousness = ConsciousnessLayer()
        
        self._initialize_state()

    def _initialize_state(self):
        self.state.neurochemistry = self.neurochemistry.state
        self.state.emotions = EmotionVector()
        self.state.needs = self.needs_engine.needs
        self.state.beliefs = self.world_model.beliefs
        self.state.goals = self.goal_engine.active_goals
        self.state.memories = []
        self.state.relationships = self.relationship_engine.relationships
        self.state.identity = self.identity_engine.identity
        self.state.cognitive_dissonance = 0.0

    def step(self, triggers: dict = None, experiences: list = None) -> dict:
        triggers = triggers or {}
        experiences = experiences or []
        self.state.step += 1
        self.state.time = datetime.now()
        
        neuro_state = self.neurochemistry.update(triggers)
        self.state.neurochemistry = neuro_state
        neuro_effects = self.neurochemistry.get_effects()
        
        needs = self.needs_engine.update(neuro_effects, experiences)
        self.state.needs = needs
        
        emotion_triggers = {}
        for exp in experiences:
            if 'type' in exp:
                emotion_triggers[exp['type']] = exp
        
        self.state.emotions = self.emotional_physics.update(
            self.state.emotions,
            emotion_triggers,
            neuro_effects
        )
        
        conflicts = self.emotional_conflict.detect_conflicts(self.state.emotions)
        for conflict in conflicts:
            resolution = self.emotional_conflict.resolve_conflict(conflict, neuro_effects)
            self.state.emotions = self.emotional_conflict.apply_resolution(
                self.state.emotions,
                resolution
            )
        
        self.state.cognitive_dissonance = self.cognitive_dissonance.calculate_dissonance(
            self.state.beliefs,
            self.state.identity.values,
            self.state.decision_history
        )
        
        new_goals = self.goal_engine.generate_goals(
            needs,
            self.state.emotions.emotions,
            {'environment_state': self.world_model.environment_state}
        )
        self.state.goals = self.goal_engine.active_goals
        
        simulations = self.imagination.simulate_future(
            self.state.emotions,
            self.state.goals,
            {'environment_state': self.world_model.environment_state}
        )
        evaluated = self.imagination.evaluate_simulations(simulations)
        
        consciousness_data = self.consciousness.process_for_consciousness(
            self.state.emotions,
            needs,
            self.state.goals,
            simulations
        )
        self.state.attention_focus = consciousness_data['attention_focus']
        self.state.active_thoughts = consciousness_data['active_thoughts']
        
        decision = self._make_decision(needs, consciousness_data, evaluated)
        decision_record = DecisionRecord(
            decision=decision['description'],
            context=decision['context'],
            emotional_state=self.state.emotions
        )
        self.state.decision_history.append(decision_record)
        if len(self.state.decision_history) > 100:
            self.state.decision_history = self.state.decision_history[-100:]
        
        memory = Memory(
            content=decision['description'],
            emotional_state=self.state.emotions,
            importance=0.5 + self.state.emotions.intensity * 0.3,
            context=decision['context']
        )
        self.state.memories.append(memory)
        if len(self.state.memories) > 500:
            self.state.memories = sorted(
                self.state.memories,
                key=lambda m: m.importance,
                reverse=True
            )[:500]
        
        self.meta_cognition.reflect_on_decisions(self.state.decision_history)
        
        if self.state.step % 10 == 0:
            self.state.identity = self.identity_engine.update_from_experiences(
                self.state.decision_history,
                self.state.memories,
                self.emotional_physics.momentum
            )
            self.state.identity = self.emotional_evolution.evolve(
                self.state.identity,
                self.state.decision_history,
                self.state.memories
            )
        
        return {
            'step': self.state.step,
            'neurochemistry': {
                'dopamine': neuro_state.dopamine,
                'serotonin': neuro_state.serotonin,
                'oxytocin': neuro_state.oxytocin,
                'cortisol': neuro_state.cortisol,
                'adrenaline': neuro_state.adrenaline
            },
            'emotions': {
                'dominant': self.state.emotions.get_dominant_emotion(),
                'valence': self.state.emotions.valence,
                'intensity': self.state.emotions.intensity,
                'all': self.state.emotions.emotions
            },
            'needs': {name: n.satisfaction for name, n in needs.items()},
            'cognitive_dissonance': self.state.cognitive_dissonance,
            'consciousness': consciousness_data,
            'decision': decision,
            'identity': {
                'self_confidence': self.state.identity.self_confidence,
                'consistency': self.state.identity.consistency_score,
                'self_image': self.state.identity.self_image
            }
        }

    def _make_decision(self, needs, consciousness_data, evaluated_simulations):
        pressing_need = self.needs_engine.get_most_pressing_need()
        
        options = []
        if consciousness_data['workspace_contents']:
            for content in consciousness_data['workspace_contents']:
                options.append({
                    'type': content['type'],
                    'description': f"Focus on {content['content']}",
                    'priority': content['priority']
                })
        
        if pressing_need:
            options.append({
                'type': 'need_satisfaction',
                'description': f"Work on satisfying {pressing_need.name}",
                'priority': pressing_need.priority * (1 + pressing_need.deprivation)
            })
        
        if evaluated_simulations and 'best_scenario' in evaluated_simulations:
            best = evaluated_simulations['best_scenario']
            options.append({
                'type': 'simulated',
                'description': f"Pursue {best['type']} scenario",
                'priority': best['likelihood'] if 'likelihood' in best else 0.5
            })
        
        if not options:
            return {
                'description': "Explore and observe",
                'context': {'action': 'exploration'},
                'priority': 0.5
            }
        
        best_option = max(options, key=lambda x: x['priority'])
        if 'context' not in best_option:
            best_option['context'] = {'type': best_option['type']}
        return best_option

    def interact_with_entity(self, entity_id: str, interaction_type: str, positive: bool = True):
        relationship = self.relationship_engine.interact(
            entity_id,
            interaction_type,
            self.state.emotions,
            positive
        )
        self.state.relationships = self.relationship_engine.relationships
        
        triggers = {}
        if positive and relationship.trust > 0.5:
            triggers['social_connection'] = 0.4
            triggers['reward'] = 0.3
        elif not positive:
            triggers['threat'] = 0.3
            triggers['stress'] = 0.2
        
        if triggers:
            self.neurochemistry.update(triggers)
        
        return relationship

    def add_experience(self, experience_type: str, **kwargs):
        exp = {'type': experience_type, **kwargs}
        return self.step(experiences=[exp])
