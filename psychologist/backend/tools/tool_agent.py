"""
Tool Agent

Main coordinator for managing and executing tools, validating parameters,
and returning formatted execution responses.
"""

import json
from typing import Dict, Any, List

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from .schemas import ToolDefinition
from .registry import ToolRegistry
from .file_tools import list_directory, read_file_content
from .project_tools import get_project_summary
from .system_tools import get_system_info

class ToolAgent(BaseAgent):
    """
    Tool Agent encapsulates local tool registration and execution.
    """

    def __init__(self):
        super().__init__()
        self.registry = ToolRegistry()

    def _get_agent_name(self) -> str:
        return "tool"

    def initialize(self) -> bool:
        # Register file list tool
        self.registry.register_tool(
            ToolDefinition(
                name="list_dir",
                description="List directory files and folders",
                input_schema={"path": "string"},
                output_schema={"success": "boolean", "files": "array"},
                risk_level="low"
            ),
            list_directory
        )
        
        # Register file read tool
        self.registry.register_tool(
            ToolDefinition(
                name="read_file",
                description="Read contents of a local workspace file",
                input_schema={"path": "string"},
                output_schema={"success": "boolean", "content": "string"},
                risk_level="medium"
            ),
            read_file_content
        )
        
        # Register project scanner
        self.registry.register_tool(
            ToolDefinition(
                name="project_scan",
                description="Scan project directory statistics",
                input_schema={},
                output_schema={"success": "boolean", "python_files_count": "number"},
                risk_level="low"
            ),
            get_project_summary
        )

        # Register system info tool
        self.registry.register_tool(
            ToolDefinition(
                name="system_info",
                description="Retrieve local system CPU, memory usage stats",
                input_schema={},
                output_schema={"success": "boolean", "os": "string"},
                risk_level="low"
            ),
            get_system_info
        )

        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        purpose = request.metadata.get("purpose", "execute")
        
        if purpose == "list":
            tools_list = []
            for t_name, t_def in self.registry.list_tools().items():
                tools_list.append({
                    "name": t_def.name,
                    "description": t_def.description,
                    "risk_level": t_def.risk_level
                })
            return AgentResponse(
                success=True,
                agent=self.name,
                response=f"Found {len(tools_list)} tools.",
                metadata={"tools": tools_list}
            )

        elif purpose == "execute":
            tool_calls = request.metadata.get("tool_calls", [])
            if not tool_calls:
                # Deduce tool call from intent / text
                text_lower = request.text.lower()
                if "system" in text_lower or "cpu" in text_lower:
                    tool_calls = [{"tool_name": "system_info", "arguments": {}}]
                elif "project" in text_lower:
                    tool_calls = [{"tool_name": "project_scan", "arguments": {}}]
                elif "list" in text_lower or "dir" in text_lower:
                    tool_calls = [{"tool_name": "list_dir", "arguments": {"path": "."}}]
                else:
                    return AgentResponse.error(self.name, "No tool calls detected or provided.")

            results = []
            for call in tool_calls:
                name = call.get("tool_name")
                args = call.get("arguments", {})
                
                tool_def = self.registry.get_tool(name)
                if not tool_def:
                    results.append({"tool_name": name, "success": False, "error": f"Tool '{name}' not found."})
                    continue
                    
                try:
                    res = self.registry.execute(name, args)
                    results.append({"tool_name": name, "success": True, "result": res})
                except Exception as e:
                    results.append({"tool_name": name, "success": False, "error": str(e)})

            success = any(r["success"] for r in results)
            response_text = json.dumps(results)
            
            return AgentResponse(
                success=success,
                agent=self.name,
                intent="tool_execution",
                response=response_text,
                confidence=1.0,
                risk_level="low",
                metadata={"execution_results": results}
            )
            
        return AgentResponse.error(self.name, f"Unknown tool agent purpose: {purpose}")
