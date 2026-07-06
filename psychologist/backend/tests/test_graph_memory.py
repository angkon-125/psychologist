"""
Graph Memory tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.memory.graph_memory import GraphMemory


@pytest.fixture
def graph():
    return GraphMemory()


def test_initial_state(graph):
    """Graph starts empty."""
    stats = graph.get_stats()
    assert stats["node_count"] == 0
    assert stats["edge_count"] == 0


def test_add_entity(graph):
    """Add entity and retrieve it."""
    node = graph.add_entity("Work Stress", entity_type="topic")
    assert node.name == "work stress"
    assert node.entity_type == "topic"
    assert node.mentions == 1

    retrieved = graph.get_entity("Work Stress")
    assert retrieved is not None
    assert retrieved["name"] == "work stress"


def test_entity_touch_on_duplicate(graph):
    """Adding same entity increments mentions."""
    graph.add_entity("Anxiety")
    graph.add_entity("Anxiety")
    graph.add_entity("Anxiety")
    
    entity = graph.get_entity("anxiety")
    assert entity["mentions"] == 3


def test_add_relationship(graph):
    """Add relationship between entities."""
    graph.add_entity("Work", entity_type="topic")
    graph.add_entity("Stress", entity_type="emotion")
    graph.add_relationship("Work", "Stress", relation="causes")
    
    related = graph.get_related_entities("work")
    assert len(related) == 1
    assert related[0]["name"] == "stress"
    assert related[0]["relation"] == "causes"


def test_top_entities(graph):
    """Top entities sorted by mention count."""
    graph.add_entity("Topic A")
    graph.add_entity("Topic B")
    graph.add_entity("Topic A")  # 2 mentions
    graph.add_entity("Topic A")  # 3 mentions
    graph.add_entity("Topic B")  # 2 mentions
    graph.add_entity("Topic C")  # 1 mention
    
    top = graph.get_top_entities(limit=2)
    assert len(top) == 2
    assert top[0]["name"] == "topic a"
    assert top[0]["mentions"] == 3


def test_search_entities(graph):
    """Keyword search over entity names."""
    graph.add_entity("Work Stress")
    graph.add_entity("Social Anxiety")
    graph.add_entity("Family Issues")
    
    results = graph.search_entities("stress")
    assert len(results) == 1
    assert results[0]["name"] == "work stress"


def test_entity_not_found(graph):
    """Non-existent entity returns None."""
    assert graph.get_entity("nonexistent") is None


def test_clear(graph):
    """Clear removes all entities and edges."""
    graph.add_entity("A")
    graph.add_entity("B")
    graph.add_relationship("A", "B")
    graph.clear()
    
    stats = graph.get_stats()
    assert stats["node_count"] == 0
    assert stats["edge_count"] == 0


def test_capacity_eviction():
    """Graph evicts least-used entity when at capacity."""
    graph = GraphMemory()
    graph.MAX_NODES = 3
    
    graph.add_entity("A")
    graph.add_entity("B")
    graph.add_entity("C")
    
    # Adding 4th should evict least used
    graph.add_entity("D")
    
    stats = graph.get_stats()
    assert stats["node_count"] == 3
    # A, B, C all have 1 mention; one of them gets evicted
    assert graph.get_entity("D") is not None
