"""
Graph Memory

Lightweight in-memory entity-relationship graph for tracking
user topics, people, places, and their connections over time.

This is NOT a full graph database — it's a simple adjacency
structure that captures entities mentioned in conversations
and the relationships between them, enabling context-aware
follow-up questions and topic tracking.
"""

import logging
from typing import Dict, Any, List, Set, Optional
from datetime import datetime

logger = logging.getLogger("zara.memory.graph")


class GraphNode:
    """A single entity in the memory graph."""

    def __init__(self, name: str, entity_type: str = "topic"):
        self.name = name.lower().strip()
        self.entity_type = entity_type  # "topic" | "person" | "place" | "event" | "emotion"
        self.mentions: int = 1
        self.first_seen: str = datetime.now().isoformat()
        self.last_seen: str = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}

    def touch(self):
        """Update last-seen timestamp and increment mention count."""
        self.mentions += 1
        self.last_seen = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "mentions": self.mentions,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }


class GraphMemory:
    """
    In-memory entity-relationship graph for conversation context.

    Tracks entities mentioned by the user and their connections,
    enabling the system to:
      - Recall topics the user cares about
      - Detect recurring themes
      - Build context for follow-up questions
    """

    # Maximum entities to keep (prevents unbounded growth)
    MAX_NODES = 200
    MAX_EDGES = 500

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, Set[str]] = {}  # adjacency list

    def add_entity(
        self,
        name: str,
        entity_type: str = "topic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GraphNode:
        """
        Add or update an entity in the graph.

        Args:
            name: Entity name (will be lowercased).
            entity_type: Category of entity.
            metadata: Optional extra data.

        Returns:
            The created or updated GraphNode.
        """
        key = name.lower().strip()
        if not key:
            raise ValueError("Entity name cannot be empty")

        if key in self._nodes:
            self._nodes[key].touch()
            if metadata:
                self._nodes[key].metadata.update(metadata)
        else:
            # Enforce capacity
            if len(self._nodes) >= self.MAX_NODES:
                self._evict_least_used()

            node = GraphNode(key, entity_type)
            if metadata:
                node.metadata = metadata
            self._nodes[key] = node

        logger.debug("Entity added/updated: %s (%s)", key, entity_type)
        return self._nodes[key]

    def add_relationship(self, entity_a: str, entity_b: str, relation: str = "related"):
        """
        Add a bidirectional relationship between two entities.

        Args:
            entity_a: First entity name.
            entity_b: Second entity name.
            relation: Relationship label.
        """
        key_a = entity_a.lower().strip()
        key_b = entity_b.lower().strip()

        if key_a not in self._nodes or key_b not in self._nodes:
            logger.warning("Cannot add edge: missing node(s) %s <-> %s", key_a, key_b)
            return

        if key_a not in self._edges:
            self._edges[key_a] = set()
        if key_b not in self._edges:
            self._edges[key_b] = set()

        # Store as "target:relation" for labeled edges
        self._edges[key_a].add(f"{key_b}:{relation}")
        self._edges[key_b].add(f"{key_a}:{relation}")

        # Enforce edge capacity
        total_edges = sum(len(v) for v in self._edges.values()) // 2
        if total_edges > self.MAX_EDGES:
            self._prune_edges()

        logger.debug("Edge added: %s <-> %s (%s)", key_a, key_b, relation)

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """Get entity details by name."""
        node = self._nodes.get(name.lower().strip())
        return node.to_dict() if node else None

    def get_related_entities(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get entities related to the given entity."""
        key = name.lower().strip()
        if key not in self._edges:
            return []

        results = []
        for edge_label in list(self._edges[key])[:limit]:
            parts = edge_label.rsplit(":", 1)
            target = parts[0]
            relation = parts[1] if len(parts) > 1 else "related"
            node = self._nodes.get(target)
            if node:
                results.append({
                    "name": target,
                    "relation": relation,
                    "mentions": node.mentions,
                })
        return results

    def get_top_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most-mentioned entities."""
        sorted_nodes = sorted(
            self._nodes.values(), key=lambda n: n.mentions, reverse=True
        )
        return [n.to_dict() for n in sorted_nodes[:limit]]

    def search_entities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search over entity names."""
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        matches = []
        for node in self._nodes.values():
            if query_lower in node.name:
                matches.append(node.to_dict())
                if len(matches) >= limit:
                    break
        return matches

    def get_stats(self) -> Dict[str, Any]:
        """Return graph statistics for diagnostics."""
        total_edges = sum(len(v) for v in self._edges.values()) // 2
        return {
            "node_count": len(self._nodes),
            "edge_count": total_edges,
            "max_nodes": self.MAX_NODES,
            "max_edges": self.MAX_EDGES,
        }

    def clear(self):
        """Clear all entities and relationships."""
        self._nodes.clear()
        self._edges.clear()
        logger.debug("Graph memory cleared")

    def _evict_least_used(self):
        """Remove the least-mentioned entity to make room."""
        if not self._nodes:
            return
        least = min(self._nodes.values(), key=lambda n: n.mentions)
        key = least.name
        del self._nodes[key]
        self._edges.pop(key, None)
        # Remove from other adjacency lists
        for neighbors in self._edges.values():
            to_remove = {e for e in neighbors if e.startswith(f"{key}:")}
            neighbors -= to_remove
        logger.debug("Evicted least-used entity: %s (mentions=%d)", key, least.mentions)

    def _prune_edges(self):
        """Remove lowest-value edges to stay within capacity."""
        # Simple strategy: remove edges from least-mentioned nodes first
        sorted_nodes = sorted(self._nodes.values(), key=lambda n: n.mentions)
        for node in sorted_nodes:
            if node.name in self._edges:
                self._edges[node.name].clear()
                total = sum(len(v) for v in self._edges.values()) // 2
                if total <= self.MAX_EDGES:
                    break
