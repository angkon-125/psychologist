"""
Forgetting Policy — Episodic Memory

User-controlled memory management:
  - Automatic importance decay over time
  - Archive old episodes
  - Manual delete
  - Privacy erase (all non-locked)
  - Locked memories (immune to decay/archive)
"""

import logging
from datetime import datetime, timedelta
from typing import List

from .schemas import Episode
from .episode_store import EpisodeStore

logger = logging.getLogger("zara.memory.episodic.forgetting")

# Minimum importance before auto-archive
ARCHIVE_THRESHOLD = 0.15


class ForgettingPolicy:
    """
    Controls how episodes fade, archive, or persist.

    Usage:
        policy = ForgettingPolicy()
        archived = policy.archive_old(episode_store, days=90)
        policy.apply_decay(episode_store, decay_rate=0.01)
    """

    def apply_decay(self, episode_store: EpisodeStore, decay_rate: float = 0.01) -> int:
        """
        Reduce importance of old episodes over time.
        Locked episodes are immune.
        Episodes falling below ARCHIVE_THRESHOLD are auto-archived.

        Args:
            episode_store: The episode store
            decay_rate: Amount to reduce per application (0.01 = 1%)

        Returns:
            Number of episodes archived due to decay
        """
        all_episodes = episode_store.get_all_episodes(include_archived=False)
        archived_count = 0

        for episode in all_episodes:
            if episode.locked:
                continue

            # Calculate age-based decay multiplier
            age_days = (datetime.now() - episode.created_at).days
            # Older episodes decay faster
            age_multiplier = 1.0 + (age_days / 30.0)  # 1x at 0 days, 2x at 30 days
            actual_decay = decay_rate * age_multiplier

            new_importance = max(0.0, episode.importance - actual_decay)
            episode_store.update_episode_importance(episode.episode_id, new_importance)

            # Auto-archive if below threshold
            if new_importance < ARCHIVE_THRESHOLD:
                episode_store.archive_episode(episode.episode_id)
                archived_count += 1

        logger.info("Decay applied: %d episodes archived", archived_count)
        return archived_count

    def archive_old(self, episode_store: EpisodeStore, days: int = 90) -> int:
        """
        Archive episodes older than N days.
        Locked episodes are immune.

        Args:
            episode_store: The episode store
            days: Age threshold in days

        Returns:
            Number of episodes archived
        """
        cutoff = datetime.now() - timedelta(days=days)
        all_episodes = episode_store.get_all_episodes(include_archived=False)
        archived_count = 0

        for episode in all_episodes:
            if episode.locked:
                continue
            if episode.started_at < cutoff:
                episode_store.archive_episode(episode.episode_id)
                archived_count += 1

        logger.info("Archived %d episodes older than %d days", archived_count, days)
        return archived_count

    def delete_episode(self, episode_store: EpisodeStore, episode_id: str) -> bool:
        """
        Permanently delete a single episode.

        Args:
            episode_store: The episode store
            episode_id: Episode to delete

        Returns:
            True if deleted, False if not found or locked
        """
        episode = episode_store.get_episode(episode_id)
        if not episode:
            return False
        if episode.locked:
            logger.warning("Cannot delete locked episode: %s", episode_id)
            return False

        result = episode_store.delete_episode(episode_id)
        if result:
            logger.info("Episode deleted: %s", episode_id)
        return result

    def privacy_erase(self, episode_store: EpisodeStore) -> int:
        """
        Delete all non-locked episodes (privacy erase).

        Args:
            episode_store: The episode store

        Returns:
            Number of episodes deleted
        """
        count = episode_store.delete_all_non_locked()
        logger.info("Privacy erase: %d episodes deleted", count)
        return count

    def locked_memories(self, episode_store: EpisodeStore) -> List[Episode]:
        """
        Get all locked episodes (immune to decay/archive).

        Args:
            episode_store: The episode store

        Returns:
            List of locked episodes
        """
        return episode_store.get_locked_episodes()
