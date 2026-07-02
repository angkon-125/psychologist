"""
Vector Store Stub for Semantic Memory

A fallback semantic search implementation that uses keyword matching
and similarity mapping when heavy databases are disabled or unavailable.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("zara.memory.vector")

class VectorStoreStub:
    """
    Stub Vector Store for semantic memory retrieval.
    Performs keyword matching fallback without requiring ChromaDB or FAISS.
    """

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []

    def add_entry(self, text: str, metadata: Dict[str, Any], tags: Optional[List[str]] = None):
        """Add text entry to semantic repository."""
        self._entries.append({
            "text": text,
            "metadata": metadata,
            "tags": tags or []
        })

    def similarity_search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Simple keyword overlap similarity search.
        """
        query_words = set(query.lower().split())
        if not query_words:
            return self._entries[:limit]

        scored_entries = []
        for entry in self._entries:
            text_words = set(entry["text"].lower().split())
            tag_words = set(t.lower() for t in entry["tags"])
            
            # Intersection score
            overlap = len(query_words.intersection(text_words)) + len(query_words.intersection(tag_words)) * 2
            if overlap > 0:
                scored_entries.append((overlap, entry))

        # Sort by score descending
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def clear(self):
        self._entries.clear()
