from scea.core.models import Need
from typing import Dict, List
import random


class NeedsEngine:
    def __init__(self):
        self.needs: Dict[str, Need] = {}
        self._initialize_default_needs()

    def _initialize_default_needs(self):
        default_needs = [
            Need(
                name="knowledge",
                satisfaction=0.5,
                priority=0.6,
                deprivation=0.0,
                description="Desire to learn and understand"
            ),
            Need(
                name="social",
                satisfaction=0.5,
                priority=0.7,
                deprivation=0.0,
                description="Desire for connection and interaction"
            ),
            Need(
                name="achievement",
                satisfaction=0.4,
                priority=0.65,
                deprivation=0.0,
                description="Desire to accomplish and succeed"
            ),
            Need(
                name="stability",
                satisfaction=0.6,
                priority=0.55,
                deprivation=0.0,
                description="Desire for security and consistency"
            ),
            Need(
                name="exploration",
                satisfaction=0.5,
                priority=0.5,
                deprivation=0.0,
                description="Desire to explore and discover"
            ),
            Need(
                name="security",
                satisfaction=0.7,
                priority=0.8,
                deprivation=0.0,
                description="Desire for safety and protection"
            ),
            Need(
                name="recognition",
                satisfaction=0.3,
                priority=0.45,
                deprivation=0.0,
                description="Desire to be acknowledged and valued"
            ),
            Need(
                name="autonomy",
                satisfaction=0.55,
                priority=0.5,
                deprivation=0.0,
                description="Desire for independence and control"
            )
        ]
        for need in default_needs:
            self.needs[need.name] = need

    def update(self, neuro_effects: Dict, experiences: List[Dict]) -> Dict[str, Need]:
        for experience in experiences:
            if 'satisfy_need' in experience:
                need_name = experience['satisfy_need']
                if need_name in self.needs:
                    amount = experience.get('amount', 0.1)
                    self.needs[need_name].satisfaction = min(1.0, 
                        self.needs[need_name].satisfaction + amount
                    )
        
        deprivation_rate = 0.005
        for need_name, need in self.needs.items():
            need.deprivation += deprivation_rate * (1 - need.satisfaction)
            need.satisfaction *= 0.995
            
            need.satisfaction = max(0.0, min(1.0, need.satisfaction))
            need.deprivation = max(0.0, min(1.0, need.deprivation))
            
            base_priority = need.priority
            need.priority = base_priority * (0.5 + need.deprivation * 0.5)
            
            if len(need.history) > 100:
                need.history = need.history[-100:]
            need.history.append(need.satisfaction)
        
        self._update_priorities_from_neurochemistry(neuro_effects)
        return self.needs

    def _update_priorities_from_neurochemistry(self, neuro_effects: Dict):
        if 'curiosity' in neuro_effects:
            self.needs['knowledge'].priority = max(0.2, 
                self.needs['knowledge'].priority + neuro_effects['curiosity'] * 0.1
            )
            self.needs['exploration'].priority = max(0.2, 
                self.needs['exploration'].priority + neuro_effects['curiosity'] * 0.15
            )
        
        if 'trust_formation' in neuro_effects:
            self.needs['social'].priority = max(0.2, 
                self.needs['social'].priority + neuro_effects['trust_formation'] * 0.1
            )
        
        if 'confidence' in neuro_effects:
            self.needs['achievement'].priority = max(0.2, 
                self.needs['achievement'].priority + neuro_effects['confidence'] * 0.1
            )
        
        if 'threat_sensitivity' in neuro_effects:
            self.needs['security'].priority = max(0.2, 
                self.needs['security'].priority + neuro_effects['threat_sensitivity'] * 0.2
            )

    def get_competing_needs(self) -> List[Need]:
        sorted_needs = sorted(
            self.needs.values(),
            key=lambda x: x.priority * (1 + x.deprivation),
            reverse=True
        )
        return sorted_needs[:3]

    def get_most_pressing_need(self) -> Need:
        return max(
            self.needs.values(),
            key=lambda x: x.priority * (1 + x.deprivation)
        )
