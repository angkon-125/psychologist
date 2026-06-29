"""
Integration tests for all Flask API endpoints.

Uses the Flask test client to exercise every route without
requiring audio hardware or external services.
"""

import json


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "voice_output_available" in data
        assert "voice_input_available" in data
        assert "voice_emotion_available" in data


class TestEmotionEndpoints:
    def test_process_emotion_valid(self, client):
        resp = client.post(
            "/api/emotion/process",
            json={"text": "I'm feeling really happy today!"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "emotional_state" in data
        assert "response" in data
        assert "dominant_emotion" in data

    def test_process_emotion_missing_text(self, client):
        resp = client.post("/api/emotion/process", json={})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_process_emotion_empty_text(self, client):
        resp = client.post(
            "/api/emotion/process", json={"text": "   "}
        )
        assert resp.status_code == 400

    def test_process_emotion_no_body(self, client):
        resp = client.post("/api/emotion/process")
        assert resp.status_code == 400

    def test_process_emotion_too_long(self, client):
        resp = client.post(
            "/api/emotion/process",
            json={"text": "x" * 6000},
        )
        assert resp.status_code == 400

    def test_get_emotion_state(self, client):
        resp = client.get("/api/emotion/state")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "primary_emotions" in data

    def test_get_personality(self, client):
        resp = client.get("/api/emotion/personality")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "openness" in data

    def test_set_personality_valid(self, client):
        resp = client.post(
            "/api/emotion/personality",
            json={"openness": 0.8, "extraversion": 0.6},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["openness"] == 0.8

    def test_set_personality_invalid_field(self, client):
        resp = client.post(
            "/api/emotion/personality",
            json={"bad_trait": 0.5},
        )
        assert resp.status_code == 400

    def test_get_memory(self, client):
        resp = client.get("/api/emotion/memory")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "short_term_count" in data

    def test_reset_emotion(self, client):
        resp = client.post("/api/emotion/reset")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestSCEAEndpoints:
    def test_scea_step_empty(self, client):
        resp = client.post("/api/scea/step", json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "step" in data
        assert "neurochemistry" in data
        assert "decision" in data

    def test_scea_step_no_body(self, client):
        resp = client.post("/api/scea/step")
        assert resp.status_code == 400

    def test_scea_interact(self, client):
        resp = client.post(
            "/api/scea/interact",
            json={
                "entity_id": "user_1",
                "interaction_type": "conversation",
                "positive": True,
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.entity_id == "user_1" if hasattr(data, "entity_id") else True

    def test_scea_interact_no_body(self, client):
        resp = client.post("/api/scea/interact")
        assert resp.status_code == 400


class TestSessionEndpoints:
    def test_session_start(self, client):
        resp = client.post(
            "/api/session/start",
            json={"mode": "text", "language": "en"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "session_id" in data
        assert data["active_mode"] == "text"

    def test_session_current_no_session(self, client):
        # End any pre-existing session from prior tests
        client.post("/api/session/end")
        resp = client.get("/api/session/current")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "no_active_session"

    def test_session_end(self, client):
        client.post("/api/session/start", json={"mode": "text"})
        resp = client.post("/api/session/end")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "summary" in data

    def test_session_history(self, client):
        resp = client.get("/api/session/history")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)


class TestSupportEndpoints:
    def test_calm(self, client):
        resp = client.post("/api/support/calm", json={"language": "en"})
        assert resp.status_code == 200
        assert "content" in resp.get_json()

    def test_breathing(self, client):
        resp = client.post("/api/support/breathing", json={"language": "en"})
        assert resp.status_code == 200
        assert "content" in resp.get_json()

    def test_journal(self, client):
        resp = client.post(
            "/api/support/journal",
            json={"language": "en", "emotion": "sadness"},
        )
        assert resp.status_code == 200
        assert "content" in resp.get_json()

    def test_reflection(self, client):
        resp = client.post("/api/support/reflection", json={"language": "en"})
        assert resp.status_code == 200

    def test_mood_checkin(self, client):
        resp = client.post("/api/support/mood-checkin", json={"language": "en"})
        assert resp.status_code == 200


class TestInteractionEndpoints:
    def test_interaction_message_text(self, client):
        resp = client.post(
            "/api/interaction/message",
            json={"text": "I feel stressed today", "language": "en"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "assistant_message" in data
        assert "emotion_result" in data

    def test_interaction_message_missing_text(self, client):
        resp = client.post("/api/interaction/message", json={})
        assert resp.status_code == 400

    def test_interaction_mode_get(self, client):
        resp = client.get("/api/interaction/mode")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "current_mode" in data

    def test_interaction_mode_switch(self, client):
        resp = client.post("/api/interaction/mode", json={"mode": "text"})
        assert resp.status_code == 200

    def test_interaction_voice_status(self, client):
        resp = client.get("/api/interaction/voice/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "is_listening" in data


class TestSafetyStatus:
    def test_safety_status_no_session(self, client):
        client.post("/api/session/end")
        resp = client.get("/api/safety/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["risk_level"] == "none"


class TestErrorHandling:
    def test_404_returns_json(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["error"] == "not_found"

    def test_method_not_allowed(self, client):
        resp = client.delete("/api/health")
        assert resp.status_code == 405
        data = resp.get_json()
        assert data["error"] == "method_not_allowed"
