from typing import Dict, List
import math


class BayesianEngine:
    def __init__(self):
        self.probability_tables = {}
        self._init_default_tables()

    def _init_default_tables(self):
        self.probability_tables = {
            'sadness_given_loneliness': {
                (True,): 0.7,
                (False,): 0.2
            },
            'anxiety_given_stress_fear': {
                (True, True): 0.9,
                (True, False): 0.6,
                (False, True): 0.5,
                (False, False): 0.1
            },
            'frustration_given_anger_stress': {
                (True, True): 0.85,
                (True, False): 0.5,
                (False, True): 0.4,
                (False, False): 0.05
            },
            'excitement_given_happiness_curiosity': {
                (True, True): 0.9,
                (True, False): 0.6,
                (False, True): 0.4,
                (False, False): 0.1
            },
            'trust_given_agreeableness': {
                (True,): 0.8,
                (False,): 0.3
            },
            'confidence_given_success': {
                (True,): 0.75,
                (False,): 0.3
            }
        }
        self.priors = {
            'loneliness': 0.3,
            'stress': 0.4,
            'fear': 0.2,
            'anger': 0.25,
            'happiness': 0.5,
            'curiosity': 0.4,
            'agreeableness': 0.5,
            'success': 0.4
        }

    def calculate_posterior(self, query: str, evidence: Dict[str, bool]) -> float:
        if query == 'sadness' and 'loneliness' in evidence:
            key = (evidence['loneliness'],)
            return self.probability_tables['sadness_given_loneliness'].get(key, 0.5)
        
        if query == 'anxiety' and 'stress' in evidence and 'fear' in evidence:
            key = (evidence['stress'], evidence['fear'])
            return self.probability_tables['anxiety_given_stress_fear'].get(key, 0.5)
        
        if query == 'frustration' and 'anger' in evidence and 'stress' in evidence:
            key = (evidence['anger'], evidence['stress'])
            return self.probability_tables['frustration_given_anger_stress'].get(key, 0.5)
        
        if query == 'excitement' and 'happiness' in evidence and 'curiosity' in evidence:
            key = (evidence['happiness'], evidence['curiosity'])
            return self.probability_tables['excitement_given_happiness_curiosity'].get(key, 0.5)
        
        return self.priors.get(query, 0.5)

    def update_emotion_probabilities(self, emotional_state: Dict[str, float]) -> Dict[str, float]:
        updated = emotional_state.copy()
        
        evidence = {
            'loneliness': emotional_state.get('loneliness', 0.0) > 0.5,
            'stress': emotional_state.get('stress', 0.0) > 0.5,
            'fear': emotional_state.get('fear', 0.0) > 0.5,
            'anger': emotional_state.get('anger', 0.0) > 0.5,
            'happiness': emotional_state.get('happiness', 0.0) > 0.5,
            'curiosity': emotional_state.get('curiosity', 0.0) > 0.5
        }
        
        if 'sadness' in updated:
            sad_prob = self.calculate_posterior('sadness', {'loneliness': evidence['loneliness']})
            updated['sadness'] = (updated['sadness'] + sad_prob) / 2
        
        if 'anxiety' in updated:
            anxiety_prob = self.calculate_posterior('anxiety', {'stress': evidence['stress'], 'fear': evidence['fear']})
            updated['anxiety'] = (updated['anxiety'] + anxiety_prob) / 2
        
        if 'frustration' in updated:
            frustration_prob = self.calculate_posterior('frustration', {'anger': evidence['anger'], 'stress': evidence['stress']})
            updated['frustration'] = (updated['frustration'] + frustration_prob) / 2
        
        if 'excitement' in updated:
            excitement_prob = self.calculate_posterior('excitement', {'happiness': evidence['happiness'], 'curiosity': evidence['curiosity']})
            updated['excitement'] = (updated['excitement'] + excitement_prob) / 2
        
        return updated

    def sigmoid(self, x: float) -> float:
        return 1 / (1 + math.exp(-x))
