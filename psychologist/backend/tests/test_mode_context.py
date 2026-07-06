"""
Mode Context Tests

Tests for the agent mode context system:
- Mode validation and labels
- Intent → mode resolution
- Mode → voice context mapping
- Orchestrator mode resolution
- Backend API mode acceptance
- Safety mode override
- Frontend mode payload shape
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestModeContextBasics(unittest.TestCase):
    """Test basic mode context functionality."""

    def test_valid_modes_exist(self):
        """Test that valid modes are defined."""
        from backend.agent.mode_context import VALID_MODES, DEFAULT_MODE
        self.assertIsInstance(VALID_MODES, set)
        self.assertGreater(len(VALID_MODES), 0)
        self.assertIn(DEFAULT_MODE, VALID_MODES)

    def test_all_required_modes_present(self):
        """Test that all required modes are defined."""
        from backend.agent.mode_context import VALID_MODES
        required = {"assistant", "psychologist", "coding", "project", "prediction", "safety", "night"}
        self.assertEqual(VALID_MODES, required)

    def test_default_mode_is_assistant(self):
        """Test that default mode is assistant."""
        from backend.agent.mode_context import DEFAULT_MODE
        self.assertEqual(DEFAULT_MODE, "assistant")

    def test_mode_labels_defined(self):
        """Test that mode labels are defined for all modes."""
        from backend.agent.mode_context import MODE_LABELS, VALID_MODES
        for mode in VALID_MODES:
            self.assertIn(mode, MODE_LABELS)
            self.assertIsInstance(MODE_LABELS[mode], str)
            self.assertGreater(len(MODE_LABELS[mode]), 0)


class TestModeValidation(unittest.TestCase):
    """Test mode validation functions."""

    def test_is_valid_mode_true(self):
        """Test is_valid_mode returns True for valid modes."""
        from backend.agent.mode_context import is_valid_mode
        for mode in ["assistant", "psychologist", "coding", "night"]:
            self.assertTrue(is_valid_mode(mode))

    def test_is_valid_mode_false(self):
        """Test is_valid_mode returns False for invalid modes."""
        from backend.agent.mode_context import is_valid_mode
        for mode in ["invalid", "unknown", "", None, "TEXT", "voice"]:
            self.assertFalse(is_valid_mode(mode))

    def test_get_mode_label(self):
        """Test get_mode_label returns correct labels."""
        from backend.agent.mode_context import get_mode_label
        self.assertEqual(get_mode_label("assistant"), "Assistant")
        self.assertEqual(get_mode_label("psychologist"), "Support")
        self.assertEqual(get_mode_label("coding"), "Coding")
        self.assertEqual(get_mode_label("night"), "Night")

    def test_get_mode_label_invalid(self):
        """Test get_mode_label handles invalid modes."""
        from backend.agent.mode_context import get_mode_label
        # Should return title-cased version for unknown modes
        self.assertEqual(get_mode_label("unknown"), "Unknown")
        # Empty string returns default "Assistant"
        self.assertEqual(get_mode_label(""), "Assistant")


class TestIntentToModeMapping(unittest.TestCase):
    """Test intent → mode resolution."""

    def test_intent_to_mode_mapping_exists(self):
        """Test that intent to mode mapping is defined."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertIsInstance(INTENT_TO_MODE, dict)
        self.assertGreater(len(INTENT_TO_MODE), 0)

    def test_crisis_maps_to_safety(self):
        """Test that crisis intent maps to safety mode."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertEqual(INTENT_TO_MODE.get("crisis"), "safety")

    def test_emotional_support_maps_to_psychologist(self):
        """Test that emotional_support intent maps to psychologist mode."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertEqual(INTENT_TO_MODE.get("emotional_support"), "psychologist")

    def test_tool_request_maps_to_project(self):
        """Test that tool_request intent maps to project mode."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertEqual(INTENT_TO_MODE.get("tool_request"), "project")

    def test_prediction_maps_to_prediction(self):
        """Test that prediction intent maps to prediction mode."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertEqual(INTENT_TO_MODE.get("prediction"), "prediction")

    def test_general_maps_to_assistant(self):
        """Test that general intent maps to assistant mode."""
        from backend.agent.mode_context import INTENT_TO_MODE
        self.assertEqual(INTENT_TO_MODE.get("general"), "assistant")

    def test_resolve_mode_from_intent(self):
        """Test resolve_mode_from_intent function."""
        from backend.agent.mode_context import resolve_mode_from_intent
        self.assertEqual(resolve_mode_from_intent("crisis"), "safety")
        self.assertEqual(resolve_mode_from_intent("emotional_support"), "psychologist")
        self.assertEqual(resolve_mode_from_intent("general"), "assistant")
        self.assertEqual(resolve_mode_from_intent("unknown_intent"), "assistant")  # fallback


