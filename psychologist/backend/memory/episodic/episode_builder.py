"""
Episode Builder — Episodic Memory

Groups related conversation turns into meaningful episodes.
Does NOT save every conversation — only creates episodes when:
  - Project milestone reached
  - Emotional conversation
  - Important decision made
  - Long planning session
  - Task completion
  - Repeated topic
  - User explicitly asks to remember

Ignores:
  - Small talk (hello, thanks, short replies)
"""

import re
import logging
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List, Optional

from .schemas import Episode
from .importance import ImportanceEngine

logger = logging.getLogger("zara.memory.episodic.builder")

# Trigger patterns that indicate an episode should be created
_EPISODE_TRIGGER_PATTERNS = [
    re.compile(r"\b(finished|completed|done|built|created|implemented|deployed)\b", re.IGNORECASE),
    re.compile(r"\b(milestone|breakthrough|achievement|accomplished)\b", re.IGNORECASE),
    re.compile(r"\b(decided|decision|chose|going\s+to\s+build|plan\s+to)\b", re.IGNORECASE),
    re.compile(r"\b(started|began|launched)\b.*\b(project|goal|plan|phase)\b", re.IGNORECASE),
    re.compile(r"\b(remember|save|don'?t\s+forget)\b", re.IGNORECASE),
    re.compile(r"\b(finally|at\s+last|after\s+all\s+this)\b", re.IGNORECASE),
]

# Ignore patterns — these should NOT trigger episode creation
_IGNORE_PATTERNS = [
    re.compile(r"^(hi|hello|hey|good\s*(morning|afternoon|evening))\b", re.IGNORECASE),
    re.compile(r"^(thanks|thank\s+you|thx|ty)\b", re.IGNORECASE),
    re.compile(r"^(bye|goodbye|good\s*night|see\s+you|take\s+care)\b", re.IGNORECASE),
    re.compile(r"^(ok|okay|sure|got\s+it|alright|cool|nice)\b", re.IGNORECASE),
    re.compile(r"^(yes|no|yeah|nope|yep)\b", re.IGNORECASE),
]

# Emotion keywords for extracting dominant emotion
_EMOTION_KEYWORDS = {
    "excited": ["excited", "thrilled", "pumped", "amazing", "awesome", "great"],
    "happy": ["happy", "glad", "pleased", "good", "joyful"],
    "motivated": ["motivated", "inspired", "driven", "determined", "focused"],
    "anxious": ["anxious", "worried", "nervous", "stressed", "tense"],
    "sad": ["sad", "down", "depressed", "unhappy", "low"],
    "frustrated": ["frustrated", "annoyed", "irritated", "fed up"],
    "relieved": ["relieved", "relaxed", "calm", "peaceful"],
    "neutral": [],
}

# Topic extraction keywords
_TOPIC_KEYWORDS = {
    "architecture": ["architecture", "design", "system", "structure", "pattern"],
    "voice": ["voice", "tts", "stt", "speech", "audio", "whisper", "piper"],
    "memory": ["memory", "store", "database", "sqlite", "remember"],
    "testing": ["test", "pytest", "assert", "coverage", "suite"],
    "frontend": ["frontend", "ui", "css", "html", "javascript", "dom"],
    "backend": ["backend", "api", "route", "endpoint", "flask"],
    "safety": ["safety", "crisis", "risk", "emergency", "helpline"],
    "prediction": ["predict", "forecast", "risk", "recommend", "next"],
    "emotion": ["emotion", "feeling", "mood", "sentiment", "affect"],
    "goal": ["goal", "milestone", "task", "progress", "complete"],
}


