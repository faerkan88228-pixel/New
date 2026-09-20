# Android Device Commander & Rooting Guide

OmniNexus Studio integrates the complete knowledge and tooling from **awesome-android-root** alongside pure Python ADB automation.

---

## 1. Connecting Devices

### USB Connection
1. Enable **Developer Options** on your Android device (Settings -> About Phone -> tap "Build Number" 7 times).
2. Enable **USB Debugging** and **USB Debugging (Security settings)**.
3. Connect device via USB. The status indicator in OmniNexus will automatically turn green.

### Wireless ADB (TCP/IP)
1. On your phone: Settings -> Developer Options -> Wireless debugging.
2. Note the IP address and port (e.g. `192.168.1.100:5555`).
3. In the OmniNexus Android tab or via API:
   ```bash
   curl -X POST http://localhost:8000/api/android/connect -H "Content-Type: application/json" -d '{"address": "192.168.1.100:5555"}'
   ```

### Virtual Sandbox Device
When no physical device is connected, OmniNexus Studio provides an active **Virtual Pixel 9 Pro (Android 15)** environment with KernelSU root privileges, allowing you to test taps, swiping, debloating, and root scripts immediately.

---

## 2. Rooting Solutions Compared

| Solution | Detection Status | Architecture | Best For |
|---|---|---|---|
| **KernelSU** | Highly Undetectable | Kernel GKI hook | Modern Android 13-15 devices |
| **Magisk** | Universal | Systemless boot patch | Broad compatibility, Zygisk modules |
| **APatch** | High Undetectable | KernelPatch + SuperKey | Devices without official GKI support |
| **Shizuku** | No Root Required | ADB privilege service | Non-rooted automation and app ops |

---

## 3. Essential Root Modules Curated in OmniNexus

1. **AdAway**: System-wide ad-blocking via `/system/etc/hosts`.
2. **LSPosed**: Successor to Xposed for runtime ART hooking.
3. **PlayIntegrityFix**: Bypasses Google Play Integrity restrictions for banking apps on rooted phones.
4. **Shamiko**: Advanced Zygisk module for hiding root detection.
5. **Universal Android Debloater (UAD)**: Disables pre-installed carrier spyware and manufacturer bloat.
6. **Viper4Android FX**: High-end parametric audio DSP engine.
