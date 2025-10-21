#!/bin/bash
#
# OpenSlide Build Script - VarunaPoC Patch for LEFT direction support
#
# Ce script compile et installe OpenSlide avec le patch pour supporter
# direction="LEFT" dans les fichiers Ventana BIF.
#
# Usage:
#   ./build-openslide.sh
#
# Prérequis:
#   - Exécuter dans MSYS2 UCRT64 (pas MinGW64 ou MSYS2)
#   - Connexion internet (pour télécharger les dépendances)
#

set -e  # Arrêter en cas d'erreur

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  OpenSlide Build Script - VarunaPoC Patch${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Vérifier qu'on est dans MSYS2 UCRT64
if [[ "$MSYSTEM" != "UCRT64" ]]; then
    echo -e "${RED}[ERROR]${NC} Ce script doit être exécuté dans MSYS2 UCRT64 !"
    echo -e "${YELLOW}Ouvrez 'MSYS2 UCRT64' (icône violette) et réessayez.${NC}"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Environnement UCRT64 détecté"
echo ""

# Étape 1: Installer les dépendances
echo -e "${BLUE}[STEP 1/5]${NC} Installation des dépendances de build..."
echo ""

DEPS=(
    "mingw-w64-ucrt-x86_64-gcc"
    "mingw-w64-ucrt-x86_64-meson"
    "mingw-w64-ucrt-x86_64-ninja"
    "mingw-w64-ucrt-x86_64-pkgconf"
    "mingw-w64-ucrt-x86_64-glib2"
    "mingw-w64-ucrt-x86_64-cairo"
    "mingw-w64-ucrt-x86_64-gdk-pixbuf2"
    "mingw-w64-ucrt-x86_64-libxml2"
    "mingw-w64-ucrt-x86_64-libtiff"
    "mingw-w64-ucrt-x86_64-openjpeg2"
    "mingw-w64-ucrt-x86_64-sqlite3"
)

echo "Installation de ${#DEPS[@]} packages..."
pacman -S --needed --noconfirm "${DEPS[@]}"

echo ""
echo -e "${GREEN}[OK]${NC} Dépendances installées"
echo ""

# Étape 2: Vérifier que le patch est appliqué
echo -e "${BLUE}[STEP 2/5]${NC} Vérification du patch..."
echo ""

if ! grep -q "DIRECTION_LEFT" openslide/src/openslide-vendor-ventana.c; then
    echo -e "${RED}[ERROR]${NC} Le patch n'est pas appliqué au code source !"
    echo "Le fichier openslide/src/openslide-vendor-ventana.c ne contient pas DIRECTION_LEFT"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Patch détecté dans le code source"
echo ""

# Étape 3: Configuration avec Meson
echo -e "${BLUE}[STEP 3/5]${NC} Configuration du build avec Meson..."
echo ""

cd openslide

# Nettoyer build précédent si existe
if [ -d "builddir" ]; then
    echo "Nettoyage du dossier builddir existant..."
    rm -rf builddir
fi

meson setup builddir \
    --prefix=/ucrt64 \
    --buildtype=release \
    --default-library=shared

echo ""
echo -e "${GREEN}[OK]${NC} Configuration terminée"
echo ""

# Étape 4: Compilation
echo -e "${BLUE}[STEP 4/5]${NC} Compilation d'OpenSlide..."
echo -e "${YELLOW}Cela peut prendre 2-5 minutes...${NC}"
echo ""

meson compile -C builddir

echo ""
echo -e "${GREEN}[OK]${NC} Compilation réussie"
echo ""

# Étape 5: Installation
echo -e "${BLUE}[STEP 5/5]${NC} Installation de la nouvelle DLL..."
echo ""

# Sauvegarder l'ancienne DLL
if [ -f "/ucrt64/bin/libopenslide-1.dll" ]; then
    BACKUP="/ucrt64/bin/libopenslide-1.dll.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Sauvegarde de l'ancienne DLL vers: $BACKUP"
    cp /ucrt64/bin/libopenslide-1.dll "$BACKUP"
fi

# Installer
meson install -C builddir

echo ""
echo -e "${GREEN}[OK]${NC} Installation terminée"
echo ""

# Résumé final
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  BUILD SUCCESSFUL !${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "La nouvelle version d'OpenSlide (avec patch LEFT) est maintenant installée."
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "1. Testez avec un fichier BIF problématique:"
echo "   cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC/backend"
echo "   python -c \"import openslide; slide = openslide.OpenSlide(r'../Slides/Ventana BIF/Ventana-1.bif'); print('SUCCESS:', slide.dimensions)\""
echo ""
echo "2. Si le test réussit, tous les fichiers BIF devraient maintenant fonctionner !"
echo ""
echo -e "${BLUE}Documentation:${NC} Voir README.md dans openslide-patch/"
echo ""

# Afficher info DLL installée
DLL_PATH="/ucrt64/bin/libopenslide-1.dll"
if [ -f "$DLL_PATH" ]; then
    DLL_SIZE=$(ls -lh "$DLL_PATH" | awk '{print $5}')
    DLL_DATE=$(ls -l "$DLL_PATH" | awk '{print $6, $7, $8}')
    echo -e "${BLUE}Fichier DLL:${NC}"
    echo "  Chemin: $DLL_PATH"
    echo "  Taille: $DLL_SIZE"
    echo "  Date: $DLL_DATE"
fi

echo ""
echo -e "${GREEN}Build script terminé avec succès !${NC}"
