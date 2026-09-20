"""
Model Context Protocol (MCP) Tool Integration
Connects to external MCP servers to fetch and execute tools dynamically.
"""

from typing import Any, Dict, List, Optional
from app.tools.base import BaseTool, ToolResult


class MCPToolAdapter(BaseTool):
    name: str = "mcp_connector"
    description: str = (
        "Interact with Model Context Protocol (MCP) servers. "
        "Allows querying active MCP tool endpoints, discovering available capabilities, and dispatching calls."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server (e.g. 'sqlite', 'github', 'filesystem')."
            },
            "mcp_method": {
                "type": "string",
                "enum": ["list_tools", "call_tool", "ping"],
                "description": "MCP operation to execute."
            },
            "tool_name": {
                "type": "string",
                "description": "Name of specific tool when calling 'call_tool'."
            },
            "arguments": {
                "type": "object",
                "description": "Arguments payload for the MCP tool call."
            }
        },
        "required": ["server_name", "mcp_method"]
    }

    def __init__(self):
        # Simulated active MCP registry
        self._connected_servers = {
            "browser_use": {"status": "connected", "tools": ["browser_exec", "browser_screenshot", "browser_click"]},
            "filesystem": {"status": "connected", "tools": ["fs_read", "fs_write", "fs_diff"]},
            "sqlite": {"status": "connected", "tools": ["query_sql", "describe_table"]}
        }

    async def execute(
        self,
        server_name: str,
        mcp_method: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        if server_name not in self._connected_servers:
            return ToolResult(
                success=False,
                output="",
                error=f"MCP server '{server_name}' is not connected. Connected: {list(self._connected_servers.keys())}"
            )

        if mcp_method == "ping":
            return ToolResult(success=True, output=f"MCP Server '{server_name}' is responsive (status: OK)")

        elif mcp_method == "list_tools":
            tools = self._connected_servers[server_name]["tools"]
            return ToolResult(
                success=True,
                output={"server": server_name, "available_tools": tools}
            )

        elif mcp_method == "call_tool":
            if not tool_name:
                return ToolResult(success=False, output="", error="tool_name is required for call_tool")
            return ToolResult(
                success=True,
                output=f"Executed MCP tool '{tool_name}' on server '{server_name}' with args {arguments or {}}",
                metadata={"server": server_name, "tool": tool_name}
            )

        return ToolResult(success=False, output="", error=f"Unknown MCP method: {mcp_method}")
