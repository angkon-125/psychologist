import unittest
import tempfile
import shutil
from emotion_engine import EmotionEngine
from emotion_engine.interaction.text_mode_handler import TextModeHandler
from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
from emotion_engine.interaction.session_manager import SessionManager

class TestTextModeHandler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.emotion_engine = EmotionEngine()
        self.safety_layer = SafetySupportLayer()
        self.session_manager = SessionManager(sessions_dir=self.test_dir)
        self.handler = TextModeHandler(
            emotion_engine=self.emotion_engine,
            tts_manager=None,
            safety_layer=self.safety_layer,
            session_manager=self.session_manager
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_process_text_normal(self):
        self.session_manager.start_session(mode="text")
        session_id = self.session_manager._current_session.session_id
        
        result = self.handler.process_text(
            text="I had a good day today!",
            language="en",
            session_id=session_id
        )
        
        self.assertIn("user_message", result)
        self.assertIn("assistant_message", result)
        self.assertIn("emotion_result", result)
        self.assertIn("safety_assessment", result)
        
        self.assertEqual(result["user_message"]["raw_text"], "I had a good day today!")
        self.assertEqual(result["safety_assessment"]["risk_level"], "none")
        self.assertIsNotNone(result["assistant_message"]["response_text"])

    def test_process_text_crisis(self):
        self.session_manager.start_session(mode="text")
        session_id = self.session_manager._current_session.session_id
        
        result = self.handler.process_text(
            text="I want to kill myself, please let me go",
            language="en",
            session_id=session_id
        )
        
        self.assertEqual(result["safety_assessment"]["risk_level"], "critical")
        self.assertTrue(result["safety_assessment"]["should_escalate"])
        self.assertIn("crisis_support", result["assistant_message"]["response_type"])

if __name__ == '__main__':
    unittest.main()
