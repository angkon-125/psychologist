"""
Episodic Memory Tests

Tests for all episodic memory components:
- ImportanceEngine: scoring, thresholds, user-request override
- EpisodeBuilder: turn buffering, trigger detection, episode creation
- EpisodeStore: save/retrieve, search, archive, delete, lock
- EpisodeRecall: query search, topic recall, emotion recall
- Timeline: period filtering, project grouping, emotional journey
- ContinuityConnector: goal linking, continuation context
- ForgettingPolicy: decay, archive, delete, privacy erase, locked immunity
- EpisodicIntegration: memory agent handlers, schema serialization
"""

import os
import sys
import json
import tempfile
import pytest
from datetime import datetime, timedelta

# Ensure project root is in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.memory.episodic.schemas import Episode, EpisodeSearchResult, EmotionSnapshot
from backend.memory.episodic.importance import ImportanceEngine, IMPORTANCE_THRESHOLD
from backend.memory.episodic.episode_builder import EpisodeBuilder
from backend.memory.episodic.episode_store import EpisodeStore
from backend.memory.episodic.episode_recall import EpisodeRecall
from backend.memory.episodic.timeline import Timeline
from backend.memory.episodic.continuity import ContinuityConnector
from backend.memory.episodic.forgetting import ForgettingPolicy


# ═══════════════════════════════════════════════════════════════════
# TestImportanceEngine
# ═══════════════════════════════════════════════════════════════════

class TestImportanceEngine:
    """Tests for importance scoring."""

    def setup_method(self):
        self.engine = ImportanceEngine()

    def test_hello_low_importance(self):
        score = self.engine.score(text="hello", intent="greeting", emotion="neutral", context_length=1)
        assert score < IMPORTANCE_THRESHOLD

    def test_finished_architecture_high(self):
        score = self.engine.score(
            text="I finished the AI architecture design today!",
            intent="general",
            emotion="excited",
            context_length=15,
            has_goal=True,
        )
        assert score >= 0.5

    def test_crisis_high_importance(self):
        score = self.engine.score(
            text="I want to end my life",
            intent="crisis",
            emotion="hopeless",
            context_length=5,
        )
        assert score >= 0.3

    def test_user_requested_override(self):
        score = self.engine.score(
            text="Please remember this",
            intent="general",
            emotion="neutral",
            context_length=1,
        )
        assert score == 1.0

    def test_user_requested_pattern(self):
        score = self.engine.score(
            text="Don't forget that my birthday is next week",
            intent="general",
            emotion="neutral",
        )
        assert score == 1.0

    def test_random_joke_low(self):
        score = self.engine.score(
            text="Tell me a joke",
            intent="general",
            emotion="neutral",
            context_length=1,
        )
        assert score < 0.3

    def test_emotional_support_moderate(self):
        score = self.engine.score(
            text="I'm feeling really anxious about tomorrow",
            intent="emotional_support",
            emotion="anxious",
            context_length=8,
        )
        assert score >= 0.2

    def test_should_store_threshold(self):
        assert self.engine.should_store(0.40) is True
        assert self.engine.should_store(0.30) is False
        assert self.engine.should_store(IMPORTANCE_THRESHOLD) is True

    def test_goal_relevance_bonus(self):
        score_no_goal = self.engine.score(text="working on the project", intent="general", has_goal=False)
        score_with_goal = self.engine.score(text="working on the project", intent="general", has_goal=True)
        assert score_with_goal > score_no_goal

    def test_novelty_with_known_topics(self):
        score_new = self.engine.score(
            text="Let's build a quantum computer",
            known_topics={"python", "web"},
        )
        score_known = self.engine.score(
            text="Let's build a python web app",
            known_topics={"python", "web", "build", "app"},
        )
        assert score_new >= score_known


# ═══════════════════════════════════════════════════════════════════
# TestEpisodeBuilder
# ═══════════════════════════════════════════════════════════════════