class EpisodeBuilder:
    """
    Groups conversation turns into meaningful episodes.

    Usage:
        builder = EpisodeBuilder()
        builder.add_turn("I finished the architecture!", "user", "general", "excited", "sess1")
        builder.add_turn("Great work!", "assistant", "general", "happy", "sess1")
        if builder.should_create_episode():
            episode = builder.build_episode()
            builder.reset()
    """

    def __init__(self, importance_engine: Optional[ImportanceEngine] = None):
        self.importance_engine = importance_engine or ImportanceEngine()
        self._buffer: List[Dict[str, Any]] = []
        self._session_id: str = ""
        self._known_topics: set = set()

    def add_turn(
        self,
        text: str,
        role: str,
        intent: str = "general",
        emotion: str = "neutral",
        session_id: str = "",
    ) -> None:
        """Add a conversation turn to the buffer."""
        self._buffer.append({
            "text": text,
            "role": role,
            "intent": intent,
            "emotion": emotion,
            "session_id": session_id,
            "timestamp": datetime.now(),
        })
        if session_id:
            self._session_id = session_id

    def should_create_episode(self) -> bool:
        """
        Determine if the buffered turns warrant creating an episode.

        Returns True when:
          - Episode trigger patterns detected
          - Long conversation (10+ turns)
          - Strong emotions detected
          - User explicitly asked to remember
          - Repeated topic (3+ mentions)
        """
        if len(self._buffer) < 2:
            return False

        # Check ignore patterns on all user turns
        user_turns = [t for t in self._buffer if t["role"] == "user"]
        if not user_turns:
            return False

        # Check if all user turns are ignorable
        all_ignorable = all(self._is_ignorable(t["text"]) for t in user_turns)
        if all_ignorable:
            return False

        # Check explicit triggers
        for turn in user_turns:
            if any(p.search(turn["text"]) for p in _EPISODE_TRIGGER_PATTERNS):
                return True

        # Check user requested remember
        for turn in user_turns:
            if self.importance_engine._user_requested_remember(turn["text"]):
                return True

        # Check long conversation
        if len(self._buffer) >= 10:
            return True

        # Check strong emotions
        for turn in self._buffer:
            if turn["emotion"] in ("excited", "anxious", "sad", "frustrated",
                                    "overwhelmed", "scared", "hopeless", "depressed"):
                return True

        # Check repeated topic
        topic_counts = Counter()
        for turn in self._buffer:
            for topic in self._extract_topics(turn["text"]):
                topic_counts[topic] += 1
        if topic_counts and topic_counts.most_common(1)[0][1] >= 3:
            return True

        # Check importance score
        combined_text = " ".join(t["text"] for t in user_turns)
        dominant_emotion = self._dominant_emotion()
        score = self.importance_engine.score(
            text=combined_text,
            intent=user_turns[-1]["intent"] if user_turns else "general",
            emotion=dominant_emotion,
            context_length=len(self._buffer),
            has_goal=False,
            known_topics=self._known_topics,
        )
        return self.importance_engine.should_store(score)

    def build_episode(self) -> Optional[Episode]:
        """
        Build an Episode from the buffered turns.

        Returns None if buffer is empty or episode shouldn't be created.
        """
        if not self._buffer:
            return None

        user_turns = [t for t in self._buffer if t["role"] == "user"]
        if not user_turns:
            return None

        # Title: first meaningful user message (trimmed)
        title = self._extract_title(user_turns)

        # Summary: combine key user messages
        summary = self._build_summary(user_turns)

        # Topics: extract from all turns
        all_topics = set()
        for turn in self._buffer:
            all_topics.update(self._extract_topics(turn["text"]))
        # Also add intent-based topics
        for turn in self._buffer:
            if turn["intent"] not in ("general", "greeting", "farewell"):
                all_topics.add(turn["intent"].replace("_", " "))

        # Dominant emotion
        dominant_emotion = self._dominant_emotion()
        emotion_intensity = self._emotion_intensity(dominant_emotion)

        # Importance score
        combined_text = " ".join(t["text"] for t in user_turns)
        importance = self.importance_engine.score(
            text=combined_text,
            intent=user_turns[-1]["intent"] if user_turns else "general",
            emotion=dominant_emotion,
            context_length=len(self._buffer),
            has_goal=False,
            known_topics=self._known_topics,
        )

        # Pending tasks from content
        pending_tasks = self._extract_pending_tasks(user_turns)

        # Outcome
        outcome = self._extract_outcome(user_turns)

        # Update known topics
        self._known_topics.update(all_topics)

        episode = Episode(
            title=title,
            summary=summary,
            started_at=self._buffer[0]["timestamp"],
            ended_at=self._buffer[-1]["timestamp"],
            topics=sorted(all_topics),
            importance=importance,
            emotion=dominant_emotion,
            emotion_intensity=emotion_intensity,
            outcome=outcome,
            pending_tasks=pending_tasks,
            source_session_id=self._session_id,
        )

        logger.info(
            "Episode built: '%s' (importance=%.2f, emotion=%s, topics=%d)",
            episode.title, episode.importance, episode.emotion, len(episode.topics),
        )
        return episode

    def reset(self) -> None:
        """Clear the buffer after episode creation."""
        self._buffer.clear()
        logger.debug("Episode builder buffer cleared")

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)

    def _is_ignorable(self, text: str) -> bool:
        """Check if text matches ignore patterns (small talk)."""
        if not text:
            return True
        text_stripped = text.strip()
        if len(text_stripped) < 10:
            return True
        return any(p.match(text_stripped) for p in _IGNORE_PATTERNS)

    def _extract_title(self, user_turns: List[Dict]) -> str:
        """Extract a title from the first meaningful user message."""
        for turn in user_turns:
            text = turn["text"].strip()
            if len(text) >= 10 and not self._is_ignorable(text):
                # Trim to ~60 chars
                if len(text) > 60:
                    return text[:57].rsplit(" ", 1)[0] + "..."
                return text
        # Fallback: use first user turn
        text = user_turns[0]["text"].strip() if user_turns else "Conversation"
        return text[:60] if text else "Conversation"

    def _build_summary(self, user_turns: List[Dict]) -> str:
        """Build a summary from key user messages."""
        parts = []
        for turn in user_turns[:5]:  # Max 5 messages in summary
            text = turn["text"].strip()
            if len(text) >= 5 and not self._is_ignorable(text):
                parts.append(text[:100])
        if not parts:
            return "Conversation occurred"
        return "; ".join(parts[:3])

    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text using keyword matching."""
        if not text:
            return []
        text_lower = text.lower()
        topics = []
        for topic, keywords in _TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        return topics

    def _dominant_emotion(self) -> str:
        """Find the most common emotion in the buffer."""
        emotions = [t["emotion"] for t in self._buffer if t.get("emotion")]
        if not emotions:
            return "neutral"
        counter = Counter(emotions)
        return counter.most_common(1)[0][0]

    def _emotion_intensity(self, emotion: str) -> float:
        """Get intensity for the dominant emotion."""
        from .importance import _EMOTION_INTENSITY
        return _EMOTION_INTENSITY.get(emotion, 0.1)

    def _extract_pending_tasks(self, user_turns: List[Dict]) -> List[str]:
        """Extract pending tasks from conversation content."""
        tasks = []
        task_patterns = [
            re.compile(r"\b(need\s+to|have\s+to|must|should|will|plan\s+to|next|todo)\b.*\b(\w+)", re.IGNORECASE),
            re.compile(r"\b(follow[- ]?up|continue|resume)\b.*\b(\w+)", re.IGNORECASE),
        ]
        for turn in user_turns:
            text = turn["text"]
            for pattern in task_patterns:
                match = pattern.search(text)
                if match:
                    task_text = match.group(0).strip()[:80]
                    if task_text and task_text not in tasks:
                        tasks.append(task_text)
        return tasks[:5]  # Max 5 pending tasks

    def _extract_outcome(self, user_turns: List[Dict]) -> str:
        """Extract the outcome from the conversation."""
        outcome_patterns = [
            re.compile(r"\b(finished|completed|done|built|created|implemented|deployed)\b", re.IGNORECASE),
            re.compile(r"\b(decided|chose|agreed|resolved)\b", re.IGNORECASE),
            re.compile(r"\b(learned|understood|realized|discovered)\b", re.IGNORECASE),
        ]
        for turn in reversed(user_turns):
            text = turn["text"]
            for pattern in outcome_patterns:
                if pattern.search(text):
                    return text[:100]
        return ""
