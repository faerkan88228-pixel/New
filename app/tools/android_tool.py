"""
Android Device Automation Tool for Agent
Enables agent to inspect device, run root commands, simulate touches, and inspect apps.
"""

from typing import Any, Dict, Optional
from app.android.controller import android_controller
from app.tools.base import BaseTool, ToolResult


class AndroidCommandTool(BaseTool):
    name: str = "android_device"
    description: str = (
        "Interact with connected Android devices or virtual Android testbed. "
        "Supports actions: 'info', 'shell', 'root_shell', 'tap', 'swipe', 'key', 'text', 'screenshot', 'list_packages', 'toggle_package'."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["info", "shell", "root_shell", "tap", "swipe", "key", "text", "screenshot", "list_packages", "toggle_package"],
                "description": "The Android action to perform."
            },
            "command": {
                "type": "string",
                "description": "Shell command to run for 'shell' or 'root_shell'."
            },
            "x": {"type": "integer", "description": "X coordinate for 'tap'."},
            "y": {"type": "integer", "description": "Y coordinate for 'tap'."},
            "x1": {"type": "integer", "description": "Start X for 'swipe'."},
            "y1": {"type": "integer", "description": "Start Y for 'swipe'."},
            "x2": {"type": "integer", "description": "End X for 'swipe'."},
            "y2": {"type": "integer", "description": "End Y for 'swipe'."},
            "text": {"type": "string", "description": "Text to type into device."},
            "keycode": {"type": "string", "description": "Keycode for 'key' (e.g. KEYCODE_HOME, KEYCODE_BACK)."},
            "package": {"type": "string", "description": "Package name for 'toggle_package'."},
            "enable": {"type": "boolean", "description": "Enable (true) or disable/debloat (false)."}
        },
        "required": ["action"]
    }

    async def execute(
        self,
        action: str,
        command: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x1: Optional[int] = None,
        y1: Optional[int] = None,
        x2: Optional[int] = None,
        y2: Optional[int] = None,
        text: Optional[str] = None,
        keycode: Optional[str] = None,
        package: Optional[str] = None,
        enable: Optional[bool] = None,
        **kwargs
    ) -> ToolResult:
        try:
            if action == "info":
                info = android_controller.get_info()
                return ToolResult(success=True, output=info)

            elif action == "shell":
                res = android_controller.execute_shell(command or "id", as_root=False)
                return ToolResult(success=(res.get("exit_code") == 0), output=res.get("stdout", ""))

            elif action == "root_shell":
                res = android_controller.execute_shell(command or "whoami", as_root=True)
                return ToolResult(success=(res.get("exit_code") == 0), output=res.get("stdout", ""))

            elif action == "tap":
                out = android_controller.tap(x or 200, y or 400)
                return ToolResult(success=True, output=out)

            elif action == "swipe":
                out = android_controller.swipe(x1 or 200, y1 or 600, x2 or 200, y2 or 200)
                return ToolResult(success=True, output=out)

            elif action == "key":
                out = android_controller.press_key(keycode or "KEYCODE_HOME")
                return ToolResult(success=True, output=out)

            elif action == "text":
                out = android_controller.input_text(text or "")
                return ToolResult(success=True, output=out)

            elif action == "screenshot":
                b64 = android_controller.get_screenshot_base64()
                return ToolResult(
                    success=True,
                    output="Screenshot captured successfully.",
                    metadata={"image_base64_preview": f"data:image/png;base64,{b64[:100]}..."}
                )

            elif action == "list_packages":
                pkgs = android_controller.list_packages()
                return ToolResult(success=True, output=pkgs)

            elif action == "toggle_package":
                if not package:
                    return ToolResult(success=False, output="", error="Package name required.")
                out = android_controller.toggle_package(package, enable if enable is not None else True)
                return ToolResult(success=True, output=out)

            else:
                return ToolResult(success=False, output="", error=f"Unknown action: {action}")

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Android action error: {str(e)}")
