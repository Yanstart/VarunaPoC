#!/bin/bash
################################################################################
# Script 01: Configuration initiale du fork OpenSlide
################################################################################
#
# OBJECTIF:
#   - Remplacer le submodule OpenSlide officiel par votre fork
#   - Configurer les remotes (origin = votre fork, upstream = officiel)
#   - Créer une branche dédiée aux patchs VarunaPoC
#   - Appliquer le patch Ventana LEFT
#   - Pusher vers votre fork sur GitHub
#
# PRÉREQUIS:
#   - Fork OpenSlide créé sur GitHub (https://github.com/Yanstart/openslide)
#   - MSYS2 UCRT64 installé
#   - Git configuré
#
# USAGE:
#   cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC
#   bash Scripts/01_setup_fork.sh
#
################################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Fork OpenSlide - VarunaPoC${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Configuration
FORK_URL="https://github.com/Yanstart/openslide.git"
UPSTREAM_URL="https://github.com/openslide/openslide.git"
PATCH_BRANCH="varuna-patches"
SUBMODULE_PATH="openslide-patch/openslide"
PATCH_FILE="openslide-patch/ventana-left-direction.patch"

# Vérifier qu'on est à la racine du projet
if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
    echo -e "${RED}[ERROR] Ce script doit être exécuté depuis la racine du projet VarunaPoC${NC}"
    exit 1
fi

echo -e "${YELLOW}[INFO] Configuration:${NC}"
echo "  Fork URL: $FORK_URL"
echo "  Upstream URL: $UPSTREAM_URL"
echo "  Patch branch: $PATCH_BRANCH"
echo ""

# Étape 1: Sauvegarder l'état actuel du submodule
echo -e "${YELLOW}[STEP 1/7] Sauvegarde de l'état actuel...${NC}"

if [ -d "$SUBMODULE_PATH" ]; then
    CURRENT_COMMIT=$(cd "$SUBMODULE_PATH" && git rev-parse HEAD)
    echo "  Current commit: $CURRENT_COMMIT"
else
    echo "  Submodule not initialized yet"
    CURRENT_COMMIT=""
fi

# Étape 2: Supprimer le submodule actuel
echo -e "${YELLOW}[STEP 2/7] Suppression du submodule actuel...${NC}"

if [ -d "$SUBMODULE_PATH" ]; then
    git submodule deinit -f "$SUBMODULE_PATH" 2>/dev/null || true
    git rm -f "$SUBMODULE_PATH" 2>/dev/null || true
    rm -rf ".git/modules/$SUBMODULE_PATH" 2>/dev/null || true
    echo "  [OK] Submodule supprimé"
else
    echo "  [SKIP] Pas de submodule à supprimer"
fi

# Étape 3: Ajouter votre fork comme submodule
echo -e "${YELLOW}[STEP 3/7] Ajout du fork comme submodule...${NC}"

git submodule add "$FORK_URL" "$SUBMODULE_PATH"
git submodule update --init --recursive

echo "  [OK] Fork ajouté comme submodule"

# Étape 4: Configurer les remotes dans le submodule
echo -e "${YELLOW}[STEP 4/7] Configuration des remotes...${NC}"

cd "$SUBMODULE_PATH"

# Vérifier que origin pointe vers le fork
CURRENT_ORIGIN=$(git remote get-url origin)
if [ "$CURRENT_ORIGIN" != "$FORK_URL" ]; then
    echo -e "${RED}[ERROR] Origin ne pointe pas vers votre fork!${NC}"
    echo "  Expected: $FORK_URL"
    echo "  Got: $CURRENT_ORIGIN"
    exit 1
fi

# Ajouter upstream vers le repo officiel
if git remote | grep -q "^upstream$"; then
    echo "  [INFO] Remote 'upstream' existe déjà"
    git remote set-url upstream "$UPSTREAM_URL"
else
    git remote add upstream "$UPSTREAM_URL"
    echo "  [OK] Remote 'upstream' ajouté"
