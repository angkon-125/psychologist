"""
Continuity Connector — Episodic Memory

Bridges episodic memory with the Executive Brain's GoalTracker.
Provides continuation context so ZARA can pick up where she left off
even after weeks of absence.
"""

import re
import logging
from typing import Dict, List, Any, Optional

from .schemas import Episode
from .episode_store import EpisodeStore

logger = logging.getLogger("zara.memory.episodic.continuity")


class ContinuityConnector:
    """
    Connects episodic memory with the executive goal tracker.

    Usage:
        connector = ContinuityConnector(episode_store)
        context = connector.generate_continuation_context(episode_store, goal_tracker)
    """

    def __init__(self, episode_store: EpisodeStore):
        self.store = episode_store

    def link_episode_to_goal(self, episode: Episode, goal_tracker) -> str:
        """
        Detect which active goal an episode relates to.

        Args:
            episode: The episode to link
            goal_tracker: Executive Brain's GoalTracker instance

        Returns:
            Goal ID if matched, empty string otherwise
        """
        if not goal_tracker or not episode:
            return ""

        # Try to detect goal from episode title + summary + topics
        text = f"{episode.title} {episode.summary} {' '.join(episode.topics)}"
        goal_id = goal_tracker.detect_goal_from_text(text)
        return goal_id or ""

    def get_goal_episodes(self, goal_id: str) -> Dict[str, Any]:
        """
        Get all episodes related to a goal, organized by status.

        Args:
            goal_id: Goal identifier

        Returns:
            Dict with: completed, remaining, blocked, next_recommendation
        """
        if not goal_id:
            return {"completed": [], "remaining": [], "blocked": [], "next_recommendation": ""}

        episodes = self.store.get_episodes_by_goal(goal_id)

        completed = []
        remaining = []
        blocked = []

        for ep in episodes:
            if ep.outcome and any(
                kw in ep.outcome.lower()
                for kw in ["finished", "completed", "done", "achieved", "built"]
            ):
                completed.append(ep.to_dict())
            elif ep.pending_tasks:
                remaining.append(ep.to_dict())
            else:
                blocked.append(ep.to_dict())

        # Next recommendation: most recent episode with pending tasks
        next_rec = ""
        if remaining:
            latest = remaining[0]  # Already sorted by date desc from store
            next_rec = latest.get("follow_up") or latest.get("title", "")

        return {
            "completed": completed,
            "remaining": remaining,
            "blocked": blocked,
            "next_recommendation": next_rec,
        }

    def generate_continuation_context(
        self,
        goal_tracker=None,
        limit_episodes: int = 3,
    ) -> str:
        """
        Build a context string for the executive controller.

        Includes: latest episode summaries, pending tasks, open goals,
        and relevant decisions.

        Args:
            goal_tracker: Executive Brain's GoalTracker (optional)
            limit_episodes: How many recent episodes to include

        Returns:
            Context string for injection into the planning pipeline
        """
        parts = []

        # Recent episodes
        recent = self.store.get_all_episodes(include_archived=False)[:limit_episodes]
        if recent:
            parts.append("Recent activity:")
            for ep in recent:
                summary = f"  - {ep.title}"
                if ep.pending_tasks:
                    summary += f" (pending: {', '.join(ep.pending_tasks[:2])})"
                parts.append(summary)

        # Pending tasks across all episodes
        pending_episodes = self.store.get_pending_episodes(limit=5)
        if pending_episodes:
            parts.append("\nUnfinished work:")
            for ep in pending_episodes:
                tasks = ", ".join(ep.pending_tasks[:3])
                parts.append(f"  - {ep.title}: {tasks}")

        # Active goals from goal tracker
        if goal_tracker:
            active_goals = goal_tracker.get_active_goals()
            if active_goals:
                parts.append("\nActive goals:")
                for goal in active_goals[:3]:
                    parts.append(f"  - {goal.description} ({goal.completion_pct:.0%} complete)")

        if not parts:
            return ""

        context = "\n".join(parts)
        logger.debug("Continuation context: %d chars", len(context))
        return context

    def detect_recurring_goals(self, text: str) -> List[str]:
        """
        Find goals/topics that appear across multiple episodes.

        Args:
            text: Current user input text

        Returns:
            List of topic strings that recur across episodes
        """
        if not text:
            return []

        # Extract key words from text
        words = set(re.findall(r'\b\w{4,}\b', text.lower()))
        stop_words = {"this", "that", "with", "have", "from", "they",
                      "would", "could", "should", "their", "there", "about"}
        words -= stop_words

        recurring = []
        for word in words:
            # Check if this word appears in multiple episodes
            episodes = self.store.search_episodes(word, limit=10)
            if len(episodes) >= 2:
                recurring.append(word)

        return recurring
