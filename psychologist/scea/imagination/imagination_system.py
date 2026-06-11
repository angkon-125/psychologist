from scea.core.models import EmotionVector, Goal
from typing import Dict, List
import random


class ImaginationEngine:
    def __init__(self):
        self.simulations: List[Dict] = []

    def simulate_future(
        self,
        current_emotions: EmotionVector,
        current_goals: List[Goal],
        world_model: Dict
    ) -> List[Dict]:
        simulations = []
        
        for goal in current_goals[:2]:
            success_simulation = self._simulate_outcome(goal, True, current_emotions)
            failure_simulation = self._simulate_outcome(goal, False, current_emotions)
            simulations.extend([success_simulation, failure_simulation])
        
        exploration_scenario = self._simulate_exploration(current_emotions, world_model)
        simulations.append(exploration_scenario)
        
        self.simulations.extend(simulations)
        if len(self.simulations) > 50:
            self.simulations = self.simulations[-50:]
        
        return simulations

    def _simulate_outcome(self, goal: Goal, success: bool, current_emotions: EmotionVector) -> Dict:
        simulated_emotions = EmotionVector()
        simulated_emotions.emotions = current_emotions.emotions.copy()
        
        if success:
            simulated_emotions.emotions['joy'] = min(1.0, simulated_emotions.emotions['joy'] + 0.5)
            simulated_emotions.emotions['pride'] = min(1.0, simulated_emotions.emotions['pride'] + 0.4)
            simulated_emotions.emotions['trust'] = min(1.0, simulated_emotions.emotions['trust'] + 0.2)
        else:
            simulated_emotions.emotions['sadness'] = min(1.0, simulated_emotions.emotions['sadness'] + 0.4)
            simulated_emotions.emotions['doubt'] = min(1.0, simulated_emotions.emotions['doubt'] + 0.3)
            simulated_emotions.emotions['fear'] = min(1.0, simulated_emotions.emotions['fear'] + 0.2)
        
        simulated_emotions._update_intensity_valence()
        
        return {
            'type': 'goal_outcome',
            'goal': goal.id,
            'success': success,
            'emotional_result': simulated_emotions,
            'likelihood': 0.6 + random.uniform(-0.3, 0.3) if success else 0.4 + random.uniform(-0.2, 0.2)
        }

    def _simulate_exploration(self, current_emotions: EmotionVector, world_model: Dict) -> Dict:
        simulated_emotions = EmotionVector()
        simulated_emotions.emotions = current_emotions.emotions.copy()
        
        simulated_emotions.emotions['curiosity'] = min(1.0, simulated_emotions.emotions['curiosity'] + 0.4)
        simulated_emotions.emotions['anticipation'] = min(1.0, simulated_emotions.emotions['anticipation'] + 0.3)
        simulated_emotions.emotions['surprise'] = min(1.0, simulated_emotions.emotions['surprise'] + 0.2)
        
        simulated_emotions._update_intensity_valence()
        
        return {
            'type': 'exploration',
            'emotional_result': simulated_emotions,
            'discovery_chance': 0.5 + random.uniform(-0.2, 0.3),
            'risk': random.uniform(0.1, 0.4)
        }

    def evaluate_simulations(self, simulations: List[Dict]) -> Dict:
        if not simulations:
            return {}
        
        best_simulation = max(
            simulations,
            key=lambda s: s['emotional_result'].valence * s.get('likelihood', 0.5)
        )
        
        return {
            'best_scenario': best_simulation,
            'total_simulations': len(simulations),
            'average_valence': sum(
                s['emotional_result'].valence for s in simulations
            ) / len(simulations)
        }
