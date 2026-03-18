r"""
Configuration OpenSlide — cross-platform library path setup.

This module MUST be imported BEFORE any openslide or pyvips import.
It configures the dynamic linker to find the correct OpenSlide library:

- **Windows**: Adds the OpenSlide DLL directory via os.add_dll_directory().
- **Linux**: Ensures libvips loads OpenSlide 4.0 from the openslide-bin
  pip wheel instead of a potentially older system libopenslide.so.0.
  Creates a .so.0 → .so.1 compatibility symlink and, if LD_LIBRARY_PATH
  is not already set, re-execs the process with the correct path.

Import in main.py:
    import config_openslide  # AVANT tout import openslide/pyvips
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================
# Windows: DLL path configuration
# ============================================

OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"


def _configure_windows():
    """Configure OpenSlide DLL path on Windows."""
    if not os.path.exists(OPENSLIDE_PATH):
        return False

    if sys.version_info >= (3, 8) and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(OPENSLIDE_PATH)
            return True
        except Exception:
            return False
    else:
        os.environ["PATH"] = OPENSLIDE_PATH + os.pathsep + os.environ.get("PATH", "")
        return True


# ============================================
# Linux: openslide-bin + libvips compatibility
# ============================================


def _configure_linux():
    """Ensure libvips loads OpenSlide 4.0 from the openslide-bin wheel.

    Problem: libvips dynamically loads libopenslide.so.0 (soname for 3.x).
    openslide-bin ships OpenSlide 4.0 as libopenslide.so.1 (new soname).
    Without intervention, libvips finds the system 3.4.1 library.

    Solution:
    1. Create a .so.0 → .so.1 symlink in the openslide-bin directory
    2. Prepend that directory to LD_LIBRARY_PATH
    3. Re-exec the process so the dynamic linker picks up the new path

    The re-exec only happens once: on the second exec, LD_LIBRARY_PATH
    is already set, so we skip straight through.
    """
    try:
        import openslide_bin
    except ImportError:
        return  # openslide-bin not installed, use system library

    bin_dir = Path(openslide_bin.__file__).parent
    bin_dir_str = str(bin_dir)

    # Step 1: Create .so.0 → .so.1 symlink for soname compatibility
    so1 = bin_dir / "libopenslide.so.1"
    so0 = bin_dir / "libopenslide.so.0"
    if so1.exists() and not so0.exists():
        try:
            so0.symlink_to(so1.name)
            logger.info("Created libopenslide.so.0 -> .so.1 symlink in %s", bin_dir)
        except OSError as e:
            logger.warning("Cannot create OpenSlide symlink: %s", e)
            return

    if not so0.exists():
        return  # No .so.0 available at all

    # Step 2: Check if LD_LIBRARY_PATH already includes openslide-bin
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if bin_dir_str in ld_path.split(os.pathsep):
        return  # Already configured — no re-exec needed

    # Step 3: Set LD_LIBRARY_PATH and re-exec the process
    new_ld_path = bin_dir_str + (os.pathsep + ld_path if ld_path else "")
    os.environ["LD_LIBRARY_PATH"] = new_ld_path

    # Skip re-exec if explicitly disabled (e.g. for test runners)
    if os.environ.get("OPENSLIDE_NO_REEXEC"):
        return

    # Read the actual command line to re-exec faithfully.
    # os.execv needs an absolute path for the executable, so we always
    # use sys.executable (the Python interpreter) as the program to run.
    try:
        raw = Path("/proc/self/cmdline").read_bytes()
        args = [a.decode() for a in raw.split(b"\x00") if a]
    except (OSError, UnicodeDecodeError):
        args = [sys.executable, *sys.argv]

    if args:
        logger.info(
            "Re-executing with LD_LIBRARY_PATH=%s to load OpenSlide 4.0",
            bin_dir_str,
        )
        os.execv(sys.executable, args)


# ============================================
# Auto-configure at import time
# ============================================

if sys.platform == "win32":
    _configure_windows()
elif sys.platform == "linux":
    _configure_linux()