class TestModeToVoiceContext(unittest.TestCase):
    """Test mode → voice context mapping."""

    def test_mode_to_voice_context_exists(self):
        """Test that mode to voice context mapping is defined."""
        from backend.agent.mode_context import MODE_TO_VOICE_CONTEXT
        self.assertIsInstance(MODE_TO_VOICE_CONTEXT, dict)
        self.assertGreater(len(MODE_TO_VOICE_CONTEXT), 0)

    def test_assistant_voice_context(self):
        """Test assistant mode voice context."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("assistant")
        self.assertEqual(profile, "zara_cute")
        self.assertEqual(style, "friendly_assistant")

    def test_psychologist_voice_context(self):
        """Test psychologist mode voice context."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("psychologist")
        self.assertEqual(profile, "zara_soft")
        self.assertEqual(style, "calm_support")

    def test_coding_voice_context(self):
        """Test coding mode voice context."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("coding")
        self.assertEqual(profile, "zara_professional")
        self.assertEqual(style, "professional_clear")

    def test_safety_voice_context(self):
        """Test safety mode voice context."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("safety")
        self.assertEqual(profile, "zara_professional")
        self.assertEqual(style, "emergency_clear")

    def test_night_voice_context(self):
        """Test night mode voice context."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("night")
        self.assertEqual(profile, "zara_night")
        self.assertEqual(style, "night_soft")

    def test_invalid_mode_fallback(self):
        """Test that invalid mode falls back to default."""
        from backend.agent.mode_context import get_voice_context_for_mode
        profile, style = get_voice_context_for_mode("invalid_mode")
        self.assertEqual(profile, "zara_cute")  # default
        self.assertEqual(style, "friendly_assistant")


class TestResolveFinalMode(unittest.TestCase):
    """Test final mode resolution with frontend mode + intent."""

    def test_safety_override(self):
        """Test that safety_override forces safety mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("assistant", "general", safety_override=True)
        self.assertEqual(result, "safety")

    def test_crisis_intent_forces_safety(self):
        """Test that crisis intent forces safety mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("assistant", "crisis")
        self.assertEqual(result, "safety")

    def test_emotional_support_overrides_assistant(self):
        """Test that emotional_support intent overrides assistant mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("assistant", "emotional_support")
        self.assertEqual(result, "psychologist")

    def test_tool_request_overrides_assistant(self):
        """Test that tool_request intent overrides assistant mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("assistant", "tool_request")
        self.assertEqual(result, "project")

    def test_prediction_overrides_assistant(self):
        """Test that prediction intent overrides assistant mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("assistant", "prediction")
        self.assertEqual(result, "prediction")

    def test_general_preserves_frontend_mode(self):
        """Test that general intent preserves frontend mode."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("coding", "general")
        self.assertEqual(result, "coding")

    def test_invalid_frontend_mode_fallback(self):
        """Test that invalid frontend mode falls back to default."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode("invalid", "general")
        self.assertEqual(result, "assistant")

    def test_none_frontend_mode_fallback(self):
        """Test that None frontend mode falls back to default."""
        from backend.agent.mode_context import resolve_final_mode
        result = resolve_final_mode(None, "general")
        self.assertEqual(result, "assistant")


class TestEmotionContextForMode(unittest.TestCase):
    """Test emotion context mapping for TTS."""

    def test_emotion_context_mapping(self):
        """Test get_emotion_context_for_mode returns correct values."""
        from backend.agent.mode_context import get_emotion_context_for_mode
        self.assertEqual(get_emotion_context_for_mode("assistant"), "chat")
        self.assertEqual(get_emotion_context_for_mode("psychologist"), "support")
        self.assertEqual(get_emotion_context_for_mode("coding"), "coding")
        self.assertEqual(get_emotion_context_for_mode("project"), "coding")
        self.assertEqual(get_emotion_context_for_mode("prediction"), "coding")
        self.assertEqual(get_emotion_context_for_mode("safety"), "crisis")
        self.assertEqual(get_emotion_context_for_mode("night"), "night")

    def test_invalid_mode_emotion_context(self):
        """Test that invalid mode returns default emotion context."""
        from backend.agent.mode_context import get_emotion_context_for_mode
        self.assertEqual(get_emotion_context_for_mode("invalid"), "chat")


