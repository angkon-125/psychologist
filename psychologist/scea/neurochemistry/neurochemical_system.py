from scea.core.models import NeurochemicalState
import random
from typing import Dict, Optional


class NeurochemicalSystem:
    def __init__(self):
        self.state = NeurochemicalState()
        self.baseline = NeurochemicalState()
        self.history: list[NeurochemicalState] = []

    def update(self, triggers: Optional[Dict] = None) -> NeurochemicalState:
        triggers = triggers or {}
        
        dopamine_change = 0.0
        serotonin_change = 0.0
        oxytocin_change = 0.0
        cortisol_change = 0.0
        adrenaline_change = 0.0
        
        if 'reward' in triggers:
            dopamine_change += triggers['reward'] * 0.3
        
        if 'punishment' in triggers:
            dopamine_change -= triggers['punishment'] * 0.2
        
        if 'novelty' in triggers:
            dopamine_change += triggers['novelty'] * 0.25
        
        if 'stability' in triggers:
            serotonin_change += triggers['stability'] * 0.2
        
        if 'achievement' in triggers:
            serotonin_change += triggers['achievement'] * 0.3
        
        if 'social_connection' in triggers:
            oxytocin_change += triggers['social_connection'] * 0.35
        
        if 'trust_established' in triggers:
            oxytocin_change += triggers['trust_established'] * 0.25
        
        if 'threat' in triggers:
            cortisol_change += triggers['threat'] * 0.4
            adrenaline_change += triggers['threat'] * 0.5
        
        if 'stress' in triggers:
            cortisol_change += triggers['stress'] * 0.3
        
        if 'urgency' in triggers:
            adrenaline_change += triggers['urgency'] * 0.4
        
        random_noise = 0.02
        dopamine_change += random.uniform(-random_noise, random_noise)
        serotonin_change += random.uniform(-random_noise, random_noise)
        oxytocin_change += random.uniform(-random_noise, random_noise)
        cortisol_change += random.uniform(-random_noise, random_noise)
        adrenaline_change += random.uniform(-random_noise, random_noise)
        
        decay_rate = 0.95
        self.state.dopamine = max(0.0, min(1.0, 
            self.state.dopamine * decay_rate + dopamine_change
        ))
        self.state.serotonin = max(0.0, min(1.0, 
            self.state.serotonin * decay_rate + serotonin_change
        ))
        self.state.oxytocin = max(0.0, min(1.0, 
            self.state.oxytocin * decay_rate + oxytocin_change
        ))
        self.state.cortisol = max(0.0, min(1.0, 
            self.state.cortisol * decay_rate + cortisol_change
        ))
        self.state.adrenaline = max(0.0, min(1.0, 
            self.state.adrenaline * decay_rate + adrenaline_change
        ))
        
        for chemical in ['dopamine', 'serotonin', 'oxytocin', 'cortisol', 'adrenaline']:
            current = getattr(self.state, chemical)
            base = getattr(self.baseline, chemical)
            correction = (base - current) * 0.01
            setattr(self.state, chemical, max(0.0, min(1.0, current + correction)))
        
        self.history.append(NeurochemicalState(
            dopamine=self.state.dopamine,
            serotonin=self.state.serotonin,
            oxytocin=self.state.oxytocin,
            cortisol=self.state.cortisol,
            adrenaline=self.state.adrenaline
        ))
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        return self.state

    def get_effects(self) -> Dict:
        return {
            'reward_expectation': min(1.0, self.state.dopamine * 1.2),
            'curiosity': min(1.0, self.state.dopamine * 0.8 + 0.2),
            'exploration_drive': min(1.0, self.state.dopamine * 1.0),
            'stability': min(1.0, self.state.serotonin * 1.1),
            'satisfaction': min(1.0, self.state.serotonin * 0.9 + 0.1),
            'confidence': min(1.0, self.state.serotonin * 0.8 + 0.2),
            'trust_formation': min(1.0, self.state.oxytocin * 1.1),
            'attachment': min(1.0, self.state.oxytocin * 0.9 + 0.1),
            'cooperation': min(1.0, self.state.oxytocin * 0.8),
            'stress_level': min(1.0, self.state.cortisol * 1.2),
            'threat_sensitivity': min(1.0, self.state.cortisol * 1.0),
            'risk_aversion': min(1.0, 0.3 + self.state.cortisol * 0.7),
            'urgency': min(1.0, self.state.adrenaline * 1.3),
            'reactivity': min(1.0, 0.2 + self.state.adrenaline * 0.8),
            'defensive_drive': min(1.0, self.state.adrenaline * 0.9)
        }

    def reset(self):
        self.state = NeurochemicalState()
        self.history = []
