import unittest
from emotion_engine.interaction.interaction_mode_manager import InteractionModeManager
from emotion_engine.interaction.interaction_models import InteractionMode

class TestInteractionModeManager(unittest.TestCase):
    def setUp(self):
        self.manager = InteractionModeManager(default_mode="hybrid")

    def test_default_mode(self):
        self.assertEqual(self.manager.current_mode, InteractionMode.HYBRID)
        self.assertEqual(self.manager.get_mode_name(), "hybrid")

    def test_switch_mode(self):
        res = self.manager.switch_mode("text")
        self.assertTrue(res["success"])
        self.assertEqual(self.manager.current_mode, InteractionMode.TEXT)

        res = self.manager.switch_mode("voice")
        self.assertTrue(res["success"])
        self.assertEqual(self.manager.current_mode, InteractionMode.VOICE)

    def test_invalid_mode_fallback(self):
        # Invalid mode switches default to hybrid
        res = self.manager.switch_mode("unknown_mode")
        self.assertTrue(res["success"])
        self.assertEqual(self.manager.current_mode, InteractionMode.HYBRID)

    def test_mode_queries(self):
        self.manager.switch_mode("text")
        self.assertTrue(self.manager.is_text_input_enabled())
        self.assertFalse(self.manager.is_voice_input_enabled())

        self.manager.switch_mode("voice")
        self.assertFalse(self.manager.is_text_input_enabled())
        self.assertTrue(self.manager.is_voice_input_enabled())

    def test_activity_callback(self):
        activity_logs = []
        self.manager.set_activity_callback(lambda text: activity_logs.append(text))
        self.manager.switch_mode("text")
        self.assertGreater(len(activity_logs), 0)
        self.assertIn("Switched to text mode", activity_logs[0])

if __name__ == '__main__':
    unittest.main()
