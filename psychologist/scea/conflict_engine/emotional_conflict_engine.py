from scea.core.models import EmotionVector
from typing import Dict, List, Tuple


class EmotionalConflictEngine:
    def __init__(self):
        self.conflicts: List[Dict] = []
        self.conflict_pairs = [
            ('fear', 'curiosity'),
            ('love', 'anger'),
            ('hope', 'anxiety'),
            ('confidence', 'doubt'),
            ('trust', 'disgust'),
            ('joy', 'sadness')
        ]

    def detect_conflicts(self, emotions: EmotionVector) -> List[Dict]:
        current_conflicts = []
        
        for e1, e2 in self.conflict_pairs:
            val1 = emotions.emotions.get(e1, 0.0)
            val2 = emotions.emotions.get(e2, 0.0)
            
            if abs(val1) > 0.3 and abs(val2) > 0.3:
                if (val1 > 0 and val2 > 0) or (val1 < 0 and val2 < 0):
                    intensity = (abs(val1) + abs(val2)) / 2
                    current_conflicts.append({
                        'emotions': (e1, e2),
                        'intensity': intensity,
                        'values': (val1, val2)
                    })
        
        self.conflicts.extend(current_conflicts)
        if len(self.conflicts) > 100:
            self.conflicts = self.conflicts[-100:]
        
        return current_conflicts

    def resolve_conflict(self, conflict: Dict, neuro_effects: Dict) -> Dict:
        e1, e2 = conflict['emotions']
        
        resolution_factor = 1.0
        if 'stability' in neuro_effects:
            resolution_factor += neuro_effects['stability'] * 0.3
        
        if conflict['intensity'] < 0.5:
            return {
                'action': 'blend',
                'factors': {e1: 0.5, e2: 0.5}
            }
        else:
            dominant = e1 if abs(conflict['values'][0]) > abs(conflict['values'][1]) else e2
            subordinate = e2 if dominant == e1 else e1
            
            return {
                'action': 'suppress',
                'dominant': dominant,
                'subordinate': subordinate,
                'suppression_strength': 0.3 * resolution_factor
            }

    def apply_resolution(self, emotions: EmotionVector, resolution: Dict) -> EmotionVector:
        if resolution['action'] == 'blend':
            pass
        elif resolution['action'] == 'suppress':
            sub = resolution['subordinate']
            emotions.emotions[sub] *= (1 - resolution['suppression_strength'])
        
        emotions._update_intensity_valence()
        return emotions
