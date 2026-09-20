"""
Android Virtual Sandbox Device
Provides full simulation of a rooted Android 15 device (Google Pixel 9 Pro / KernelSU)
for testing automation workflows, package management, and ADB commands.
"""

import base64
import io
import time
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont


class VirtualAndroidDevice:
    """Simulated Android device state and screen buffer."""

    def __init__(self, device_id: str = "virtual-pixel9"):
        self.device_id = device_id
        self.model = "Pixel 9 Pro"
        self.brand = "Google"
        self.android_version = "15 (Vanilla Ice Cream)"
        self.build_id = "AP2A.240905.003"
        self.root_type = "KernelSU (v0.9.5)"
        self.is_rooted = True
        self.battery_level = 88
        self.is_charging = True
        self.wifi_ssid = "OmniNexus-HighSpeed-5G"
        self.screen_width = 400
        self.screen_height = 800
        self.current_app = "com.google.android.apps.nexus"
        self.last_action = "System Boot Complete"
        self.last_touch = (200, 400)
        
        # Package catalog
        self.installed_packages = {
            "com.google.android.apps.nexus": {"name": "Nexus Hub", "system": False, "enabled": True},
            "com.android.chrome": {"name": "Chrome Browser", "system": True, "enabled": True},
            "com.termux": {"name": "Termux", "system": False, "enabled": True},
            "moe.shizuku.privileged.api": {"name": "Shizuku", "system": False, "enabled": True},
            "org.lsposed.manager": {"name": "LSPosed", "system": False, "enabled": True},
            "me.weishu.kernelsu": {"name": "KernelSU", "system": False, "enabled": True},
            "org.adaway": {"name": "AdAway", "system": False, "enabled": True},
            "com.facebook.katana": {"name": "Facebook (Bloatware)", "system": True, "enabled": False},
            "com.facebook.system": {"name": "Facebook App Installer", "system": True, "enabled": False},
            "com.google.android.youtube": {"name": "YouTube", "system": True, "enabled": True},
        }

    def tap(self, x: int, y: int) -> str:
        self.last_touch = (x, y)
        self.last_action = f"Tap at ({x}, {y})"
        return f"Simulated tap at x={x}, y={y}"

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> str:
        self.last_action = f"Swipe ({x1},{y1}) -> ({x2},{y2})"
        return f"Simulated swipe from ({x1},{y1}) to ({x2},{y2})"

    def input_text(self, text: str) -> str:
        self.last_action = f"Typed text: '{text[:20]}...'"
        return f"Typed text successfully"

    def press_key(self, keycode: str) -> str:
        key_names = {
            "KEYCODE_HOME": "Home button",
            "KEYCODE_BACK": "Back button",
            "KEYCODE_APP_SWITCH": "Recent Apps",
            "KEYCODE_POWER": "Power toggle",
            "KEYCODE_VOLUME_UP": "Volume Up",
            "KEYCODE_VOLUME_DOWN": "Volume Down"
        }
        self.last_action = f"Pressed {key_names.get(keycode, keycode)}"
        return f"Keyevent {keycode} triggered"

    def execute_shell(self, command: str, as_root: bool = False) -> Dict[str, Any]:
        """Simulate execution of shell and root commands."""
        cmd = command.strip()
        self.last_action = f"Shell: '{cmd[:30]}'"

        if cmd.startswith("su") or as_root:
            if "id" in cmd or "whoami" in cmd:
                return {"stdout": "uid=0(root) gid=0(root) groups=0(root) context=u:r:su:s0\n", "exit_code": 0}
            if "uname" in cmd:
                return {"stdout": "Linux localhost 6.1.75-android15-gki-kernelsu #1 SMP PREEMPT\n", "exit_code": 0}

        if cmd == "getprop ro.product.model":
            return {"stdout": f"{self.model}\n", "exit_code": 0}
        elif cmd == "getprop ro.build.version.release":
            return {"stdout": f"15\n", "exit_code": 0}
        elif cmd.startswith("pm list packages"):
            lines = [f"package:{pkg}" for pkg, info in self.installed_packages.items() if info["enabled"]]
            return {"stdout": "\n".join(lines) + "\n", "exit_code": 0}
        elif cmd.startswith("pm disable-user") or cmd.startswith("pm disable"):
            parts = cmd.split()
            pkg = parts[-1]
            if pkg in self.installed_packages:
                self.installed_packages[pkg]["enabled"] = False
                return {"stdout": f"Package {pkg} new state: disabled-user\n", "exit_code": 0}
            return {"stdout": f"Error: package {pkg} not found\n", "exit_code": 1}
        elif cmd.startswith("pm enable"):
            parts = cmd.split()
            pkg = parts[-1]
            if pkg in self.installed_packages:
                self.installed_packages[pkg]["enabled"] = True
                return {"stdout": f"Package {pkg} new state: enabled\n", "exit_code": 0}
            return {"stdout": f"Error: package {pkg} not found\n", "exit_code": 1}
        elif cmd == "dumpsys battery":
            return {
                "stdout": (
                    f"Current Battery Service state:\n"
                    f"  AC powered: true\n"
                    f"  level: {self.battery_level}\n"
                    f"  scale: 100\n"
                    f"  voltage: 4210\n"
                    f"  temperature: 285 (28.5 C)\n"
                    f"  technology: Li-ion\n"
                ),
                "exit_code": 0
            }
        else:
            return {"stdout": f"[simulated-adb-shell]: executed '{cmd}' successfully\n", "exit_code": 0}

    def render_screenshot_png(self) -> bytes:
        """Draw an informative live Android screen buffer."""
        img = Image.new("RGB", (self.screen_width, self.screen_height), color=(18, 22, 32))
        draw = ImageDraw.Draw(img)

        # Status Bar
        draw.rectangle([0, 0, self.screen_width, 40], fill=(10, 14, 22))
        draw.text((15, 12), time.strftime("%H:%M"), fill=(220, 225, 235))
        draw.text((self.screen_width - 120, 12), f"5G  88% 🔋", fill=(220, 225, 235))

        # Device Header
        draw.rectangle([15, 60, self.screen_width - 15, 160], fill=(28, 36, 52), outline=(50, 70, 100))
        draw.text((30, 75), f"📱 {self.brand} {self.model}", fill=(255, 255, 255))
        draw.text((30, 100), f"Android {self.android_version} • Root: {self.root_type}", fill=(74, 222, 128))
        draw.text((30, 125), f"Status: ADB Online • Wi-Fi Active", fill=(148, 163, 184))

        # Active App Panel
        draw.rectangle([15, 180, self.screen_width - 15, 300], fill=(22, 27, 40), outline=(40, 55, 80))
        draw.text((30, 195), "ACTIVE APPLICATION", fill=(148, 163, 184))
        draw.text((30, 225), "OmniNexus Android Commander", fill=(96, 165, 250))
        draw.text((30, 255), f"Last Action: {self.last_action}", fill=(245, 158, 11))

        # Touch Indicator
        tx, ty = self.last_touch
        draw.ellipse([tx - 12, ty - 12, tx + 12, ty + 12], outline=(239, 68, 68), width=2)
        draw.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=(239, 68, 68))

        # Installed Root Apps List preview
        draw.rectangle([15, 320, self.screen_width - 15, 720], fill=(25, 32, 46), outline=(40, 55, 80))
        draw.text((30, 335), "INSTALLED PACKAGES & ROOT MODULES", fill=(148, 163, 184))
        
        y_pos = 370
        for pkg, info in list(self.installed_packages.items())[:8]:
            color = (255, 255, 255) if info["enabled"] else (150, 80, 80)
            tag = "✓ ACTIVE" if info["enabled"] else "✗ DEBLOATED"
            tag_color = (74, 222, 128) if info["enabled"] else (248, 113, 113)
            draw.text((30, y_pos), f"{info['name']}", fill=color)
            draw.text((self.screen_width - 110, y_pos), tag, fill=tag_color)
            draw.text((30, y_pos + 18), pkg, fill=(100, 116, 139))
            y_pos += 42

        # Navigation Bar
        draw.rectangle([0, self.screen_height - 50, self.screen_width, self.screen_height], fill=(10, 14, 22))
        draw.text((self.screen_width // 4 - 10, self.screen_height - 35), "◁", fill=(200, 200, 200))
        draw.text((self.screen_width // 2 - 10, self.screen_height - 35), "○", fill=(200, 200, 200))
        draw.text((3 * self.screen_width // 4 - 10, self.screen_height - 35), "□", fill=(200, 200, 200))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def get_screenshot_base64(self) -> str:
        png_bytes = self.render_screenshot_png()
        return base64.b64encode(png_bytes).decode("ascii")


virtual_device = VirtualAndroidDevice()
