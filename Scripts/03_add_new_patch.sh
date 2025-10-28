#!/bin/bash
################################################################################
# Script 03: Ajouter un nouveau patch à OpenSlide
################################################################################
#
# OBJECTIF:
#   - Appliquer un nouveau patch à votre fork OpenSlide
#   - Commit et push vers GitHub
#   - Maintenir l'historique des patchs
#
# USAGE:
#   bash Scripts/03_add_new_patch.sh <patch-file> [commit-message]
#
# EXEMPLES:
#   # Appliquer un nouveau patch
#   bash Scripts/03_add_new_patch.sh openslide-patch/my-fix.patch
#
#   # Avec message personnalisé
#   bash Scripts/03_add_new_patch.sh openslide-patch/czi-support.patch "Add CZI JPEG XR support"
#
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Add New Patch to OpenSlide${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
PATCH_BRANCH="varuna-patches"
SUBMODULE_PATH="openslide-patch/openslide"
PATCH_FILE="$1"
COMMIT_MSG="${2:-}"

# Validation des arguments
if [ -z "$PATCH_FILE" ]; then
    echo -e "${RED}[ERROR] Patch file requis${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 <patch-file> [commit-message]"
    echo ""
    echo "Exemple:"
    echo "  $0 openslide-patch/my-new-fix.patch \"Fix issue #123\""
    exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
    echo -e "${RED}[ERROR] Patch file introuvable: $PATCH_FILE${NC}"
    exit 1
fi

if [ ! -d "$SUBMODULE_PATH" ]; then
    echo -e "${RED}[ERROR] Submodule OpenSlide non trouvé${NC}"
    echo "  Exécutez d'abord: bash Scripts/01_setup_fork.sh"
    exit 1
fi

PATCH_NAME=$(basename "$PATCH_FILE")

echo -e "${YELLOW}[INFO] Configuration:${NC}"
echo "  Patch file: $PATCH_FILE"
echo "  Patch name: $PATCH_NAME"
echo "  Branch: $PATCH_BRANCH"
echo ""

# Étape 1: Vérifier l'état du submodule
echo -e "${YELLOW}[STEP 1/5] Vérification de l'état du submodule...${NC}"

cd "$SUBMODULE_PATH"

CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "$PATCH_BRANCH" ]; then
    echo -e "${RED}[ERROR] Vous n'êtes pas sur la branche $PATCH_BRANCH${NC}"
    echo "  Branch actuelle: $CURRENT_BRANCH"
    echo "  Passez sur la bonne branche avec: git checkout $PATCH_BRANCH"
    exit 1
fi

if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}[ERROR] Modifications non commitées détectées${NC}"
    echo "  Committez ou stash vos changements avant de continuer"
    git status --short
    exit 1
fi

echo "  [OK] État propre"

# Étape 2: Tester le patch
echo -e "${YELLOW}[STEP 2/5] Test du patch (dry-run)...${NC}"

if git apply --check "../../$PATCH_FILE" 2>/dev/null; then
    echo "  [OK] Patch applicable sans conflit"
else
    echo -e "${RED}[ERROR] Le patch ne peut pas être appliqué!${NC}"
    echo ""
    echo "  Raisons possibles:"
    echo "    - Le patch a déjà été appliqué"
    echo "    - Le patch n'est pas compatible avec cette version"
    echo "    - Le code a changé dans cette zone"
    echo ""
    echo "  Vérifiez manuellement:"
    git apply --check "../../$PATCH_FILE" 2>&1 || true
    exit 1
fi

# Étape 3: Appliquer le patch
echo -e "${YELLOW}[STEP 3/5] Application du patch...${NC}"

git apply "../../$PATCH_FILE"

echo "  [OK] Patch appliqué"

# Afficher un diff summary
echo ""
echo "  Fichiers modifiés:"
git diff --stat

# Étape 4: Commit
echo -e "${YELLOW}[STEP 4/5] Création du commit...${NC}"

git add .

# Générer un message de commit si non fourni
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Apply patch: $PATCH_NAME"
fi

# Créer le commit avec un message détaillé
git commit -m "$COMMIT_MSG

Patch: $PATCH_NAME
Applied: $(date +%Y-%m-%d)

Changes:
$(git diff --cached --stat HEAD~1)
"

COMMIT_HASH=$(git rev-parse --short HEAD)

echo "  [OK] Commit créé: $COMMIT_HASH"

# Étape 5: Push vers GitHub
echo -e "${YELLOW}[STEP 5/5] Push vers GitHub...${NC}"

git push origin "$PATCH_BRANCH"

echo "  [OK] Push réussi"

# Mettre à jour le submodule dans le repo principal
cd ../..

git add "$SUBMODULE_PATH"

# Vérifier s'il y a des changements à committer
if git diff --cached --quiet; then
    echo ""
    echo -e "${YELLOW}[INFO] Submodule déjà à jour dans le repo principal${NC}"
else
    git commit -m "Apply OpenSlide patch: $PATCH_NAME

Patch applied to fork: Yanstart/openslide
Branch: $PATCH_BRANCH
Commit: $COMMIT_HASH

$COMMIT_MSG
"
    echo "  [OK] Repo principal mis à jour"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Patch appliqué avec succès!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Résumé:${NC}"
echo "  - Patch: $PATCH_NAME"
echo "  - Commit: $COMMIT_HASH"
echo "  - Branch: $PATCH_BRANCH"
echo "  - Pushed to GitHub: ✓"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "  1. Recompiler OpenSlide:"
echo "     cd openslide-patch && bash build-openslide.sh"
echo ""
echo "  2. Tester les changements"
echo ""
echo "  3. Si tout est OK, commit et push le repo principal:"
echo "     git push origin develop"
echo ""
