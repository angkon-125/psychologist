"""
Memory schemas for persistence and queries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class ConversationRecord:
    session_id: str
    interaction_id: str
    role: str # "user" | "assistant" | "system"
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    emotion: Optional[str] = None
    confidence: float = 0.0
    risk_level: str = "low"
    metadata: Dict[str, Any] = field(default_factory=dict)