class TestEpisodeBuilder:
    """Tests for episode building from conversation turns."""

    def setup_method(self):
        self.engine = ImportanceEngine()
        self.builder = EpisodeBuilder(importance_engine=self.engine)

    def test_buffer_add_turns(self):
        self.builder.add_turn("Hello", "user", "greeting", "neutral", "s1")
        self.builder.add_turn("Hi there!", "assistant", "greeting", "neutral", "s1")
        assert self.builder.buffer_size == 2

    def test_ignore_small_talk(self):
        self.builder.add_turn("hi", "user", "greeting", "neutral", "s1")
        self.builder.add_turn("hello!", "assistant", "greeting", "neutral", "s1")
        assert self.builder.should_create_episode() is False

    def test_trigger_on_achievement(self):
        self.builder.add_turn("I finished the architecture!", "user", "general", "excited", "s1")
        self.builder.add_turn("Great work!", "assistant", "general", "happy", "s1")
        assert self.builder.should_create_episode() is True

    def test_trigger_on_strong_emotion(self):
        self.builder.add_turn("I'm so anxious about everything", "user", "emotional_support", "anxious", "s1")
        self.builder.add_turn("I understand", "assistant", "emotional_support", "calm", "s1")
        assert self.builder.should_create_episode() is True

    def test_trigger_on_remember_request(self):
        self.builder.add_turn("Remember that I like Python", "user", "general", "neutral", "s1")
        self.builder.add_turn("Got it!", "assistant", "general", "neutral", "s1")
        assert self.builder.should_create_episode() is True

    def test_build_episode(self):
        self.builder.add_turn("I finished the architecture!", "user", "general", "excited", "s1")
        self.builder.add_turn("That's great!", "assistant", "general", "happy", "s1")
        episode = self.builder.build_episode()
        assert episode is not None
        assert len(episode.title) > 0
        assert episode.emotion in ("excited", "happy")
        assert episode.importance > 0.0

    def test_reset_clears_buffer(self):
        self.builder.add_turn("test", "user", "general", "neutral", "s1")
        self.builder.reset()
        assert self.builder.buffer_size == 0

    def test_build_episode_empty_returns_none(self):
        assert self.builder.build_episode() is None

    def test_long_conversation_triggers(self):
        for i in range(12):
            self.builder.add_turn(f"Turn {i} about the project", "user", "general", "neutral", "s1")
            self.builder.add_turn(f"Response {i}", "assistant", "general", "neutral", "s1")
        assert self.builder.should_create_episode() is True


# ═══════════════════════════════════════════════════════════════════
# TestEpisodeStore
# ═══════════════════════════════════════════════════════════════════

