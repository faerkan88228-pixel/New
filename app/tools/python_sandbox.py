"""
Python Execution Sandbox Tool
Runs Python scripts in an isolated process with stdout/stderr capture and timeout.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict
from app.config import settings
from app.tools.base import BaseTool, ToolResult


class PythonExecuteTool(BaseTool):
    name: str = "python_execute"
    description: str = (
        "Execute Python code in an isolated subprocess. "
        "Prints stdout and stderr. Ideal for data processing, math calculations, testing logic, or parsing formats."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python source code to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Execution timeout in seconds (default 30).",
                "default": 30
            }
        },
        "required": ["code"]
    }

    async def execute(self, code: str, timeout: int = 30, **kwargs) -> ToolResult:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = Path(tmp.name)

        try:
            process = await asyncio.create_subprocess_exec(
                "python3",
                str(tmp_path),
                cwd=str(settings.workspace_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_b, stderr_b = await asyncio.wait_for(process.communicate(), timeout=float(timeout))
                stdout = stdout_b.decode("utf-8", errors="replace")
                stderr = stderr_b.decode("utf-8", errors="replace")
                exit_code = process.returncode

                out = stdout
                if stderr:
                    out = f"{out}\n[STDERR]: {stderr}".strip()

                return ToolResult(
                    success=(exit_code == 0),
                    output=out if out else "(Executed with no stdout)",
                    error=None if exit_code == 0 else f"Process exited with code {exit_code}",
                    metadata={"exit_code": exit_code}
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
                    error=f"Python execution timed out after {timeout} seconds",
                    metadata={"exit_code": -1}
                )

        finally:
            if tmp_path.exists():
                tmp_path.unlink()
