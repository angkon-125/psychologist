from scea.core.models import Belief, Relationship
from typing import Dict, List, Optional


class WorldModel:
    def __init__(self):
        self.beliefs: List[Belief] = []
        self.environment_state: Dict = {}
        self.relationships: Dict[str, Relationship] = {}

    def add_belief(
        self,
        subject: str,
        predicate: str,
        obj,
        confidence: float = 0.5,
        source: str = "",
        evidence: List[str] = None
    ) -> Belief:
        evidence = evidence or []
        
        existing = self._find_existing_belief(subject, predicate, obj)
        if existing:
            existing.confidence = (existing.confidence + confidence) / 2
            existing.evidence.extend(evidence)
            existing.evidence = list(set(existing.evidence))
            return existing
        
        new_belief = Belief(
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            source=source,
            evidence=evidence
        )
        self.beliefs.append(new_belief)
        if len(self.beliefs) > 1000:
            self.beliefs = sorted(self.beliefs, key=lambda x: x.confidence, reverse=True)[:1000]
        
        return new_belief

    def _find_existing_belief(self, subject: str, predicate: str, obj) -> Optional[Belief]:
        for belief in self.beliefs:
            if (belief.subject == subject and 
                belief.predicate == predicate and 
                belief.object == obj):
                return belief
        return None

    def query_beliefs(self, subject: str = None, predicate: str = None) -> List[Belief]:
        results = []
        for belief in self.beliefs:
            if subject and belief.subject != subject:
                continue
            if predicate and belief.predicate != predicate:
                continue
            results.append(belief)
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def update_environment(self, updates: Dict):
        self.environment_state.update(updates)

    def add_relationship(self, entity_id: str) -> Relationship:
        if entity_id not in self.relationships:
            self.relationships[entity_id] = Relationship(entity_id=entity_id)
        return self.relationships[entity_id]

    def get_relationship(self, entity_id: str) -> Optional[Relationship]:
        return self.relationships.get(entity_id)

    def get_conflicting_beliefs(self) -> List[List[Belief]]:
        conflicts = []
        for i, b1 in enumerate(self.beliefs):
            for b2 in self.beliefs[i+1:]:
                if (b1.subject == b2.subject and 
                    b1.predicate == b2.predicate and 
                    b1.object != b2.object):
                    conflicts.append([b1, b2])
        return conflicts
