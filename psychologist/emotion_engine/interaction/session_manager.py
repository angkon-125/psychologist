"""
Session Manager

Creates, loads, saves, and queries user sessions.
Sessions are stored as JSON files in a local directory.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from .interaction_models import (
    SessionState,
    UserMessage,
    AssistantMessage,
)


class SessionManager:
    """Manages session lifecycle: create, update, save, load, summarise."""

    def __init__(
        self,
        sessions_dir: Optional[str] = None,
        max_stored_sessions: int = 50,
        max_session_minutes: int = 60,
        auto_save: bool = True,
    ):
        if sessions_dir:
            self._sessions_dir = Path(sessions_dir)
        else:
            self._sessions_dir = Path(__file__).parent.parent.parent / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

        self._max_stored = max_stored_sessions
        self._max_minutes = max_session_minutes
        self._auto_save = auto_save
        self._current_session: Optional[SessionState] = None
        self._activity_callback: Optional[Callable[[str], None]] = None

    # ── Activity callback ────────────────────────────────────────

    def set_activity_callback(self, callback: Optional[Callable[[str], None]]):
        self._activity_callback = callback

    def _log_activity(self, text: str):
        if self._activity_callback:
            self._activity_callback(text)

    # ── Session lifecycle ────────────────────────────────────────

    def start_session(
        self,
        mode: str = "hybrid",
        language: str = "en",
    ) -> SessionState:
        """Start a new session. Saves any existing session first."""
        if self._current_session:
            self.end_session()

        session = SessionState(
            active_mode=mode,
            language=language,
        )
        self._current_session = session
        self._log_activity("Session started")
        return session

    def end_session(self, generate_summary: bool = True) -> Optional[Dict]:
        """End the current session, generate summary, save to disk."""
        if not self._current_session:
            return None

        self._current_session.end_time = datetime.now()

        if generate_summary:
            self._current_session.summary = self._generate_summary()
            self._current_session.follow_up_suggestions = self._generate_follow_ups()

        result = self._current_session.to_dict()
        self._save_session(self._current_session)
        self._log_activity("Session saved")
        self._current_session = None
        self._cleanup_old_sessions()
        return result

    def get_current_session(self) -> Optional[SessionState]:
        return self._current_session

    def has_active_session(self) -> bool:
        return self._current_session is not None

    # ── Message recording ────────────────────────────────────────

    def add_user_message(self, message: UserMessage):
        """Add a user message to the current session."""
        if not self._current_session:
            return
        self._current_session.user_messages.append(message.to_dict())
        self._current_session.last_interaction_time = datetime.now()

        if message.detected_emotion:
            self._current_session.detected_emotions.append(message.detected_emotion)
            self._current_session.mood_timeline.append({
                "emotion": message.detected_emotion,
                "confidence": message.confidence,
                "timestamp": message.timestamp.isoformat(),
                "input_type": message.input_type,
            })

        if self._auto_save:
            self._save_session(self._current_session)

    def add_assistant_message(self, message: AssistantMessage):
        """Add an assistant response to the current session."""
        if not self._current_session:
            return
        self._current_session.assistant_messages.append(message.to_dict())

        if message.safety_level and message.safety_level != "none":
            self._current_session.safety_flags.append(message.safety_level)

        if self._auto_save:
            self._save_session(self._current_session)

    def update_emotion_state(self, emotion_state: Dict):
        """Update the current session's emotion state snapshot."""
        if self._current_session:
            self._current_session.current_emotion_state = emotion_state

    def update_mode(self, mode: str):
        """Record a mode switch in the active session."""
        if self._current_session:
            self._current_session.active_mode = mode

    def update_preferences(self, preferences: Dict):
        """Snapshot user preferences into the session."""
        if self._current_session:
            self._current_session.user_preference_snapshot.update(preferences)

    # ── Session queries ──────────────────────────────────────────

    def get_session_history(self, limit: int = 10) -> List[Dict]:
        """Return summaries of recent past sessions."""
        session_files = sorted(
            self._sessions_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        results = []
        for f in session_files[:limit]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "session_id": data.get("session_id", ""),
                    "start_time": data.get("start_time", ""),
                    "end_time": data.get("end_time", ""),
                    "summary": data.get("summary", ""),
                    "message_count": len(data.get("user_messages", [])),
                    "active_mode": data.get("active_mode", ""),
                    "language": data.get("language", "en"),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return results

    def get_recurring_emotions(self, max_sessions: int = 20) -> Dict[str, int]:
        """Analyse recent sessions for recurring emotion patterns."""
        emotion_counts: Dict[str, int] = {}
        session_files = sorted(
            self._sessions_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for f in session_files[:max_sessions]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for emotion in data.get("detected_emotions", []):
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            except (json.JSONDecodeError, OSError):
                continue
        return emotion_counts

    def get_preferred_mode(self, max_sessions: int = 10) -> str:
        """Determine user's preferred interaction mode from recent sessions."""
        mode_counts: Dict[str, int] = {}
        session_files = sorted(
            self._sessions_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for f in session_files[:max_sessions]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                mode = data.get("active_mode", "hybrid")
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            except (json.JSONDecodeError, OSError):
                continue
        if not mode_counts:
            return "hybrid"
        return max(mode_counts, key=mode_counts.get)

    # ── Summary generation ───────────────────────────────────────

    def _generate_summary(self) -> str:
        """Generate a simple end-of-session summary."""
        if not self._current_session:
            return ""

        s = self._current_session
        msg_count = len(s.user_messages)
        emotions = s.detected_emotions

        # Find most frequent emotion
        if emotions:
            emotion_counts: Dict[str, int] = {}
            for e in emotions:
                emotion_counts[e] = emotion_counts.get(e, 0) + 1
            dominant = max(emotion_counts, key=emotion_counts.get)
        else:
            dominant = "neutral"

        duration = ""
        if s.start_time:
            end = s.end_time or datetime.now()
            minutes = int((end - s.start_time).total_seconds() / 60)
            duration = f" over {minutes} minute{'s' if minutes != 1 else ''}"

        safety_note = ""
        if s.safety_flags:
            safety_note = " Safety support was provided during this session."

        return (
            f"Session with {msg_count} interaction{'s' if msg_count != 1 else ''}"
            f"{duration}. "
            f"Primary emotional theme: {dominant}.{safety_note}"
        )

    def _generate_follow_ups(self) -> List[str]:
        """Suggest follow-up actions based on session content."""
        if not self._current_session:
            return []

        suggestions = []
        emotions = self._current_session.detected_emotions

        if emotions:
            # Count high-distress emotions
            distress = sum(
                1 for e in emotions
                if e in ("sadness", "anger", "fear", "anxiety", "stress", "loneliness")
            )
            if distress > len(emotions) * 0.5:
                suggestions.append(
                    "Consider trying a breathing exercise or grounding activity."
                )
                suggestions.append(
                    "Journaling about today's feelings may help organise your thoughts."
                )
            if any(e in ("stress", "burnout", "emotional_fatigue") for e in emotions):
                suggestions.append(
                    "Taking a break and doing something you enjoy could help restore energy."
                )

        suggestions.append(
            "Remember, reaching out to a trusted person or professional is always a good step."
        )
        return suggestions

    # ── Persistence ──────────────────────────────────────────────

    def _save_session(self, session: SessionState):
        """Save session to a JSON file on disk."""
        filename = f"session_{session.session_id}.json"
        filepath = self._sessions_dir / filename
        try:
            filepath.write_text(
                json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as e:
            print(f"Failed to save session: {e}")

    def _cleanup_old_sessions(self):
        """Remove oldest sessions if we exceed the max count."""
        session_files = sorted(
            self._sessions_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
        )
        while len(session_files) > self._max_stored:
            oldest = session_files.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass
