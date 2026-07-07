"""
Timeline — Episodic Memory

Chronological organization of episodes.
Supports period filtering, project grouping, emotional journey,
achievements, and pending goals.

Lazy-loaded: queries only when requested.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any

from .schemas import Episode, EmotionSnapshot
from .episode_store import EpisodeStore

logger = logging.getLogger("zara.memory.episodic.timeline")


class Timeline:
    """
    Chronological timeline of episodes.

    Usage:
        timeline = Timeline(episode_store)
        today = timeline.get_timeline(period="today")
        projects = timeline.get_projects()
    """

    def __init__(self, episode_store: EpisodeStore):
        self.store = episode_store

    def get_timeline(self, period: str = "all") -> List[Episode]:
        """
        Get episodes for a time period.

        Args:
            period: "today" | "yesterday" | "week" | "all"

        Returns:
            Chronologically ordered episode list (newest first)
        """
        now = datetime.now()

        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "week":
            start = now - timedelta(days=7)
            end = now
        else:  # "all"
            return self.store.get_all_episodes(include_archived=False)

        return self.store.get_episodes_by_date_range(start, end, limit=100)

    def get_projects(self) -> Dict[str, List[Episode]]:
        """
        Get episodes grouped by project/topic.

        Returns:
            Dict mapping topic -> list of episodes
        """
        all_episodes = self.store.get_all_episodes(include_archived=False)
        projects: Dict[str, List[Episode]] = defaultdict(list)

        for episode in all_episodes:
            for topic in episode.topics:
                projects[topic].append(episode)

        # Sort each project's episodes by date
        for topic in projects:
            projects[topic].sort(key=lambda e: e.started_at, reverse=True)

        return dict(projects)

    def get_achievements(self, limit: int = 20) -> List[Episode]:
        """
        Get high-importance completed episodes (achievements).

        Returns:
            List of high-importance episodes
        """
        return self.store.get_high_importance(threshold=0.7, limit=limit)

    def get_pending_goals(self, limit: int = 20) -> List[Episode]:
        """
        Get episodes with pending tasks.

        Returns:
            List of episodes with unfinished work
        """
        return self.store.get_pending_episodes(limit=limit)

    def get_emotional_journey(self, limit: int = 100) -> List[EmotionSnapshot]:
        """
        Get emotional progression over time.

        Returns:
            Chronological list of EmotionSnapshots
        """
        return self.store.get_emotion_snapshots(limit=limit)

    def get_timeline_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the timeline for the frontend.

        Returns:
            Dict with today, yesterday, week counts and recent episodes
        """
        today = self.get_timeline("today")
        yesterday = self.get_timeline("yesterday")
        week = self.get_timeline("week")
        pending = self.get_pending_goals(limit=5)
        achievements = self.get_achievements(limit=5)

        return {
            "today": [e.to_dict() for e in today],
            "yesterday": [e.to_dict() for e in yesterday],
            "week": [e.to_dict() for e in week],
            "pending": [e.to_dict() for e in pending],
            "achievements": [e.to_dict() for e in achievements],
            "today_count": len(today),
            "yesterday_count": len(yesterday),
            "week_count": len(week),
        }
