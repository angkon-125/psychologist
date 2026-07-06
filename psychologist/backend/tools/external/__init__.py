"""
External Tools

Stub for external tool integration (MCP client, API connectors, etc.).
External tools require safety approval before execution.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("zara.tools.external")


class ExternalToolStub:
    """
    Placeholder for external tool integration (e.g., MCP protocol).
    
    External tools are not yet implemented. This stub provides
    the interface that future external tool connectors must follow.
    
    All external tools require:
      - Safety Agent permission check before execution
      - User confirmation for medium+ risk operations
      - Timeout enforcement
      - Result validation
    """

    def __init__(self):
        self._available = False
        logger.info("External tool stub initialized (no external tools configured)")

    @property
    def is_available(self) -> bool:
        return self._available

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an external tool (not yet implemented).
        
        Returns:
            Error dict indicating external tools are not configured.
        """
        logger.warning("External tool execution attempted: %s (not configured)", tool_name)
        return {
            "success": False,
            "error": f"External tool '{tool_name}' is not configured. External tools are not yet available.",
            "tool_name": tool_name,
        }

    def list_available(self) -> list:
        """List available external tools (currently empty)."""
        return []
