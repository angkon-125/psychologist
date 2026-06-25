import unittest
import tempfile
import shutil
import os
from pathlib import Path
from emotion_engine.interaction.session_manager import SessionManager
from emotion_engine.interaction.interaction_models import UserMessage, AssistantMessage

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = SessionManager(sessions_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_start_session(self):
        session = self.manager.start_session(mode="hybrid", language="en")
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.active_mode, "hybrid")
        self.assertEqual(session.language, "en")
        self.assertEqual(self.manager._current_session.session_id, session.session_id)

    def test_add_messages(self):
        session = self.manager.start_session()
        user_msg = UserMessage(raw_text="Hello", detected_emotion="happy", confidence=0.8)
        self.manager.add_user_message(user_msg)
        
        assistant_msg = AssistantMessage(response_text="Hi there", response_type="supportive")
        self.manager.add_assistant_message(assistant_msg)

        # Check if saved to current session state
        self.assertEqual(len(self.manager._current_session.user_messages), 1)
        self.assertEqual(len(self.manager._current_session.assistant_messages), 1)
        self.assertEqual(self.manager._current_session.user_messages[0]["raw_text"], "Hello")
        self.assertEqual(self.manager._current_session.assistant_messages[0]["response_text"], "Hi there")

    def test_persistence(self):
        session = self.manager.start_session()
        session_id = session.session_id
        
        user_msg = UserMessage(raw_text="Hello persistent world", detected_emotion="neutral")
        self.manager.add_user_message(user_msg)
        self.manager.save_session(session)
        
        # Load from disk
        loaded = self.manager.load_session(session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.session_id, session_id)
        self.assertEqual(len(loaded.user_messages), 1)
        self.assertEqual(loaded.user_messages[0]["raw_text"], "Hello persistent world")

    def test_end_session(self):
        session = self.manager.start_session()
        user_msg = UserMessage(raw_text="I feel a bit sad today.", detected_emotion="sad")
        self.manager.add_user_message(user_msg)
        
        summary_result = self.manager.end_session()
        self.assertIsNone(self.manager._current_session)
        self.assertIn("summary", summary_result)
        self.assertIsNotNone(summary_result["summary"])

if __name__ == '__main__':
    unittest.main()
