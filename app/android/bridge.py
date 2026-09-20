"""
Android ADB Bridge & Device Discovery
Coordinates real ADB connections (USB/TCP) and virtual sandbox fallback.
"""

import asyncio
from typing import Any, Dict, List, Optional
import adbutils

from app.android.virtual_device import virtual_device
from app.config import settings


class AndroidBridge:
    """Manages connection to local, network, and virtual Android devices."""

    def __init__(self):
        self._adb_client: Optional[adbutils.AdbClient] = None
        self._active_device_serial: Optional[str] = None
        self._init_client()

    def _init_client(self):
        try:
            self._adb_client = adbutils.AdbClient(host=settings.android.adb_host, port=settings.android.adb_port)
        except Exception:
            self._adb_client = None

    def list_devices(self) -> List[Dict[str, Any]]:
        devices = []
        # Real ADB devices
        if self._adb_client:
            try:
                for dev in self._adb_client.device_list():
                    try:
                        model = dev.prop.model or "Android Device"
                    except Exception:
                        model = "Android Device"
                    devices.append({
                        "serial": dev.serial,
                        "model": model,
                        "type": "physical",
                        "status": "device"
                    })
            except Exception:
                pass

        # Virtual device is always present for testing & simulation
        devices.append({
            "serial": virtual_device.device_id,
            "model": f"{virtual_device.brand} {virtual_device.model} (Virtual)",
            "type": "virtual",
            "status": "online"
        })
        return devices

    def connect_network_device(self, address: str) -> str:
        """Connect to device via TCP/IP (e.g. '192.168.1.100:5555')."""
        if not self._adb_client:
            self._init_client()
        if self._adb_client:
            try:
                result = self._adb_client.connect(address)
                return f"ADB connect: {result}"
            except Exception as e:
                return f"ADB connect failed: {str(e)}"
        return "ADB client not initialized"

    def get_device(self, serial: Optional[str] = None):
        """Get device handle by serial or active default."""
        target_serial = serial or self._active_device_serial
        if not target_serial or target_serial == virtual_device.device_id:
            return ("virtual", virtual_device)

        if self._adb_client:
            try:
                for d in self._adb_client.device_list():
                    if d.serial == target_serial:
                        return ("physical", d)
            except Exception:
                pass

        # Fallback to virtual
        return ("virtual", virtual_device)

    def set_active_device(self, serial: str):
        self._active_device_serial = serial


android_bridge = AndroidBridge()
