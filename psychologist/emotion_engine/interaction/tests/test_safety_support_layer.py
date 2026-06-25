import unittest
from emotion_engine.interaction.safety_support_layer import SafetySupportLayer

class TestSafetySupportLayer(unittest.TestCase):
    def setUp(self):
        self.safety = SafetySupportLayer()

    def test_clean_input(self):
        # Neutral input
        assessment = self.safety.assess_input("How is the weather today?", "en")
        self.assertEqual(assessment.risk_level, "none")
        self.assertFalse(assessment.should_escalate)

    def test_crisis_detection_english(self):
        assessment = self.safety.assess_input("I want to end my life, please help", "en")
        self.assertEqual(assessment.risk_level, "critical")
        self.assertTrue(assessment.should_escalate)
        self.assertIn("suicide", assessment.detected_signals)
        self.assertIsNotNone(assessment.safe_response_template)

    def test_crisis_detection_bangla(self):
        assessment = self.safety.assess_input("আমি আত্মহত্যা করতে চাই", "bn")
        self.assertEqual(assessment.risk_level, "critical")
        self.assertTrue(assessment.should_escalate)
        self.assertIn("suicide", assessment.detected_signals)

    def test_diagnosis_blocking(self):
        # The system must not claim to diagnose illnesses like clinical depression
        response = "Based on my analysis, you have clinical depression."
        filtered = self.safety.filter_response(response)
        self.assertNotEqual(response, filtered)
        self.assertIn("supportive space", filtered)

    def test_distress_detection(self):
        assessment = self.safety.assess_input("I feel so overwhelmed and anxious", "en")
        self.assertEqual(assessment.risk_level, "moderate")
        self.assertFalse(assessment.should_escalate)
        self.assertIn("anxiety", assessment.detected_signals)

if __name__ == '__main__':
    unittest.main()
