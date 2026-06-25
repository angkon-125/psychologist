import unittest
from emotion_engine.interaction.support_tools import SupportTools
from emotion_engine.interaction.interaction_models import SupportAction

class TestSupportTools(unittest.TestCase):
    def setUp(self):
        self.tools = SupportTools()

    def test_calm_down_english(self):
        action = self.tools.calm_down("en")
        self.assertIsInstance(action, SupportAction)
        self.assertEqual(action.action_type, "calm_down")
        self.assertEqual(action.language, "en")
        self.assertIsNotNone(action.content)

    def test_calm_down_bangla(self):
        action = self.tools.calm_down("bn")
        self.assertIsInstance(action, SupportAction)
        self.assertEqual(action.action_type, "calm_down")
        self.assertEqual(action.language, "bn")
        self.assertIsNotNone(action.content)

    def test_breathing_exercise(self):
        action = self.tools.breathing_exercise("en")
        self.assertEqual(action.action_type, "breathing_exercise")
        self.assertIsNotNone(action.content)

    def test_journaling_prompt_with_emotion(self):
        action = self.tools.journaling_prompt("en", emotion="sad")
        self.assertEqual(action.action_type, "journaling_prompt")
        self.assertIn("sad", action.content)

    def test_reflection_questions(self):
        action = self.tools.reflection_questions("en")
        self.assertEqual(action.action_type, "reflection_questions")
        self.assertIsNotNone(action.content)

if __name__ == '__main__':
    unittest.main()