fi

# Fetch upstream pour avoir les dernières versions
git fetch upstream
git fetch origin

echo "  [OK] Remotes configurés:"
echo "    - origin: $FORK_URL (votre fork)"
echo "    - upstream: $UPSTREAM_URL (officiel)"

# Étape 5: Créer la branche de patchs
echo -e "${YELLOW}[STEP 5/7] Création de la branche $PATCH_BRANCH...${NC}"

# Se baser sur la dernière version de main (là où le patch a été créé)
TARGET_BASE="upstream/main"
echo "  [INFO] Basing on: $TARGET_BASE"

# Créer la branche depuis upstream/main
if git show-ref --verify --quiet "refs/heads/$PATCH_BRANCH"; then
    echo "  [WARN] Branch $PATCH_BRANCH déjà existe, la suppression..."
    git branch -D "$PATCH_BRANCH"
fi

git checkout -b "$PATCH_BRANCH" "$TARGET_BASE"

echo "  [OK] Branch $PATCH_BRANCH créée depuis $TARGET_BASE"

# Étape 6: Appliquer les patchs
echo -e "${YELLOW}[STEP 6/7] Application des patchs...${NC}"

cd ../..  # Retour à la racine du projet

if [ ! -f "$PATCH_FILE" ]; then
    echo -e "${RED}[ERROR] Patch file not found: $PATCH_FILE${NC}"
    exit 1
fi

cd "$SUBMODULE_PATH"

# Appliquer le patch Ventana LEFT
echo "  [INFO] Applying: ventana-left-direction.patch"
if git apply --check "../../$PATCH_FILE" 2>/dev/null; then
    git apply "../../$PATCH_FILE"
    git add .
    git commit -m "Apply Ventana LEFT direction patch for VarunaPoC

This patch allows OpenSlide to handle Ventana BIF files with direction=\"LEFT\".

Background:
- Ventana BIF files can have direction=\"LEFT\" or direction=\"RIGHT\"
- OpenSlide officially only supports direction=\"RIGHT\"
- Community testing shows LEFT produces nearly identical images as RIGHT

Solution:
- Treat LEFT the same as RIGHT in tile joint calculations
- This allows opening files like Ventana-1.bif

See: https://github.com/openslide/openslide/issues/234
"
    echo "  [OK] Patch appliqué et commité"
else
    echo -e "${RED}[ERROR] Le patch ne peut pas être appliqué!${NC}"
    echo "  Vérifiez que le patch est compatible avec cette version d'OpenSlide"
    exit 1
fi

# Étape 7: Pusher vers GitHub
echo -e "${YELLOW}[STEP 7/7] Push vers GitHub...${NC}"

echo "  [INFO] Pushing branch $PATCH_BRANCH to origin..."
git push -u origin "$PATCH_BRANCH"

echo "  [OK] Branch pushed to GitHub"

# Retour à la racine et commit du nouveau submodule
cd ../..

git add .gitmodules "$SUBMODULE_PATH"
git commit -m "Configure OpenSlide fork with Ventana LEFT patch

- Submodule now points to fork: Yanstart/openslide
- Branch: $PATCH_BRANCH
- Patch applied: ventana-left-direction.patch
- Upstream configured for future updates
"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup terminé avec succès!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${YELLOW}État final:${NC}"
echo "  - Fork configuré comme submodule"
echo "  - Branch: $PATCH_BRANCH"
echo "  - Patch Ventana LEFT appliqué"
echo "  - Pushed to GitHub"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "  1. Recompiler OpenSlide:"
echo "     cd openslide-patch && bash build-openslide.sh"
echo ""
echo "  2. Pour mettre à jour depuis upstream:"
echo "     bash Scripts/02_update_from_upstream.sh"
echo ""
echo "  3. Pour ajouter un nouveau patch:"
echo "     bash Scripts/03_add_new_patch.sh <nom-du-patch>.patch"
echo ""
