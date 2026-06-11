from typing import Dict, List


class FuzzyLogicEngine:
    def __init__(self):
        self.membership_functions = {}

    def triangular_mf(self, x: float, a: float, b: float, c: float) -> float:
        if x <= a or x >= c:
            return 0.0
        if a < x <= b:
            return (x - a) / (b - a)
        if b < x < c:
            return (c - x) / (c - b)
        return 0.0

    def trapezoidal_mf(self, x: float, a: float, b: float, c: float, d: float) -> float:
        if x <= a or x >= d:
            return 0.0
        if a < x <= b:
            return (x - a) / (b - a)
        if b <= x <= c:
            return 1.0
        if c < x < d:
            return (d - x) / (d - c)
        return 0.0

    def fuzzify_emotion_intensity(self, value: float) -> Dict[str, float]:
        return {
            'low': self.triangular_mf(value, 0.0, 0.0, 0.5),
            'medium': self.triangular_mf(value, 0.2, 0.5, 0.8),
            'high': self.triangular_mf(value, 0.5, 1.0, 1.0)
        }

    def fuzzify_personality_trait(self, value: float) -> Dict[str, float]:
        return {
            'very_low': self.trapezoidal_mf(value, 0.0, 0.0, 0.1, 0.2),
            'low': self.triangular_mf(value, 0.1, 0.25, 0.4),
            'medium': self.triangular_mf(value, 0.3, 0.5, 0.7),
            'high': self.triangular_mf(value, 0.6, 0.75, 0.9),
            'very_high': self.trapezoidal_mf(value, 0.8, 0.9, 1.0, 1.0)
        }

    def defuzzify_centroid(self, rules: List[Dict], output_range: tuple = (0.0, 1.0)) -> float:
        step = 0.01
        numerator = 0.0
        denominator = 0.0
        
        x = output_range[0]
        while x <= output_range[1]:
            max_membership = 0.0
            for rule in rules:
                if 'value' in rule:
                    mf = self.triangular_mf(x, rule['value'] - 0.2, rule['value'], rule['value'] + 0.2)
                    membership = min(rule['weight'], mf)
                    max_membership = max(max_membership, membership)
            
            numerator += x * max_membership * step
            denominator += max_membership * step
            x += step
        
        return numerator / denominator if denominator > 0 else 0.5

    def apply_rules(self, emotion_intensities: Dict[str, float], personality: Dict[str, float]) -> Dict[str, float]:
        outputs = {}
        
        for emotion, intensity in emotion_intensities.items():
            fuzzy_intensity = self.fuzzify_emotion_intensity(intensity)
            rules = []
            
            if fuzzy_intensity['high'] > 0.5:
                rules.append({'value': intensity, 'weight': fuzzy_intensity['high']})
            elif fuzzy_intensity['medium'] > 0.3:
                rules.append({'value': intensity * 0.8, 'weight': fuzzy_intensity['medium']})
            else:
                rules.append({'value': intensity * 0.5, 'weight': fuzzy_intensity['low']})
            
            outputs[emotion] = self.defuzzify_centroid(rules)
        
        return outputs
