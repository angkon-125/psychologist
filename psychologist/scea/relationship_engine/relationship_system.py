from scea.core.models import Relationship, EmotionVector
from typing import Dict, List, Optional
from datetime import datetime


class RelationshipEngine:
    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}

    def interact(
        self,
        entity_id: str,
        interaction_type: str,
        emotional_response: EmotionVector,
        positive: bool = True
    ) -> Relationship:
        if entity_id not in self.relationships:
            self.relationships[entity_id] = Relationship(entity_id=entity_id)
        
        rel = self.relationships[entity_id]
        
        rel.interaction_history.append({
            'type': interaction_type,
            'positive': positive,
            'timestamp': datetime.now()
        })
        if len(rel.interaction_history) > 100:
            rel.interaction_history = rel.interaction_history[-100:]
        
        rel.familiarity = min(1.0, rel.familiarity + 0.05)
        
        if positive:
            rel.trust = min(1.0, rel.trust + 0.03)
            rel.respect = min(1.0, rel.respect + 0.02)
            rel.reliability = min(1.0, rel.reliability + 0.02)
            rel.attachment = min(1.0, rel.attachment + 0.01)
        else:
            rel.trust = max(0.0, rel.trust - 0.04)
            rel.respect = max(0.0, rel.respect - 0.03)
            rel.reliability = max(0.0, rel.reliability - 0.03)
        
        dominant_emotion = emotional_response.get_dominant_emotion()
        if dominant_emotion:
            rel.emotional_associations[dominant_emotion] = (
                rel.emotional_associations.get(dominant_emotion, 0.0) +
                emotional_response.emotions[dominant_emotion] * 0.1
            )
            rel.emotional_associations[dominant_emotion] = max(-1.0, min(1.0,
                rel.emotional_associations[dominant_emotion]
            ))
        
        return rel

    def get_relationship_summary(self, entity_id: str) -> Optional[Dict]:
        if entity_id not in self.relationships:
            return None
        
        rel = self.relationships[entity_id]
        return {
            'entity_id': entity_id,
            'trust': rel.trust,
            'familiarity': rel.familiarity,
            'attachment': rel.attachment,
            'respect': rel.respect,
            'reliability': rel.reliability,
            'interaction_count': len(rel.interaction_history),
            'dominant_association': max(
                rel.emotional_associations.items(),
                key=lambda x: abs(x[1])
            ) if rel.emotional_associations else None
        }

    def get_closest_relationships(self, limit: int = 5) -> List[Dict]:
        summaries = []
        for entity_id in self.relationships:
            summary = self.get_relationship_summary(entity_id)
            if summary:
                summaries.append(summary)
        
        return sorted(
            summaries,
            key=lambda x: x['attachment'] + x['trust'],
            reverse=True
        )[:limit]
