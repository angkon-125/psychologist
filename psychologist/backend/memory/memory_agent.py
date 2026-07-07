"""
Memory Agent

Handles short-term memory, long-term SQLite database storage,
preferences, emotional trajectory records, and retrieval decisions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from backend.config import config
from .sqlite_store import SQLiteStore
from .vector_store import VectorStoreStub
from .conversation_memory import ConversationMemory
from .graph_memory import GraphMemory
from .episodic import (
    EpisodeStore, EpisodeBuilder, EpisodeRecall, Timeline,
    ContinuityConnector, ForgettingPolicy, ImportanceEngine,
)
from backend.safety.privacy_guard import PrivacyGuard

class MemoryAgent(BaseAgent):
    """
    Memory Agent is the brain's storage controller.
    Ensures persistent storage of conversation state, preferences, and trajectory.
    """

    def __init__(self):
        super().__init__()
        self.db = None
        self.vector_store = None
        self.conversation_memory = None
        self.privacy_guard = None
        self.graph_memory = None
        # Episodic memory components
        self.episode_store = None
        self.episode_builder = None
        self.episode_recall = None
        self.timeline = None
        self.continuity = None
        self.forgetting = None

    def _get_agent_name(self) -> str:
        return "memory"

    def initialize(self) -> bool:
        db_path = config.MEMORY_DB_PATH
        self.db = SQLiteStore(db_path)
        self.vector_store = VectorStoreStub()
        self.conversation_memory = ConversationMemory()
        self.privacy_guard = PrivacyGuard()
        self.graph_memory = GraphMemory()
        # Initialize episodic memory
        self.episode_store = EpisodeStore(db_path)
        importance_engine = ImportanceEngine()
        self.episode_builder = EpisodeBuilder(importance_engine=importance_engine)
        self.episode_recall = EpisodeRecall(self.episode_store)
        self.timeline = Timeline(self.episode_store)
        self.continuity = ContinuityConnector(self.episode_store)
        self.forgetting = ForgettingPolicy()
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        purpose = request.metadata.get("purpose", "retrieve")
        session_id = request.session_id
        
        if purpose == "save_interaction":
            text = request.text
            # Sanitize PII before storage
            if self.privacy_guard:
                text = self.privacy_guard.sanitize_for_storage(text)
            # Parse text into role / content (e.g. 'User: Hi | ZARA: Hello')
            role = "user"
            content = text
            if " | ZARA: " in text:
                parts = text.split(" | ZARA: ", 1)
                user_part = parts[0].replace("User: ", "", 1)
                zara_part = parts[1]
                
                # Save user part
                self.db.add_interaction(
                    session_id=session_id,
                    role="user",
                    text=user_part,
                    intent=request.metadata.get("intent"),
                    emotion=request.metadata.get("emotion"),
                    risk_level=request.metadata.get("risk", "low")
                )
                # Save assistant part
                self.db.add_interaction(
                    session_id=session_id,
                    role="assistant",
                    text=zara_part,
                    risk_level=request.metadata.get("risk", "low")
                )
                
                # Update vector store stub
                self.vector_store.add_entry(user_part, {"session_id": session_id, "role": "user"})
                self.vector_store.add_entry(zara_part, {"session_id": session_id, "role": "assistant"})
            else:
                self.db.add_interaction(
                    session_id=session_id,
                    role="user",
                    text=text,
                    intent=request.metadata.get("intent"),
                    risk_level=request.metadata.get("risk", "low")
                )
                self.vector_store.add_entry(text, {"session_id": session_id, "role": "user"})

            return AgentResponse(success=True, agent=self.name, response="Saved successfully")

        elif purpose == "retrieve":
            limit = request.metadata.get("limit", 5)
            # Retrieve recent conversation interactions
            history = self.db.get_recent_interactions(session_id, limit=limit)
            
            # Format context string
            context_lines = []
            for h in history:
                speaker = "User" if h["role"] == "user" else "ZARA"
                context_lines.append(f"{speaker}: {h['text']}")
            
            context_str = "\n".join(context_lines)
            
            return AgentResponse(
                success=True,
                agent=self.name,
                response=context_str,
                metadata={"context": context_str, "history": history}
            )

        elif purpose == "set_preference":
            key = request.metadata.get("key")
            value = request.metadata.get("value")
            if key:
                self.db.set_preference(key, value)
                return AgentResponse(success=True, agent=self.name, response=f"Set preference {key}")
            return AgentResponse.error(self.name, "Key not specified")

        elif purpose == "get_preference":
            key = request.metadata.get("key")
            default = request.metadata.get("default")
            if key:
                val = self.db.get_preference(key, default)
                return AgentResponse(success=True, agent=self.name, response=str(val), metadata={"value": val})
            return AgentResponse.error(self.name, "Key not specified")

        elif purpose == "save_summary":
            summary = request.metadata.get("summary", "")
            dominant_mood = request.metadata.get("dominant_mood", "neutral")
            self.db.save_summary(session_id, summary, dominant_mood)
            return AgentResponse(success=True, agent=self.name, response="Summary saved")

        elif purpose == "get_session_history":
            history = self.db.get_session_history()
            return AgentResponse(
                success=True,
                agent=self.name,
                response=f"Found {len(history)} sessions",
                metadata={"history": history}
            )

        elif purpose == "build_episode":
            # Feed a turn to the episode builder
            if self.episode_builder:
                self.episode_builder.add_turn(
                    text=request.text,
                    role=request.metadata.get("role", "user"),
                    intent=request.metadata.get("intent", "general"),
                    emotion=request.metadata.get("emotion", "neutral"),
                    session_id=session_id,
                )
                # Check if we should create an episode
                if self.episode_builder.should_create_episode():
                    episode = self.episode_builder.build_episode()
                    if episode and self.episode_store:
                        episode.source_session_id = session_id
                        self.episode_store.save_episode(episode)
                        self.episode_builder.reset()
                        return AgentResponse(
                            success=True,
                            agent=self.name,
                            response="Episode created",
                            metadata={"episode": episode.to_dict()}
                        )
            return AgentResponse(success=True, agent=self.name, response="Turn buffered")

        elif purpose == "recall_episodes":
            if self.episode_recall:
                query = request.metadata.get("query", request.text)
                topic = request.metadata.get("topic", "")
                emotion = request.metadata.get("emotion", "")
                limit = request.metadata.get("limit", 5)
                if topic:
                    episodes = self.episode_recall.recall_by_topic(topic, limit=limit)
                elif emotion:
                    episodes = self.episode_recall.recall_by_emotion(emotion, limit=limit)
                else:
                    result = self.episode_recall.recall_by_query(query, limit=limit)
                    episodes = result.episodes
                return AgentResponse(
                    success=True,
                    agent=self.name,
                    response=f"Found {len(episodes)} episodes",
                    metadata={"episodes": [e.to_dict() for e in episodes]}
                )
            return AgentResponse.error(self.name, "Episode recall not initialized")

        elif purpose == "get_timeline":
            if self.timeline:
                period = request.metadata.get("period", "all")
                summary = self.timeline.get_timeline_summary()
                return AgentResponse(
                    success=True,
                    agent=self.name,
                    response="Timeline retrieved",
                    metadata=summary,
                )
            return AgentResponse.error(self.name, "Timeline not initialized")

        elif purpose == "get_continuity_context":
            if self.continuity:
                context = self.continuity.generate_continuation_context()
                return AgentResponse(
                    success=True,
                    agent=self.name,
                    response=context or "No prior context",
                    metadata={"context": context},
                )
            return AgentResponse.error(self.name, "Continuity connector not initialized")

        elif purpose == "apply_forgetting":
            if self.forgetting and self.episode_store:
                action = request.metadata.get("action", "decay")
                if action == "decay":
                    count = self.forgetting.apply_decay(self.episode_store)
                elif action == "archive":
                    days = request.metadata.get("days", 90)
                    count = self.forgetting.archive_old(self.episode_store, days=days)
                elif action == "erase":
                    count = self.forgetting.privacy_erase(self.episode_store)
                else:
                    return AgentResponse.error(self.name, f"Unknown forgetting action: {action}")
                return AgentResponse(
                    success=True,
                    agent=self.name,
                    response=f"Forgetting policy applied: {count} episodes affected",
                    metadata={"affected": count, "action": action},
                )
            return AgentResponse.error(self.name, "Forgetting policy not initialized")

        return AgentResponse.error(self.name, f"Unknown memory agent purpose: {purpose}")
