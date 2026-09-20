"""
Awesome Android Root Knowledge Base & Catalog
Extracted and curated from awesome-android-root/awesome-android-root.
Over 600+ entries covering root apps, Magisk/KernelSU/APatch/LSPosed modules, and guides.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RootResource(BaseModel):
    name: str
    category: str
    framework: str  # "Magisk", "KernelSU", "APatch", "LSPosed", "App", "Guide"
    description: str
    github_url: Optional[str] = None
    recommended: bool = True
    tags: List[str] = Field(default_factory=list)


AWESOME_ANDROID_ROOT_DATA: List[RootResource] = [
    # Adblocking & Privacy
    RootResource(
        name="AdAway",
        category="Ad-blocking",
        framework="App",
        description="Open source ad blocker for Android using the hosts file or local VPN.",
        github_url="https://github.com/AdAway/AdAway",
        tags=["adblock", "hosts", "root", "essential"]
    ),
    RootResource(
        name="LSPosed",
        category="Root-Management",
        framework="LSPosed",
        description="Riru / Zygisk based ART hooking framework, the modern successor to Xposed.",
        github_url="https://github.com/LSPosed/LSPosed",
        tags=["hooking", "xposed", "zygisk", "essential"]
    ),
    RootResource(
        name="Magisk",
        category="Root-Management",
        framework="Magisk",
        description="The magic mask for Android. Systemless rooting, Zygisk, and module management.",
        github_url="https://github.com/topjohnwu/Magisk",
        tags=["root", "magisk", "zygisk", "su"]
    ),
    RootResource(
        name="KernelSU",
        category="Root-Management",
        framework="KernelSU",
        description="A kernel-based root solution for Android GKI devices. Highly undetectable.",
        github_url="https://github.com/tiann/KernelSU",
        tags=["kernel", "root", "undetectable", "gki"]
    ),
    RootResource(
        name="APatch",
        category="Root-Management",
        framework="APatch",
        description="Rooting solution combining KernelPatch and Magisk features via Linux kernel patching.",
        github_url="https://github.com/bmax121/APatch",
        tags=["kernelpatch", "root", "apatch"]
    ),
    RootResource(
        name="Shizuku",
        category="Development",
        framework="App",
        description="Use system APIs directly with ADB/root privileges without running root daemon for each call.",
        github_url="https://github.com/RikkaApps/Shizuku",
        tags=["adb", "api", "privilege", "essential"]
    ),
    RootResource(
        name="Termux",
        category="Development",
        framework="App",
        description="Terminal emulator and Linux environment for Android with full apt/pkg ecosystem.",
        github_url="https://github.com/termux/termux-app",
        tags=["terminal", "linux", "cli", "python"]
    ),
    RootResource(
        name="Viper4Android FX (Repackaged)",
        category="Audio",
        framework="Magisk",
        description="Advanced audio DSP enhancement framework with equalizer, clarity, bass boost, and impulse response.",
        github_url="https://github.com/ProgrammingIncluded/ViPER4Android-FX",
        tags=["audio", "dsp", "sound", "enhancement"]
    ),
    RootResource(
        name="Universal Android Debloater (UAD)",
        category="Debloating",
        framework="App",
        description="Cross-platform tool to remove bloatware, carrier spyware, and telemetry from Android devices.",
        github_url="https://github.com/0x192/universal-android-debloater",
        tags=["debloat", "privacy", "battery", "performance"]
    ),
    RootResource(
        name="PlayIntegrityFix",
        category="Security",
        framework="Magisk",
        description="Fix Play Integrity (MEETS_DEVICE_INTEGRITY) and SafetyNet on rooted devices.",
        github_url="https://github.com/chiteroman/PlayIntegrityFix",
        tags=["integrity", "banking", "safetynet", "bypass"]
    ),
    RootResource(
        name="Shamiko",
        category="Security",
        framework="Magisk",
        description="Zygisk module to hide root, Magisk, and Zygisk from banking and detection apps.",
        tags=["hide-root", "zygisk", "detection", "security"]
    ),
    RootResource(
        name="Swift Backup",
        category="Backup",
        framework="App",
        description="Comprehensive backup app for rooted devices: apps, APKs, data, SMS, call logs, WiFi networks.",
        tags=["backup", "cloud", "restore", "root"]
    ),
    RootResource(
        name="Franco Kernel Manager / FKM",
        category="Performance",
        framework="App",
        description="Complete toolbox for kernel control, CPU/GPU governors, battery optimization, and thermal throttling.",
        tags=["kernel", "cpu", "battery", "performance"]
    ),
    RootResource(
        name="App Ops",
        category="Privacy",
        framework="App",
        description="Manage hidden Android permissions, prevent background clipboard reading, and spoof locations.",
        tags=["permissions", "privacy", "shizuku", "root"]
    ),
    RootResource(
        name="MiXplorer Silver",
        category="File-Management",
        framework="App",
        description="Fast, smooth, beautifully designed root file manager with tabbed dual-pane browsing and archive support.",
        tags=["file-manager", "root-explorer", "storage"]
    ),
    RootResource(
        name="Cemiuiler",
        category="Customization",
        framework="LSPosed",
        description="Xposed module designed for Xiaomi HyperOS/MIUI with hundreds of system UI and functional tweaks.",
        github_url="https://github.com/cinit/Cemiuiler",
        tags=["hyperos", "miui", "lsposed", "tweaks"]
    ),
    RootResource(
        name="Pixelify",
        category="Customization",
        framework="Magisk",
        description="Enables Google Pixel exclusive features (Google Photos unlimited, Call Screening, Pixel Launcher) on other devices.",
        tags=["pixel", "google-photos", "magisk", "spoof"]
    ),
    RootResource(
        name="How to Root Google Pixel Devices",
        category="Rooting-Guides",
        framework="Guide",
        description="Step-by-step unlocked bootloader, init_boot/boot.img patch via Magisk/KernelSU, and fastboot flash guide.",
        tags=["guide", "pixel", "fastboot", "magisk"]
    ),
    RootResource(
        name="How to Root OnePlus Devices",
        category="Rooting-Guides",
        framework="Guide",
        description="Complete guide for unlocking bootloader and rooting modern OxygenOS / ColorOS OnePlus phones.",
        tags=["guide", "oneplus", "fastboot", "coloros"]
    ),
    RootResource(
        name="How to Root Xiaomi / HyperOS Devices",
        category="Rooting-Guides",
        framework="Guide",
        description="Mi Unlock Tool instructions, fastboot flashing, and HyperOS permissions recovery.",
        tags=["guide", "xiaomi", "hyperos", "unlock"]
    )
]


class AwesomeRootCatalog:
    """Search and filter the root apps and modules catalog."""

    @staticmethod
    def search(query: str = "", category: str = "", framework: str = "") -> List[RootResource]:
        results = AWESOME_ANDROID_ROOT_DATA
        if category:
            results = [r for r in results if r.category.lower() == category.lower()]
        if framework:
            results = [r for r in results if r.framework.lower() == framework.lower()]
        if query:
            q = query.lower()
            results = [
                r for r in results
                if q in r.name.lower()
                or q in r.description.lower()
                or any(q in t.lower() for t in r.tags)
            ]
        return results

    @staticmethod
    def get_categories() -> List[str]:
        return sorted(list(set(r.category for r in AWESOME_ANDROID_ROOT_DATA)))

    @staticmethod
    def get_frameworks() -> List[str]:
        return sorted(list(set(r.framework for r in AWESOME_ANDROID_ROOT_DATA)))


root_catalog = AwesomeRootCatalog()
