"""
SQLite Store for Persistent Memory

Creates the local SQLite database and provides clean methods to store/retrieve
conversations, emotional memories, preferences, and session logs.
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("zara.memory.sqlite")

class SQLiteStore:
    """
    SQLite persistence backend for the Memory Agent.
    Creates and manages tables for session records, emotional context, and preferences.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure containing directory exists
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the memory schema tables if they do not exist."""
        with self._get_connection() as conn:
            # 1. Conversation turns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL, -- 'user' or 'assistant'
                    text TEXT NOT NULL,
                    intent TEXT,
                    emotion TEXT,
                    confidence REAL,
                    risk_level TEXT,
                    metadata TEXT
                )
            """)
            
            # 2. Emotional memory & patterns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emotional_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    dominant_emotion TEXT NOT NULL,
                    intensity REAL NOT NULL,
                    notes TEXT,
                    metadata TEXT
                )
            """)

            # 3. User Preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # 4. Session summaries table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    dominant_mood TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
        logger.info("SQLiteStore tables verified at %s", self.db_path)

    # ── Interaction CRUD ──────────────────────────────────────────

    def add_interaction(
        self,
        session_id: str,
        role: str,
        text: str,
        intent: Optional[str] = None,
        emotion: Optional[str] = None,
        confidence: float = 0.0,
        risk_level: str = "low",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Adds a conversation interaction (turn)."""
        meta_str = json.dumps(metadata or {})
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO interactions (session_id, timestamp, role, text, intent, emotion, confidence, risk_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, now, role, text, intent, emotion, confidence, risk_level, meta_str)
            )
            conn.commit()

    def get_recent_interactions(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent conversation turns for a session."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT role, text, timestamp, intent, emotion, confidence, risk_level, metadata
                FROM interactions
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cursor.fetchall()
            # Convert back to ordered list (from oldest to newest)
            results = []
            for row in reversed(rows):
                results.append({
                    "role": row["role"],
                    "text": row["text"],
                    "timestamp": row["timestamp"],
                    "intent": row["intent"],
                    "emotion": row["emotion"],
                    "confidence": row["confidence"],
                    "risk_level": row["risk_level"],
                    "metadata": json.loads(row["metadata"] or "{}")
                })
            return results

    # ── Preferences CRUD ─────────────────────────────────────────

    def set_preference(self, key: str, value: Any):
        """Sets a persistent user preference."""
        val_str = json.dumps(value)
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, val_str, now)
            )
            conn.commit()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieves a user preference."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
            return default

    def get_all_preferences(self) -> Dict[str, Any]:
        """Retrieves all stored preferences."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM user_preferences")
            rows = cursor.fetchall()
            result = {}
            for row in rows:
                try:
                    result[row["key"]] = json.loads(row["value"])
                except Exception:
                    result[row["key"]] = row["value"]
            return result

    # ── Session Summary CRUD ─────────────────────────────────────

    def save_summary(self, session_id: str, summary: str, dominant_mood: Optional[str] = None, metadata: Optional[Dict] = None):
        """Saves a summary of a completed session."""
        now = datetime.now().isoformat()
        meta_str = json.dumps(metadata or {})
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO session_summaries (session_id, created_at, summary, dominant_mood, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, now, summary, dominant_mood, meta_str)
            )
            conn.commit()

    def get_session_history(self) -> List[Dict[str, Any]]:
        """Retrieves session summaries representing long-term memory logs."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT session_id, created_at, summary, dominant_mood, metadata
                FROM session_summaries
                ORDER BY created_at DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "session_id": r["session_id"],
                    "created_at": r["created_at"],
                    "summary": r["summary"],
                    "dominant_mood": r["dominant_mood"],
                    "metadata": json.loads(r["metadata"] or "{}")
                }
                for r in rows
            ]
