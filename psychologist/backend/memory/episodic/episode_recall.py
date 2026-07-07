"""
Episode Recall — Episodic Memory

Retrieves relevant episodes for context injection.
Supports search by query, date, topic, emotion, goal, and recency.
All queries target <40ms (SQLite indexed).
"""

import time
import logging
from typing import List

from .schemas import Episode, EpisodeSearchResult
from .episode_store import EpisodeStore

logger = logging.getLogger("zara.memory.episodic.recall")


class EpisodeRecall:
    """
    Retrieves relevant episodes for the executive controller.

    Usage:
        recall = EpisodeRecall(episode_store)
        result = recall.recall_by_query("android voice", limit=5)
    """

    def __init__(self, episode_store: EpisodeStore):
        self.store = episode_store

    def recall_by_query(self, query: str, limit: int = 5) -> EpisodeSearchResult:
        """
        Search episodes by keyword across title, summary, and topics.

        Args:
            query: Search query string
            limit: Maximum results

        Returns:
            EpisodeSearchResult with matching episodes
        """
        start = time.perf_counter()
        episodes = self.store.search_episodes(query, limit=limit)
        elapsed = (time.perf_counter() - start) * 1000

        logger.debug("Recall by query '%s': %d results in %.1fms", query, len(episodes), elapsed)
        return EpisodeSearchResult(
            episodes=episodes,
            query=query,
            total_count=len(episodes),
            search_time_ms=round(elapsed, 2),
        )

    def recall_by_date(self, date_str: str, limit: int = 10) -> List[Episode]:
        """
        Get episodes on a specific date.

        Args:
            date_str: Date string (YYYY-MM-DD)
            limit: Maximum results

        Returns:
            List of episodes from that date
        """
        from datetime import datetime, timedelta
        try:
            target = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning("Invalid date format: %s", date_str)
            return []

        start = target.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
        return self.store.get_episodes_by_date_range(start, end, limit=limit)

    def recall_by_topic(self, topic: str, limit: int = 10) -> List[Episode]:
        """
        Get episodes matching a topic.

        Args:
            topic: Topic keyword
            limit: Maximum results

        Returns:
            List of matching episodes
        """
        return self.store.get_episodes_by_topic(topic, limit=limit)

    def recall_by_emotion(self, emotion: str, limit: int = 10) -> List[Episode]:
        """
        Get episodes with a specific emotion.

        Args:
            emotion: Emotion label
            limit: Maximum results

        Returns:
            List of matching episodes
        """
        return self.store.get_episodes_by_emotion(emotion, limit=limit)

    def recall_recent(self, limit: int = 10) -> List[Episode]:
        """
        Get the most recent episodes.

        Args:
            limit: Maximum results

        Returns:
            List of recent episodes
        """
        return self.store.get_all_episodes(include_archived=False)[:limit]

    def recall_for_goal(self, goal_id: str) -> List[Episode]:
        """
        Get episodes linked to a specific goal.

        Args:
            goal_id: Goal identifier

        Returns:
            List of episodes linked to this goal
        """
        if not goal_id:
            return []
        return self.store.get_episodes_by_goal(goal_id)

    def recall_pending(self, limit: int = 10) -> List[Episode]:
        """
        Get episodes with pending tasks.

        Args:
            limit: Maximum results

        Returns:
            List of episodes with unfinished work
        """
        return self.store.get_pending_episodes(limit=limit)

    def recall_high_importance(self, threshold: float = 0.7, limit: int = 10) -> List[Episode]:
        """
        Get high-importance episodes (achievements, milestones).

        Args:
            threshold: Minimum importance score
            limit: Maximum results

        Returns:
            List of high-importance episodes
        """
        return self.store.get_high_importance(threshold=threshold, limit=limit)