class TestEpisodeStore:
    """Tests for SQLite episode persistence."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.store = EpisodeStore(self.db_path)

    def _make_episode(self, title="Test", importance=0.5, emotion="neutral", topics=None):
        return Episode(
            title=title,
            summary=f"Summary of {title}",
            topics=topics or ["test"],
            importance=importance,
            emotion=emotion,
            emotion_intensity=0.5,
            source_session_id="test-session",
        )

    def test_save_and_retrieve(self):
        ep = self._make_episode("My Episode", importance=0.8)
        self.store.save_episode(ep)
        retrieved = self.store.get_episode(ep.episode_id)
        assert retrieved is not None
        assert retrieved.title == "My Episode"
        assert retrieved.importance == 0.8

    def test_get_all_episodes(self):
        self.store.save_episode(self._make_episode("Ep1"))
        self.store.save_episode(self._make_episode("Ep2"))
        all_eps = self.store.get_all_episodes()
        assert len(all_eps) == 2

    def test_search_episodes(self):
        self.store.save_episode(self._make_episode("Android Voice", topics=["voice", "android"]))
        self.store.save_episode(self._make_episode("Python Script", topics=["backend"]))
        results = self.store.search_episodes("android")
        assert len(results) >= 1
        assert results[0].title == "Android Voice"

    def test_get_by_topic(self):
        self.store.save_episode(self._make_episode("Voice Project", topics=["voice"]))
        self.store.save_episode(self._make_episode("Backend API", topics=["backend"]))
        results = self.store.get_episodes_by_topic("voice")
        assert len(results) == 1

    def test_get_by_emotion(self):
        self.store.save_episode(self._make_episode("Happy Day", emotion="happy"))
        self.store.save_episode(self._make_episode("Sad Day", emotion="sad"))
        results = self.store.get_episodes_by_emotion("happy")
        assert len(results) == 1

    def test_get_by_goal(self):
        ep = self._make_episode("Goal Episode")
        ep.related_goal_id = "goal-123"
        self.store.save_episode(ep)
        results = self.store.get_episodes_by_goal("goal-123")
        assert len(results) == 1

    def test_archive_episode(self):
        ep = self._make_episode("Archive Me")
        self.store.save_episode(ep)
        self.store.archive_episode(ep.episode_id)
        # Should not appear in non-archived list
        all_eps = self.store.get_all_episodes(include_archived=False)
        assert len(all_eps) == 0
        # But should exist
        assert self.store.get_episode(ep.episode_id) is not None

    def test_delete_episode(self):
        ep = self._make_episode("Delete Me")
        self.store.save_episode(ep)
        assert self.store.delete_episode(ep.episode_id) is True
        assert self.store.get_episode(ep.episode_id) is None

    def test_lock_episode(self):
        ep = self._make_episode("Lock Me")
        self.store.save_episode(ep)
        self.store.lock_episode(ep.episode_id, locked=True)
        locked = self.store.get_locked_episodes()
        assert len(locked) == 1
        assert locked[0].title == "Lock Me"

    def test_high_importance(self):
        self.store.save_episode(self._make_episode("Low", importance=0.3))
        self.store.save_episode(self._make_episode("High", importance=0.9))
        results = self.store.get_high_importance(threshold=0.7)
        assert len(results) == 1
        assert results[0].title == "High"

    def test_date_range(self):
        ep = self._make_episode("Today")
        self.store.save_episode(ep)
        now = datetime.now()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = self.store.get_episodes_by_date_range(start, end)
        assert len(results) >= 1

    def test_pending_episodes(self):
        ep = self._make_episode("Pending Work")
        ep.pending_tasks = ["finish implementation", "write tests"]
        self.store.save_episode(ep)
        results = self.store.get_pending_episodes()
        assert len(results) == 1

    def test_delete_all_non_locked(self):
        ep1 = self._make_episode("Normal")
        ep2 = self._make_episode("Locked")
        self.store.save_episode(ep1)
        self.store.save_episode(ep2)
        self.store.lock_episode(ep2.episode_id, locked=True)
        count = self.store.delete_all_non_locked()
        assert count == 1
        remaining = self.store.get_all_episodes(include_archived=True)
        assert len(remaining) == 1


# ═══════════════════════════════════════════════════════════════════
# TestEpisodeRecall
# ═══════════════════════════════════════════════════════════════════

class TestEpisodeRecall:
    """Tests for episode recall and search."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = EpisodeStore(os.path.join(self.tmpdir, "test.db"))
        self.recall = EpisodeRecall(self.store)
        # Seed some episodes
        for title, topic, emotion, imp in [
            ("Android Voice Setup", "voice", "excited", 0.85),
            ("Python Backend", "backend", "neutral", 0.60),
            ("Feeling Anxious", "emotion", "anxious", 0.70),
        ]:
            ep = Episode(title=title, summary=f"Summary: {title}", topics=[topic],
                         emotion=emotion, importance=imp, pending_tasks=["task1"] if "Android" in title else [])
            self.store.save_episode(ep)

    def test_recall_by_query(self):
        result = self.recall.recall_by_query("android")
        assert len(result.episodes) >= 1
        assert result.query == "android"
        assert result.search_time_ms >= 0

    def test_recall_by_topic(self):
        results = self.recall.recall_by_topic("voice")
        assert len(results) >= 1

    def test_recall_by_emotion(self):
        results = self.recall.recall_by_emotion("anxious")
        assert len(results) == 1

    def test_recall_recent(self):
        results = self.recall.recall_recent(limit=2)
        assert len(results) == 2

    def test_recall_pending(self):
        results = self.recall.recall_pending()
        assert len(results) >= 1

    def test_recall_high_importance(self):
        results = self.recall.recall_high_importance(threshold=0.7)
        assert all(e.importance >= 0.7 for e in results)


# ═══════════════════════════════════════════════════════════════════
# TestTimeline
# ═══════════════════════════════════════════════════════════════════

