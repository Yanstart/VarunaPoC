"""
Configuration OpenSlide pour Docker

IMPORTANT: Ce fichier est utilisé dans le conteneur Docker.
Les DLLs OpenSlide sont installées via apt-get dans le Dockerfile.

Difference avec config_openslide.py:
- config_openslide.py: Windows (MSYS2/bin path)
- config_openslide_docker.py: Docker Linux (system packages)

Dans Docker, OpenSlide est installé comme package système:
  apt-get install openslide-tools libopenslide0

Les librairies sont automatiquement dans /usr/lib/, pas besoin de configuration.
"""

import os
import sys


def configure_openslide_path():
    """
    Configure OpenSlide pour environnement Docker.

    Dans Docker Linux, OpenSlide est installé comme package système,
    donc les librairies sont déjà dans le path du système.
    Cette fonction vérifie simplement que les libs sont présentes.

    Returns:
        bool: True si OpenSlide est accessible, False sinon
    """
    # Dans Docker Linux, vérifier que libopenslide est accessible
    # Les chemins courants sur Debian/Ubuntu:
    common_paths = [
        "/usr/lib/x86_64-linux-gnu/libopenslide.so.0",
        "/usr/lib/libopenslide.so.0",
        "/usr/local/lib/libopenslide.so.0",
    ]

    for lib_path in common_paths:
        if os.path.exists(lib_path):
            print(f"[OK] OpenSlide library found: {lib_path}")
            return True

    # Si aucune lib trouvée, warning mais pas fatal
    # (openslide-python va essayer de charger quand même)
    print("[WARNING] OpenSlide library not found in common paths")
    print("Expected installation via: apt-get install libopenslide0 openslide-tools")
    print("Python openslide module will attempt to load system libraries...")

    return False


# Auto-configure au import
configure_openslide_path()
