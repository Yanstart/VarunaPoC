"""
Configuration OpenSlide Auto-Detection

Détecte automatiquement l'environnement (Windows/Docker) et configure OpenSlide.

Usage:
    import config_openslide_auto  # AVANT tout import d'openslide

Environnements supportés:
- Windows: MSYS2/UCRT64, OpenSlide Windows binaries
- Docker: Debian/Ubuntu avec apt packages
- Linux: System packages
"""

import os
import platform
import sys


def configure_openslide():
    """
    Configure OpenSlide selon l'environnement détecté.

    Detection logic:
    1. Check DOCKER_CONTAINER env var (set in Dockerfile)
    2. Check if running on Windows
    3. Check if running on Linux with system packages
    """
    # Check if running in Docker
    if os.environ.get("DOCKER_CONTAINER") == "true":
        print("[INFO] Running in Docker container")
        return _configure_docker()

    # Check if running on Windows
    if platform.system() == "Windows":
        print("[INFO] Running on Windows")
        return _configure_windows()

    # Default: assume Linux with system packages
    print("[INFO] Running on Linux (system packages)")
    return _configure_linux()


def _configure_windows():
    """Configure OpenSlide pour Windows (MSYS2)."""
    # Path MSYS2 UCRT64
    OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"

    if not os.path.exists(OPENSLIDE_PATH):
        print(f"[WARNING] OpenSlide path not found: {OPENSLIDE_PATH}")
        print("Please download OpenSlide from: https://openslide.org/download/")
        print("Or install via MSYS2: pacman -S mingw-w64-ucrt-x86_64-openslide")
        return False

    # Python 3.8+ recommande os.add_dll_directory()
    if sys.version_info >= (3, 8) and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(OPENSLIDE_PATH)
            print(f"[OK] OpenSlide DLL directory added: {OPENSLIDE_PATH}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add DLL directory: {e}")
            return False
    else:
        # Fallback pour Python < 3.8
        os.environ["PATH"] = OPENSLIDE_PATH + os.pathsep + os.environ.get("PATH", "")
        print(f"[OK] OpenSlide added to PATH: {OPENSLIDE_PATH}")
        return True


def _configure_docker():
    """Configure OpenSlide pour Docker (Debian/Ubuntu packages)."""
    # Dans Docker, OpenSlide est installé comme package système
    # via: apt-get install libopenslide0 openslide-tools
    common_paths = [
        "/usr/lib/x86_64-linux-gnu/libopenslide.so.0",
        "/usr/lib/libopenslide.so.0",
        "/usr/local/lib/libopenslide.so.0",
    ]

    for lib_path in common_paths:
        if os.path.exists(lib_path):
            print(f"[OK] OpenSlide library found: {lib_path}")
            return True

    print("[WARNING] OpenSlide library not found in common paths")
    print("Expected installation: apt-get install libopenslide0 openslide-tools")
    return False


def _configure_linux():
    """Configure OpenSlide pour Linux (system packages)."""
    # Même logique que Docker (packages système)
    return _configure_docker()


# Auto-configure au import
configure_openslide()