class TestAgentRequestMode(unittest.TestCase):
    """Test AgentRequest schema includes agent_mode."""

    def test_agent_request_has_mode(self):
        """Test that AgentRequest has agent_mode field."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="test")
        self.assertTrue(hasattr(req, "agent_mode"))
        self.assertEqual(req.agent_mode, "assistant")  # default

    def test_agent_request_custom_mode(self):
        """Test AgentRequest with custom mode."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="test", agent_mode="coding")
        self.assertEqual(req.agent_mode, "coding")

    def test_agent_request_to_dict_includes_mode(self):
        """Test that to_dict includes agent_mode."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="test", agent_mode="night")
        d = req.to_dict()
        self.assertIn("agent_mode", d)
        self.assertEqual(d["agent_mode"], "night")


class TestOrchestratorModeResolution(unittest.TestCase):
    """Test orchestrator mode resolution in responses."""

    def setUp(self):
        """Set up test fixtures."""
        from backend.agent.orchestrator import OrchestratorAgent
        from backend.safety.safety_agent import SafetyAgent
        from backend.llm.llm_agent import LLMAgent
        self.orchestrator = OrchestratorAgent()
        self.orchestrator.register_specialist("safety", SafetyAgent())
        self.orchestrator.register_specialist("llm", LLMAgent())
        self.orchestrator.initialize()

    def test_orchestrator_returns_resolved_mode(self):
        """Test that orchestrator response includes resolved_mode."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="Hello", agent_mode="assistant")
        res = self.orchestrator.safe_process(req)
        self.assertIn("resolved_mode", res.metadata)

    def test_orchestrator_returns_emotion_context(self):
        """Test that orchestrator response includes emotion_context."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="Hello", agent_mode="assistant")
        res = self.orchestrator.safe_process(req)
        self.assertIn("emotion_context", res.metadata)

    def test_orchestrator_returns_mode_label(self):
        """Test that orchestrator response includes mode_label."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="Hello", agent_mode="coding")
        res = self.orchestrator.safe_process(req)
        self.assertIn("mode_label", res.metadata)

    def test_crisis_resolves_to_safety(self):
        """Test that crisis intent resolves to safety mode."""
        from backend.agent.schemas import AgentRequest
        req = AgentRequest(text="I want to end my life", agent_mode="assistant")
        res = self.orchestrator.safe_process(req)
        self.assertEqual(res.metadata.get("resolved_mode"), "safety")
        self.assertEqual(res.metadata.get("emotion_context"), "crisis")


class TestChatEndpointMode(unittest.TestCase):
    """Test /api/chat endpoint accepts mode parameter."""

    def setUp(self):
        """Set up test client."""
        from flask import Flask
        from backend.api.routes_chat import chat_bp
        from backend.api.shared import orchestrator
        from backend.safety.safety_agent import SafetyAgent
        from backend.llm.llm_agent import LLMAgent

        # Register specialists if not already
        if "safety" not in orchestrator.specialists:
            orchestrator.register_specialist("safety", SafetyAgent())
        if "llm" not in orchestrator.specialists:
            orchestrator.register_specialist("llm", LLMAgent())
        orchestrator.initialize()

        app = Flask(__name__)
        app.register_blueprint(chat_bp)
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_chat_accepts_mode_parameter(self):
        """Test that /api/chat accepts mode parameter."""
        resp = self.client.post("/api/chat", json={
            "text": "Hello",
            "mode": "coding"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))

    def test_chat_returns_resolved_mode(self):
        """Test that /api/chat response includes resolved_mode."""
        resp = self.client.post("/api/chat", json={
            "text": "Hello",
            "mode": "assistant"
        })
        data = resp.get_json()
        self.assertIn("metadata", data)
        self.assertIn("resolved_mode", data["metadata"])

    def test_chat_invalid_mode_fallback(self):
        """Test that invalid mode falls back safely."""
        resp = self.client.post("/api/chat", json={
            "text": "Hello",
            "mode": "invalid_mode"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        # Should have a resolved_mode (may be safety if crisis detector fails)
        self.assertIn(data["metadata"].get("resolved_mode"), ["assistant", "safety"])

    def test_chat_empty_mode_uses_default(self):
        """Test that empty mode uses default."""
        resp = self.client.post("/api/chat", json={
            "text": "Hello"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))


class TestInteractionEndpointMode(unittest.TestCase):
    """Test /api/interaction/message endpoint accepts mode."""

    def setUp(self):
        """Set up test client."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from app import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_interaction_accepts_mode(self):
        """Test that /api/interaction/message accepts mode parameter."""
        resp = self.client.post("/api/interaction/message", json={
            "text": "Hello there",
            "language": "en",
            "mode": "assistant"
        })
        self.assertEqual(resp.status_code, 200)

    def test_interaction_returns_resolved_mode(self):
        """Test that response includes resolved_mode."""
        resp = self.client.post("/api/interaction/message", json={
            "text": "I'm feeling happy today",
            "language": "en",
            "mode": "assistant"
        })
        data = resp.get_json()
        self.assertIn("resolved_mode", data)


if __name__ == "__main__":
    unittest.main()
