r"""
Configuration OpenSlide pour Windows

IMPORTANT: Sur Windows, OpenSlide nécessite que les DLLs soient accessibles.
Ce fichier doit être importé AVANT tout import d'openslide.

Installation OpenSlide Windows:
1. Télécharger depuis: https://openslide.org/download/
2. Extraire dans un dossier (ex: C:\OpenSlide)
3. Modifier OPENSLIDE_PATH ci-dessous avec votre chemin

Alternative: Ajouter le dossier bin/ au PATH système Windows.
"""

import os
import sys

# ============================================
# CONFIGUREZ CE CHEMIN selon votre installation
# ============================================

# MSYS2 UCRT64 installation (recommandé)
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"

# Chemins alternatifs courants (décommentez si besoin)
# OPENSLIDE_PATH = r"C:\OpenSlide\bin"
# OPENSLIDE_PATH = r"C:\Program Files\OpenSlide\bin"
# OPENSLIDE_PATH = r"C:\OpenSlide-win64\bin"


def configure_openslide_path():
    """
    Configure le chemin DLL pour OpenSlide sur Windows.

    Pour Python 3.8+, utilise os.add_dll_directory().
    Pour versions antérieures, modifie PATH.
    """
    if not os.path.exists(OPENSLIDE_PATH):
        print(f"WARNING: OpenSlide path not found: {OPENSLIDE_PATH}")
        print("Please download OpenSlide from: https://openslide.org/download/")
        print("And update OPENSLIDE_PATH in backend/config_openslide.py")
        return False

    # Python 3.8+ recommande os.add_dll_directory()
    if sys.version_info >= (3, 8) and hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(OPENSLIDE_PATH)
            print(f"[OK] OpenSlide DLL directory added: {OPENSLIDE_PATH}")
            return True
        except Exception as e:
            print(f"Error adding DLL directory: {e}")
            return False
    else:
        # Fallback pour Python < 3.8
        os.environ['PATH'] = OPENSLIDE_PATH + os.pathsep + os.environ.get('PATH', '')
        print(f"[OK] OpenSlide added to PATH: {OPENSLIDE_PATH}")
        return True


# Auto-configure au import
configure_openslide_path()
