from scea.core.models import Belief, Value, DecisionRecord
from typing import List, Dict


class CognitiveDissonanceEngine:
    def __init__(self):
        self.dissonance_score: float = 0.0
        self.dissonance_history: List[float] = []
        self.resolutions: List[Dict] = []

    def calculate_dissonance(
        self,
        beliefs: List[Belief],
        values: List[Value],
        decisions: List[DecisionRecord]
    ) -> float:
        total = 0.0
        
        belief_conflicts = self._find_belief_conflicts(beliefs)
        for conflict in belief_conflicts:
            b1, b2 = conflict
            conflict_strength = (b1.confidence + b2.confidence) / 2
            total += conflict_strength * 0.4
        
        value_action_conflicts = self._find_value_action_conflicts(values, decisions)
        total += value_action_conflicts * 0.4
        
        belief_decision_conflicts = self._find_belief_decision_conflicts(beliefs, decisions)
        total += belief_decision_conflicts * 0.2
        
        self.dissonance_score = min(1.0, total)
        
        self.dissonance_history.append(self.dissonance_score)
        if len(self.dissonance_history) > 100:
            self.dissonance_history = self.dissonance_history[-100:]
        
        return self.dissonance_score

    def _find_belief_conflicts(self, beliefs: List[Belief]) -> List[List[Belief]]:
        conflicts = []
        for i, b1 in enumerate(beliefs):
            for b2 in beliefs[i+1:]:
                if (b1.subject == b2.subject and 
                    b1.predicate == b2.predicate and 
                    b1.object != b2.object):
                    conflicts.append([b1, b2])
        return conflicts

    def _find_value_action_conflicts(self, values: List[Value], decisions: List[DecisionRecord]) -> float:
        conflict = 0.0
        recent_decisions = decisions[-10:] if len(decisions) > 10 else decisions
        
        for value in values:
            for decision in recent_decisions:
                if decision.outcome:
                    if 'violates' in decision.context and value.name in decision.context['violates']:
                        conflict += value.importance * 0.1
        return conflict

    def _find_belief_decision_conflicts(self, beliefs: List[Belief], decisions: List[DecisionRecord]) -> float:
        conflict = 0.0
        recent_decisions = decisions[-5:] if len(decisions) > 5 else decisions
        
        for belief in beliefs:
            for decision in recent_decisions:
                if 'contradicts_belief' in decision.context:
                    if decision.context['contradicts_belief'] == belief.id:
                        conflict += belief.confidence * 0.1
        return conflict

    def resolve_dissonance(self, beliefs: List[Belief]) -> List[Dict]:
        resolutions = []
        
        conflicts = self._find_belief_conflicts(beliefs)
        for conflict in conflicts:
            b1, b2 = conflict
            if b1.confidence > b2.confidence:
                resolutions.append({
                    'type': 'adjust_belief',
                    'target': b2.id,
                    'action': 'reduce_confidence',
                    'amount': 0.1
                })
            else:
                resolutions.append({
                    'type': 'adjust_belief',
                    'target': b1.id,
                    'action': 'reduce_confidence',
                    'amount': 0.1
                })
        
        resolutions.append({
            'type': 'seek_evidence',
            'priority': self.dissonance_score
        })
        
        self.resolutions.extend(resolutions)
        return resolutions
