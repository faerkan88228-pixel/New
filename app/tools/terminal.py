"""
Terminal / Bash Tool
Executes shell commands in a safe subprocess environment with timeouts.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Dict
from app.config import settings
from app.tools.base import BaseTool, ToolResult


class BashTool(BaseTool):
    name: str = "bash"
    description: str = (
        "Execute a shell/bash command on the host environment. "
        "Useful for running scripts, installing packages, checking git status, inspecting processes, or running system utilities."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute."
            },
            "cwd": {
                "type": "string",
                "description": "Working directory path. Defaults to workspace directory.",
                "default": str(settings.workspace_dir)
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds. Default is 30.",
                "default": 30
            }
        },
        "required": ["command"]
    }

    async def execute(self, command: str, cwd: str = None, timeout: int = 30) -> ToolResult:
        work_dir = Path(cwd) if cwd else settings.workspace_dir
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=float(timeout)
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = process.returncode

                output = stdout
                if stderr:
                    output = f"{output}\n[STDERR]: {stderr}".strip()

                return ToolResult(
                    success=(exit_code == 0),
                    output=output if output else "(Command executed with no output)",
                    error=None if exit_code == 0 else f"Command exited with code {exit_code}",
                    metadata={"exit_code": exit_code, "cwd": str(work_dir)}
                )

            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {timeout} seconds",
                    metadata={"exit_code": -1}
                )

        except Exception as ex:
            return ToolResult(
                success=False,
                output="",
                error=f"Subprocess spawn error: {str(ex)}"
            )
