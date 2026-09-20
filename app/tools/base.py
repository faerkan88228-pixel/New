"""
Agent Tool Base & Registry
Unified interface for OpenManus, KODE SDK, and MCP tools.
"""

import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema format

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI / OpenManus tool specification format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


class ToolRegistry:
    """Central registry of executable agent tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' not found in registry. Available tools: {list(self._tools.keys())}"
            )
        try:
            return await tool.execute(**arguments)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution error in tool '{name}': {str(e)}"
            )


tool_registry = ToolRegistry()
