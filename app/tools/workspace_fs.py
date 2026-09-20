"""
Workspace File System Tools
File reading, writing, string replacement editing, and directory listing.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from app.config import settings
from app.tools.base import BaseTool, ToolResult


class FileOperationTool(BaseTool):
    name: str = "file_operator"
    description: str = (
        "Perform file system operations: 'read', 'write', 'append', 'replace', 'list', 'delete', or 'grep'. "
        "Operates relative to workspace directory."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "append", "replace", "list", "delete", "grep"],
                "description": "The file action to execute."
            },
            "path": {
                "type": "string",
                "description": "File or folder path relative to workspace or absolute."
            },
            "content": {
                "type": "string",
                "description": "Content for 'write' or 'append' operations."
            },
            "old_str": {
                "type": "string",
                "description": "Text to replace in 'replace' operation."
            },
            "new_str": {
                "type": "string",
                "description": "Replacement text in 'replace' operation."
            },
            "pattern": {
                "type": "string",
                "description": "Regex or substring pattern for 'grep' operation."
            }
        },
        "required": ["operation", "path"]
    }

    def _resolve_path(self, path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute():
            return p
        return (settings.workspace_dir / p).resolve()

    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        pattern: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            target = self._resolve_path(path)

            if operation == "read":
                if not target.exists():
                    return ToolResult(success=False, output="", error=f"File not found: {path}")
                text = target.read_text(encoding="utf-8", errors="replace")
                return ToolResult(
                    success=True,
                    output=text,
                    metadata={"size": len(text), "path": str(target)}
                )

            elif operation == "write":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content or "", encoding="utf-8")
                return ToolResult(
                    success=True,
                    output=f"Successfully written {len(content or '')} bytes to {path}",
                    metadata={"path": str(target)}
                )

            elif operation == "append":
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "a", encoding="utf-8") as f:
                    f.write(content or "")
                return ToolResult(
                    success=True,
                    output=f"Appended {len(content or '')} bytes to {path}",
                    metadata={"path": str(target)}
                )

            elif operation == "replace":
                if not target.exists():
                    return ToolResult(success=False, output="", error=f"File not found: {path}")
                text = target.read_text(encoding="utf-8", errors="replace")
                if old_str not in text:
                    return ToolResult(success=False, output="", error=f"old_str pattern not found in {path}")
                updated = text.replace(old_str, new_str or "", 1)
                target.write_text(updated, encoding="utf-8")
                return ToolResult(
                    success=True,
                    output=f"Successfully replaced match in {path}",
                    metadata={"path": str(target)}
                )

            elif operation == "list":
                if not target.exists():
                    return ToolResult(success=False, output="", error=f"Directory not found: {path}")
                if not target.is_dir():
                    return ToolResult(success=False, output="", error=f"Path is not a directory: {path}")
                entries = []
                for child in sorted(target.iterdir()):
                    kind = "DIR" if child.is_dir() else "FILE"
                    size = child.stat().st_size if child.is_file() else 0
                    entries.append(f"{kind:4}  {size:10} B  {child.name}")
                return ToolResult(
                    success=True,
                    output="\n".join(entries) if entries else "(Empty directory)",
                    metadata={"count": len(entries)}
                )

            elif operation == "delete":
                if not target.exists():
                    return ToolResult(success=False, output="", error=f"Path not found: {path}")
                if target.is_file():
                    target.unlink()
                elif target.is_dir():
                    import shutil
                    shutil.rmtree(target)
                return ToolResult(success=True, output=f"Deleted {path}")

            elif operation == "grep":
                if not target.exists():
                    return ToolResult(success=False, output="", error=f"Path not found: {path}")
                matches = []
                pat = pattern or old_str or ""
                if target.is_file():
                    lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
                    for idx, line in enumerate(lines, 1):
                        if pat.lower() in line.lower():
                            matches.append(f"{target.name}:{idx}: {line}")
                return ToolResult(
                    success=True,
                    output="\n".join(matches) if matches else f"No matches found for '{pat}'",
                    metadata={"match_count": len(matches)}
                )

            else:
                return ToolResult(success=False, output="", error=f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult(success=False, output="", error=f"File operation error: {str(e)}")
