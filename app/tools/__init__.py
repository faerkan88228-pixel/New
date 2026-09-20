"""
Agent Tools Module
Registers default tools into the central tool registry.
"""

from app.tools.base import tool_registry, BaseTool, ToolResult
from app.tools.terminal import BashTool
from app.tools.workspace_fs import FileOperationTool
from app.tools.web_intelligence import WebSearchTool, FetchPageTool
from app.tools.python_sandbox import PythonExecuteTool
from app.tools.tts_tool import TTSSpeechTool
from app.tools.android_tool import AndroidCommandTool
from app.tools.mcp_client import MCPToolAdapter


def register_default_tools():
    """Register all core agent tools."""
    tool_registry.register(BashTool())
    tool_registry.register(FileOperationTool())
    tool_registry.register(WebSearchTool())
    tool_registry.register(FetchPageTool())
    tool_registry.register(PythonExecuteTool())
    tool_registry.register(TTSSpeechTool())
    tool_registry.register(AndroidCommandTool())
    tool_registry.register(MCPToolAdapter())


# Initialize immediately on import
register_default_tools()
