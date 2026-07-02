"""
Tool Schemas

Defines structured schemas for registering local execution tools.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    risk_level: str = "low" # "low" | "medium" | "high"
    required_permission: str = "none"
    timeout: int = 30
    failure_response: str = "Execution failed."