class TestTimeline:
    """Tests for timeline organization."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = EpisodeStore(os.path.join(self.tmpdir, "test.db"))
        self.timeline = Timeline(self.store)
        # Seed episodes
        self.store.save_episode(Episode(title="Today Ep", topics=["test"], importance=0.8, emotion="happy"))
        self.store.save_episode(Episode(title="Project Ep", topics=["android", "voice"], importance=0.9))

    def test_timeline_today(self):
        results = self.timeline.get_timeline("today")
        assert len(results) >= 1

    def test_timeline_all(self):
        results = self.timeline.get_timeline("all")
        assert len(results) == 2

    def test_projects_grouping(self):
        projects = self.timeline.get_projects()
        assert "android" in projects or "voice" in projects or "test" in projects

    def test_achievements(self):
        achievements = self.timeline.get_achievements()
        assert all(e.importance >= 0.7 for e in achievements)

    def test_timeline_summary(self):
        summary = self.timeline.get_timeline_summary()
        assert "today" in summary
        assert "week" in summary
        assert "today_count" in summary


# ═══════════════════════════════════════════════════════════════════
# TestContinuityConnector
# ═══════════════════════════════════════════════════════════════════

class TestContinuityConnector:
    """Tests for goal continuity bridging."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = EpisodeStore(os.path.join(self.tmpdir, "test.db"))
        self.connector = ContinuityConnector(self.store)

    def test_continuation_context_empty(self):
        context = self.connector.generate_continuation_context()
        assert context == ""

    def test_continuation_context_with_episodes(self):
        ep = Episode(title="Built Executive Brain", summary="Completed cognitive core",
                     topics=["testing"], importance=0.9, pending_tasks=["Write tests"])
        self.store.save_episode(ep)
        context = self.connector.generate_continuation_context()
        assert "Executive Brain" in context

    def test_detect_recurring_goals(self):
        self.store.save_episode(Episode(title="Android 1", topics=["android"], importance=0.7))
        self.store.save_episode(Episode(title="Android 2", topics=["android"], importance=0.8))
        recurring = self.connector.detect_recurring_goals("Continue android project")
        assert "android" in recurring

    def test_goal_episodes(self):
        ep = Episode(title="Goal Ep", topics=["test"], importance=0.7, related_goal_id="g1")
        self.store.save_episode(ep)
        result = self.connector.get_goal_episodes("g1")
        assert "completed" in result
        assert "remaining" in result


# ═══════════════════════════════════════════════════════════════════
# TestForgettingPolicy
# ═══════════════════════════════════════════════════════════════════

class TestForgettingPolicy:
    """Tests for forgetting policies."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = EpisodeStore(os.path.join(self.tmpdir, "test.db"))
        self.policy = ForgettingPolicy()

    def test_decay_reduces_importance(self):
        ep = Episode(title="Old Ep", topics=["test"], importance=0.5)
        self.store.save_episode(ep)
        self.policy.apply_decay(self.store, decay_rate=0.05)
        updated = self.store.get_episode(ep.episode_id)
        assert updated.importance < 0.5

    def test_locked_immune_to_decay(self):
        ep = Episode(title="Locked", topics=["test"], importance=0.5)
        self.store.save_episode(ep)
        self.store.lock_episode(ep.episode_id, locked=True)
        self.policy.apply_decay(self.store, decay_rate=0.05)
        updated = self.store.get_episode(ep.episode_id)
        assert updated.importance == 0.5

    def test_archive_old(self):
        ep = Episode(title="Very Old", topics=["test"], importance=0.5)
        ep.started_at = datetime.now() - timedelta(days=100)
        self.store.save_episode(ep)
        count = self.policy.archive_old(self.store, days=90)
        assert count >= 1

    def test_privacy_erase(self):
        self.store.save_episode(Episode(title="Ep1", topics=["test"], importance=0.5))
        self.store.save_episode(Episode(title="Ep2", topics=["test"], importance=0.6))
        count = self.policy.privacy_erase(self.store)
        assert count == 2
        assert len(self.store.get_all_episodes(include_archived=True)) == 0

    def test_locked_memories(self):
        ep = Episode(title="Locked", topics=["test"], importance=0.5)
        self.store.save_episode(ep)
        self.store.lock_episode(ep.episode_id, locked=True)
        locked = self.policy.locked_memories(self.store)
        assert len(locked) == 1


# ═══════════════════════════════════════════════════════════════════
# TestEpisodicSchemas
# ═══════════════════════════════════════════════════════════════════

class TestEpisodicSchemas:
    """Tests for schema serialization."""

    def test_episode_to_dict_roundtrip(self):
        ep = Episode(title="Test", topics=["a", "b"], importance=0.75, emotion="happy")
        d = ep.to_dict()
        restored = Episode.from_dict(d)
        assert restored.title == "Test"
        assert restored.topics == ["a", "b"]
        assert restored.importance == 0.75

    def test_emotion_snapshot_roundtrip(self):
        snap = EmotionSnapshot(emotion="anxious", intensity=0.8, episode_id="ep1")
        d = snap.to_dict()
        restored = EmotionSnapshot.from_dict(d)
        assert restored.emotion == "anxious"
        assert restored.intensity == 0.8

    def test_search_result_to_dict(self):
        result = EpisodeSearchResult(
            episodes=[Episode(title="Ep1", topics=["test"])],
            query="test",
            total_count=1,
            search_time_ms=2.5,
        )
        d = result.to_dict()
        assert d["total_count"] == 1
        assert len(d["episodes"]) == 1
