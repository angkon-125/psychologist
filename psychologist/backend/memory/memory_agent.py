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

class MemoryAgent(BaseAgent):
    """
    Memory Agent is the brain's storage controller.
    Ensures persistent storage of conversation state, preferences, and trajectory.
    """

    def __init__(self):
        super().__init__()
        self.db = None
        self.vector_store = None

    def _get_agent_name(self) -> str:
        return "memory"

    def initialize(self) -> bool:
        db_path = config.MEMORY_DB_PATH
        self.db = SQLiteStore(db_path)
        self.vector_store = VectorStoreStub()
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        purpose = request.metadata.get("purpose", "retrieve")
        session_id = request.session_id
        
        if purpose == "save_interaction":
            text = request.text
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

        return AgentResponse.error(self.name, f"Unknown memory agent purpose: {purpose}")
