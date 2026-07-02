"""
Tool Registry

Keeps track of registered local automation tools.
"""

from typing import Dict, Callable, Any, Optional
from .schemas import ToolDefinition

class ToolRegistry:
    """Manages active tools and executes them."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_tool(self, definition: ToolDefinition, executor: Callable[[Dict[str, Any]], Any]):
        self._tools[definition.name] = definition
        self._executors[definition.name] = executor

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def execute(self, name: str, args: Dict[str, Any]) -> Any:
        if name not in self._executors:
            raise ValueError(f"Tool '{name}' is not registered.")
        return self._executors[name](args)

    def list_tools(self) -> Dict[str, ToolDefinition]:
        return self._tools
