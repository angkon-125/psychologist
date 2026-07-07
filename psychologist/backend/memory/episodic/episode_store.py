"""
Episode Store — Episodic Memory

SQLite persistence for episodes. Uses the existing database
(data/zara_memory.db) and adds episodes + emotion_snapshots tables.
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .schemas import Episode, EmotionSnapshot

logger = logging.getLogger("zara.memory.episodic.store")


class EpisodeStore:
    """
    SQLite-backed storage for episodic memories.

    Usage:
        store = EpisodeStore("data/zara_memory.db")
        store.save_episode(episode)
        results = store.search_episodes("android")
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create episodes and emotion_snapshots tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    topics TEXT,
                    importance REAL,
                    emotion TEXT,
                    emotion_intensity REAL,
                    outcome TEXT,
                    pending_tasks TEXT,
                    follow_up TEXT,
                    related_goal_id TEXT,
                    source_session_id TEXT,
                    interaction_ids TEXT,
                    locked INTEGER DEFAULT 0,
                    archived INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emotion_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    intensity REAL NOT NULL,
                    episode_id TEXT,
                    notes TEXT
                )
            """)
            # Indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_started ON episodes(started_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_importance ON episodes(importance)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_emotion ON episodes(emotion)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_goal ON episodes(related_goal_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_archived ON episodes(archived)")
            conn.commit()
        logger.info("EpisodeStore tables verified at %s", self.db_path)

    def save_episode(self, episode: Episode) -> None:
        """Save an episode to the database."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO episodes
                (episode_id, title, summary, started_at, ended_at, topics, importance,
                 emotion, emotion_intensity, outcome, pending_tasks, follow_up,
                 related_goal_id, source_session_id, interaction_ids, locked, archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode.episode_id,
                    episode.title,
                    episode.summary,
                    episode.started_at.isoformat(),
                    episode.ended_at.isoformat(),
                    json.dumps(episode.topics),
                    episode.importance,
                    episode.emotion,
                    episode.emotion_intensity,
                    episode.outcome,
                    json.dumps(episode.pending_tasks),
                    episode.follow_up,
                    episode.related_goal_id,
                    episode.source_session_id,
                    json.dumps(episode.interaction_ids),
                    1 if episode.locked else 0,
                    1 if episode.archived else 0,
                    episode.created_at.isoformat(),
                ),
            )
            conn.commit()
        logger.debug("Saved episode: %s (importance=%.2f)", episode.episode_id, episode.importance)

    def save_emotion_snapshot(self, snapshot: EmotionSnapshot) -> None:
        """Save an emotion snapshot."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO emotion_snapshots (timestamp, emotion, intensity, episode_id, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.timestamp.isoformat(),
                    snapshot.emotion,
                    snapshot.intensity,
                    snapshot.episode_id,
                    snapshot.notes,
                ),
            )
            conn.commit()

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        """Get a single episode by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM episodes WHERE episode_id = ?", (episode_id,)
            )
            row = cursor.fetchone()
            return self._row_to_episode(row) if row else None

    def get_all_episodes(self, include_archived: bool = False) -> List[Episode]:
        """Get all episodes, optionally including archived."""
        with self._get_connection() as conn:
            if include_archived:
                cursor = conn.execute("SELECT * FROM episodes ORDER BY started_at DESC")
            else:
                cursor = conn.execute(
                    "SELECT * FROM episodes WHERE archived = 0 ORDER BY started_at DESC"
                )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_episodes_by_date_range(
        self, start: datetime, end: datetime, limit: int = 50
    ) -> List[Episode]:
        """Get episodes within a date range."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE started_at >= ? AND started_at <= ? AND archived = 0
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (start.isoformat(), end.isoformat(), limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_episodes_by_topic(self, topic: str, limit: int = 20) -> List[Episode]:
        """Get episodes matching a topic (keyword search in topics JSON)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE topics LIKE ? AND archived = 0
                ORDER BY importance DESC
                LIMIT ?
                """,
                (f'%"{topic}"%', limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_episodes_by_emotion(self, emotion: str, limit: int = 20) -> List[Episode]:
        """Get episodes with a specific emotion."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE emotion = ? AND archived = 0
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (emotion, limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_episodes_by_goal(self, goal_id: str, limit: int = 20) -> List[Episode]:
        """Get episodes linked to a specific goal."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE related_goal_id = ? AND archived = 0
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (goal_id, limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_high_importance(self, threshold: float = 0.7, limit: int = 20) -> List[Episode]:
        """Get episodes above an importance threshold."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE importance >= ? AND archived = 0
                ORDER BY importance DESC
                LIMIT ?
                """,
                (threshold, limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def search_episodes(self, query: str, limit: int = 20) -> List[Episode]:
        """Search episodes by keyword in title, summary, and topics."""
        if not query:
            return []
        pattern = f"%{query}%"
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE (title LIKE ? OR summary LIKE ? OR topics LIKE ?) AND archived = 0
                ORDER BY importance DESC
                LIMIT ?
                """,
                (pattern, pattern, pattern, limit),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def get_pending_episodes(self, limit: int = 20) -> List[Episode]:
        """Get episodes with pending tasks."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM episodes
                WHERE pending_tasks != '[]' AND archived = 0
                ORDER BY importance DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def archive_episode(self, episode_id: str) -> bool:
        """Archive an episode."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE episodes SET archived = 1 WHERE episode_id = ? AND locked = 0",
                (episode_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_episode(self, episode_id: str) -> bool:
        """Permanently delete an episode."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM episodes WHERE episode_id = ?", (episode_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def lock_episode(self, episode_id: str, locked: bool = True) -> bool:
        """Lock or unlock an episode (locked episodes are immune to forgetting)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE episodes SET locked = ? WHERE episode_id = ?",
                (1 if locked else 0, episode_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_episode_importance(self, episode_id: str, new_importance: float) -> bool:
        """Update the importance score of an episode (for decay)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE episodes SET importance = ? WHERE episode_id = ?",
                (new_importance, episode_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_emotion_snapshots(self, limit: int = 100) -> List[EmotionSnapshot]:
        """Get emotion snapshots in chronological order."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM emotion_snapshots ORDER BY timestamp ASC LIMIT ?",
                (limit,),
            )
            return [
                EmotionSnapshot(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    emotion=row["emotion"],
                    intensity=row["intensity"],
                    episode_id=row["episode_id"] or "",
                    notes=row["notes"] or "",
                )
                for row in cursor.fetchall()
            ]

    def delete_all_non_locked(self) -> int:
        """Delete all non-locked episodes (privacy erase)."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM episodes WHERE locked = 0")
            conn.commit()
            return cursor.rowcount

    def get_locked_episodes(self) -> List[Episode]:
        """Get all locked episodes."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM episodes WHERE locked = 1 ORDER BY started_at DESC"
            )
            return [self._row_to_episode(row) for row in cursor.fetchall()]

    def _row_to_episode(self, row) -> Episode:
        """Convert a SQLite row to an Episode dataclass."""
        def _parse_dt(val):
            if val:
                try:
                    return datetime.fromisoformat(val)
                except (ValueError, TypeError):
                    pass
            return datetime.now()

        return Episode(
            episode_id=row["episode_id"],
            title=row["title"],
            summary=row["summary"] or "",
            started_at=_parse_dt(row["started_at"]),
            ended_at=_parse_dt(row["ended_at"]),
            topics=json.loads(row["topics"] or "[]"),
            importance=float(row["importance"] or 0.0),
            emotion=row["emotion"] or "neutral",
            emotion_intensity=float(row["emotion_intensity"] or 0.0),
            outcome=row["outcome"] or "",
            pending_tasks=json.loads(row["pending_tasks"] or "[]"),
            follow_up=row["follow_up"] or "",
            related_goal_id=row["related_goal_id"] or "",
            source_session_id=row["source_session_id"] or "",
            interaction_ids=json.loads(row["interaction_ids"] or "[]"),
            locked=bool(row["locked"]),
            archived=bool(row["archived"]),
            created_at=_parse_dt(row["created_at"]),
        )
