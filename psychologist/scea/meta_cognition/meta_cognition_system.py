from scea.core.models import DecisionRecord, Belief
from typing import List, Dict


class MetaCognitionEngine:
    def __init__(self):
        self.self_reflections: List[Dict] = []
        self.decision_evaluations: List[Dict] = []

    def reflect_on_decisions(self, decisions: List[DecisionRecord]) -> List[Dict]:
        reflections = []
        
        recent_decisions = decisions[-10:] if len(decisions) > 10 else decisions
        for decision in recent_decisions:
            evaluation = self._evaluate_decision(decision)
            reflections.append(evaluation)
            self.decision_evaluations.append(evaluation)
        
        if len(self.decision_evaluations) > 100:
            self.decision_evaluations = self.decision_evaluations[-100:]
        
        self.self_reflections.extend(reflections)
        if len(self.self_reflections) > 100:
            self.self_reflections = self.self_reflections[-100:]
        
        return reflections

    def _evaluate_decision(self, decision: DecisionRecord) -> Dict:
        outcome_score = 0.5
        if decision.evaluation_score:
            outcome_score = decision.evaluation_score
        
        confidence = getattr(decision.emotional_state, 'intensity', 0.5)
        
        return {
            'decision_id': decision.id,
            'outcome_score': outcome_score,
            'confidence': confidence,
            'regret': 1 - outcome_score,
            'learned': outcome_score > 0.6
        }

    def reassess_beliefs(self, beliefs: List[Belief]) -> List[Dict]:
        reassessments = []
        
        for belief in beliefs:
            if len(belief.evidence) < 2 and belief.confidence > 0.7:
                reassessments.append({
                    'belief_id': belief.id,
                    'action': 'reduce_confidence',
                    'reason': 'insufficient_evidence',
                    'amount': 0.1
                })
            
            if len(belief.evidence) > 5 and belief.confidence < 0.6:
                reassessments.append({
                    'belief_id': belief.id,
                    'action': 'increase_confidence',
                    'reason': 'sufficient_evidence',
                    'amount': 0.15
                })
        
        return reassessments

    def get_self_awareness_summary(self) -> Dict:
        if not self.decision_evaluations:
            return {}
        
        avg_outcome = sum(d['outcome_score'] for d in self.decision_evaluations) / len(self.decision_evaluations)
        avg_regret = sum(d['regret'] for d in self.decision_evaluations) / len(self.decision_evaluations)
        
        return {
            'decision_success_rate': avg_outcome,
            'average_regret': avg_regret,
            'total_reflections': len(self.self_reflections),
            'learning_rate': sum(1 for d in self.decision_evaluations if d['learned']) / len(self.decision_evaluations) if self.decision_evaluations else 0
        }
