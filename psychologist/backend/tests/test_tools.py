"""
Tool Agent tests
"""

import pytest
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.agent.schemas import AgentRequest
from backend.tools.tool_agent import ToolAgent

@pytest.fixture
def tool_agent():
    agent = ToolAgent()
    agent.initialize()
    return agent

def test_tool_registration(tool_agent):
    """Verify all 4 tools are registered on initialization."""
    tools = tool_agent.registry.list_tools()
    assert len(tools) == 4
    assert "list_dir" in tools
    assert "read_file" in tools
    assert "project_scan" in tools
    assert "system_info" in tools

def test_tool_list_purpose(tool_agent):
    """Test listing available tools via API."""
    req = AgentRequest(text="", metadata={"purpose": "list"})
    res = tool_agent.safe_process(req)
    
    assert res.success is True
    assert "tools" in res.metadata
    assert len(res.metadata["tools"]) == 4

def test_tool_execute_system_info(tool_agent):
    """Test executing system_info tool."""
    req = AgentRequest(
        text="",
        metadata={
            "purpose": "execute",
            "tool_calls": [{"tool_name": "system_info", "arguments": {}}]
        }
    )
    res = tool_agent.safe_process(req)
    
    assert res.success is True
    results = res.metadata["execution_results"]
    assert len(results) == 1
    assert results[0]["success"] is True
    assert "os" in results[0]["result"]

def test_tool_execute_list_dir(tool_agent):
    """Test executing list_dir tool on current directory."""
    req = AgentRequest(
        text="",
        metadata={
            "purpose": "execute",
            "tool_calls": [{"tool_name": "list_dir", "arguments": {"path": "."}}]
        }
    )
    res = tool_agent.safe_process(req)
    
    assert res.success is True
    results = res.metadata["execution_results"]
    assert results[0]["success"] is True

def test_tool_auto_deduce_from_text(tool_agent):
    """Test that tool calls are auto-deduced from user text."""
    req = AgentRequest(
        text="What is my CPU usage?",
        metadata={"purpose": "execute"}
    )
    res = tool_agent.safe_process(req)
    
    assert res.success is True
    results = res.metadata["execution_results"]
    assert len(results) == 1
    assert results[0]["tool_name"] == "system_info"

def test_tool_not_found(tool_agent):
    """Test error handling for non-existent tool."""
    req = AgentRequest(
        text="",
        metadata={
            "purpose": "execute",
            "tool_calls": [{"tool_name": "nonexistent_tool", "arguments": {}}]
        }
    )
    res = tool_agent.safe_process(req)
    
    results = res.metadata["execution_results"]
    assert results[0]["success"] is False
    assert "not found" in results[0]["error"]
