#!/bin/bash
################################################################################
# Script 04: Recompiler OpenSlide après modifications
################################################################################
#
# OBJECTIF:
#   - Recompiler OpenSlide avec les patchs appliqués
#   - Installer la DLL dans MSYS2
#   - Vérifier que Python utilise bien la bonne DLL
#
# USAGE:
#   bash Scripts/04_rebuild_openslide.sh
#
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rebuild OpenSlide${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
BUILD_SCRIPT="openslide-patch/build-openslide.sh"
DLL_PATH="/c/msys64/ucrt64/bin/libopenslide-1.dll"
CONFIG_SCRIPT="backend/config_openslide.py"

# Vérifier le script de build
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo -e "${RED}[ERROR] Build script introuvable: $BUILD_SCRIPT${NC}"
    exit 1
fi

# Étape 1: Clean build (optionnel)
echo -e "${YELLOW}[STEP 1/4] Nettoyage...${NC}"

cd openslide-patch/openslide

if [ -d "build" ]; then
    echo "  [INFO] Suppression du dossier build existant"
    rm -rf build
fi

cd ../..

echo "  [OK] Nettoyage terminé"

# Étape 2: Compilation
echo -e "${YELLOW}[STEP 2/4] Compilation d'OpenSlide...${NC}"

cd openslide-patch

echo "  [INFO] Lancement de build-openslide.sh..."
echo "  (Cela peut prendre quelques minutes)"
echo ""

if bash build-openslide.sh; then
    echo ""
    echo "  [OK] Compilation réussie"
else
    echo -e "${RED}[ERROR] Échec de la compilation${NC}"
    exit 1
fi

cd ..

# Étape 3: Vérifier la DLL
echo -e "${YELLOW}[STEP 3/4] Vérification de la DLL...${NC}"

if [ -f "$DLL_PATH" ]; then
    DLL_SIZE=$(stat -f%z "$DLL_PATH" 2>/dev/null || stat -c%s "$DLL_PATH" 2>/dev/null || echo "0")
    DLL_DATE=$(ls -lh "$DLL_PATH" | awk '{print $6, $7, $8}')

    echo "  [OK] DLL trouvée:"
    echo "    Path: $DLL_PATH"
    echo "    Size: $((DLL_SIZE / 1024)) KB"
    echo "    Date: $DLL_DATE"
else
    echo -e "${RED}[ERROR] DLL non trouvée à: $DLL_PATH${NC}"
    exit 1
fi

# Étape 4: Test Python
echo -e "${YELLOW}[STEP 4/4] Test avec Python...${NC}"

echo "  [INFO] Test de l'import OpenSlide depuis Python..."

cd backend

python << 'PYTHON_TEST'
import sys
import os

# Charger config_openslide AVANT openslide
sys.path.insert(0, os.getcwd())
import config_openslide

import openslide

# Tester la version
print(f"  OpenSlide version: {openslide.__version__}")

# Vérifier la DLL utilisée
dll_path = openslide._convert._dll._name
print(f"  DLL loaded: {dll_path}")

# Vérifier que c'est bien la DLL MSYS2
if "msys64" in dll_path.lower():
    print("  [OK] Using MSYS2 DLL (patched)")
else:
    print(f"  [WARN] Not using MSYS2 DLL!")
    sys.exit(1)

# Test basique
try:
    # Tenter d'ouvrir un fichier de test (si disponible)
    test_files = [
        "../Slides/Ventana BIF/Ventana-1.bif",
        "../Slides-old/Ventana BIF/Ventana-1.bif",
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  [INFO] Testing with: {os.path.basename(test_file)}")
            slide = openslide.OpenSlide(test_file)
            print(f"    Dimensions: {slide.dimensions}")
            print(f"    Levels: {slide.level_count}")
            slide.close()
            print("  [OK] Test successful!")
            break
    else:
        print("  [INFO] No test files available (skipped)")

except Exception as e:
    print(f"  [ERROR] Test failed: {e}")
    sys.exit(1)
PYTHON_TEST

if [ $? -eq 0 ]; then
    echo "  [OK] Python test réussi"
else
    echo -e "${RED}[ERROR] Python test échoué${NC}"
    exit 1
fi

cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rebuild terminé avec succès!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Résumé:${NC}"
echo "  - OpenSlide compilé avec patchs"
echo "  - DLL installée: $DLL_PATH"
echo "  - Python configuré correctement"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "  1. Tester avec le backend:"
echo "     cd backend && python main.py"
echo ""
echo "  2. Tester avec des lames réelles"
echo ""
