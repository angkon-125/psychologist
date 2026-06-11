import unittest
from emotion_engine import EmotionEngine
from emotion_engine.models import EmotionalState, PersonalityTraits, MemoryEntry
from emotion_engine.personality_engine import PersonalityEngine
from emotion_engine.sentiment_analysis import SentimentAnalyzer


class TestEmotionModels(unittest.TestCase):
    def test_emotional_state_creation(self):
        state = EmotionalState()
        self.assertIsNotNone(state.timestamp)
        self.assertIn('happiness', state.primary_emotions)
        self.assertEqual(state.primary_emotions['happiness'], 0.0)

    def test_dominant_emotion(self):
        state = EmotionalState()
        state.primary_emotions['happiness'] = 0.8
        state.primary_emotions['sadness'] = 0.2
        self.assertEqual(state.get_dominant_emotion(), 'happiness')


class TestSentimentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        result = self.analyzer.analyze_text("I'm so happy today!")
        self.assertGreater(result['sentiment'], 0)

    def test_negative_sentiment(self):
        result = self.analyzer.analyze_text("This is terrible and sad.")
        self.assertLess(result['sentiment'], 0)


class TestPersonalityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PersonalityEngine()

    def test_randomize_traits(self):
        original = self.engine.get_traits()
        self.engine.randomize_traits()
        new = self.engine.get_traits()
        self.assertNotEqual(original['openness'], new['openness'])

    def test_influence_emotion(self):
        result = self.engine.influence_emotion('happiness', 0.5)
        self.assertGreater(result, 0)
        self.assertLess(result, 1.1)


class TestEmotionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = EmotionEngine()

    def test_process_input(self):
        result = self.engine.process_input("Hello!")
        self.assertIn('emotional_state', result)
        self.assertIn('response', result)
        self.assertIn('dominant_emotion', result)

    def test_emotion_decay(self):
        state = EmotionalState()
        state.primary_emotions['happiness'] = 0.5
        decayed = self.engine._decay_emotions(state)
        self.assertLess(decayed.primary_emotions['happiness'], 0.5)


if __name__ == '__main__':
    unittest.main()
