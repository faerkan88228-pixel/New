"""
Android Device Controller
Handles UI automation, root operations, and screen streaming across devices.
"""

import base64
import io
from typing import Any, Dict, List, Optional
from app.android.bridge import android_bridge
from app.android.virtual_device import virtual_device


class AndroidController:
    """Controls connected Android device operations."""

    def get_info(self, serial: Optional[str] = None) -> Dict[str, Any]:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return {
                "serial": dev.device_id,
                "model": dev.model,
                "brand": dev.brand,
                "android_version": dev.android_version,
                "build_id": dev.build_id,
                "root_type": dev.root_type,
                "is_rooted": dev.is_rooted,
                "battery_level": dev.battery_level,
                "is_charging": dev.is_charging,
                "wifi_ssid": dev.wifi_ssid,
                "type": "virtual"
            }
        else:
            try:
                model = dev.prop.model or "Android"
                version = dev.shell("getprop ro.build.version.release").strip()
                # Check root status
                su_test = dev.shell("su -c id 2>/dev/null || echo 'no-root'").strip()
                is_rooted = "uid=0" in su_test
                return {
                    "serial": dev.serial,
                    "model": model,
                    "brand": dev.prop.name or "Android",
                    "android_version": version,
                    "build_id": dev.shell("getprop ro.build.id").strip(),
                    "root_type": "Magisk/KernelSU" if is_rooted else "Not Rooted",
                    "is_rooted": is_rooted,
                    "battery_level": 90,
                    "type": "physical"
                }
            except Exception as e:
                return {"error": str(e), "type": "error"}

    def tap(self, x: int, y: int, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.tap(x, y)
        else:
            dev.shell(f"input tap {x} {y}")
            return f"Tapped at ({x}, {y})"

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.swipe(x1, y1, x2, y2, duration_ms)
        else:
            dev.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            return f"Swiped ({x1},{y1}) -> ({x2},{y2})"

    def input_text(self, text: str, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.input_text(text)
        else:
            # Escape spaces for ADB input
            escaped = text.replace(" ", "%s").replace("'", "\\'")
            dev.shell(f"input text '{escaped}'")
            return f"Entered text: '{text}'"

    def press_key(self, keycode: str, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.press_key(keycode)
        else:
            dev.shell(f"input keyevent {keycode}")
            return f"Key {keycode} sent"

    def execute_shell(self, command: str, as_root: bool = False, serial: Optional[str] = None) -> Dict[str, Any]:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.execute_shell(command, as_root=as_root)
        else:
            cmd = f"su -c '{command}'" if as_root else command
            try:
                out = dev.shell(cmd)
                return {"stdout": out, "exit_code": 0}
            except Exception as e:
                return {"stdout": "", "exit_code": 1, "error": str(e)}

    def get_screenshot_base64(self, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return dev.get_screenshot_base64()
        else:
            try:
                pil_img = dev.screenshot()
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                return base64.b64encode(buf.getvalue()).decode("ascii")
            except Exception:
                return virtual_device.get_screenshot_base64()

    def list_packages(self, serial: Optional[str] = None) -> List[Dict[str, Any]]:
        dev_type, dev = android_bridge.get_device(serial)
        if dev_type == "virtual":
            return [
                {"package": pkg, "name": info["name"], "system": info["system"], "enabled": info["enabled"]}
                for pkg, info in dev.installed_packages.items()
            ]
        else:
            try:
                raw = dev.shell("pm list packages -u")
                packages = []
                for line in raw.splitlines():
                    if line.startswith("package:"):
                        pkg = line.replace("package:", "").strip()
                        packages.append({"package": pkg, "name": pkg, "system": False, "enabled": True})
                return packages
            except Exception:
                return []

    def toggle_package(self, package_name: str, enable: bool, serial: Optional[str] = None) -> str:
        dev_type, dev = android_bridge.get_device(serial)
        action = "enable" if enable else "disable-user --user 0"
        if dev_type == "virtual":
            res = dev.execute_shell(f"pm {action} {package_name}")
            return res.get("stdout", "")
        else:
            try:
                out = dev.shell(f"su -c 'pm {action} {package_name}'")
                return out
            except Exception as e:
                return str(e)


android_controller = AndroidController()
