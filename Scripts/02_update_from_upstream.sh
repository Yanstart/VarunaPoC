#!/bin/bash
################################################################################
# Script 02: Mise à jour depuis upstream (OpenSlide officiel)
################################################################################
#
# OBJECTIF:
#   - Récupérer les dernières modifications d'OpenSlide officiel
#   - Rebaser votre branche de patchs sur la nouvelle version
#   - Gérer les conflits si nécessaire
#   - Pusher les changements vers votre fork
#
# QUAND L'UTILISER:
#   - Quand OpenSlide sort une nouvelle version
#   - Pour rester à jour avec les correctifs de sécurité
#   - Pour bénéficier des nouvelles fonctionnalités
#
# USAGE:
#   cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC
#   bash Scripts/02_update_from_upstream.sh [version]
#
#   Sans argument: met à jour vers la dernière version de main
#   Avec argument: met à jour vers une version spécifique (ex: v4.1.0)
#
################################################################################

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update OpenSlide from Upstream${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
PATCH_BRANCH="varuna-patches"
SUBMODULE_PATH="openslide-patch/openslide"
TARGET_VERSION="${1:-main}"  # Par défaut: main

# Vérifier qu'on est à la racine du projet
if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
    echo -e "${RED}[ERROR] Ce script doit être exécuté depuis la racine du projet${NC}"
    exit 1
fi

if [ ! -d "$SUBMODULE_PATH" ]; then
    echo -e "${RED}[ERROR] Submodule OpenSlide non trouvé${NC}"
    echo "  Exécutez d'abord: bash Scripts/01_setup_fork.sh"
    exit 1
fi

echo -e "${YELLOW}[INFO] Configuration:${NC}"
echo "  Target version: $TARGET_VERSION"
echo "  Patch branch: $PATCH_BRANCH"
echo ""

# Étape 1: Sauvegarder l'état actuel
echo -e "${YELLOW}[STEP 1/6] Sauvegarde de l'état actuel...${NC}"

cd "$SUBMODULE_PATH"

CURRENT_BRANCH=$(git branch --show-current)
CURRENT_COMMIT=$(git rev-parse HEAD)

echo "  Current branch: $CURRENT_BRANCH"
echo "  Current commit: $CURRENT_COMMIT"

if [ "$CURRENT_BRANCH" != "$PATCH_BRANCH" ]; then
    echo -e "${RED}[ERROR] Vous n'êtes pas sur la branche $PATCH_BRANCH${NC}"
    echo "  Passez sur la bonne branche avec: git checkout $PATCH_BRANCH"
    exit 1
fi

# Vérifier qu'il n'y a pas de modifications non commitées
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}[ERROR] Vous avez des modifications non commitées${NC}"
    echo "  Committez ou stash vos changements avant de continuer"
    git status --short
    exit 1
fi

# Étape 2: Fetch upstream
echo -e "${YELLOW}[STEP 2/6] Récupération des mises à jour upstream...${NC}"

git fetch upstream
git fetch origin

echo "  [OK] Upstream mis à jour"

# Étape 3: Déterminer la version cible
echo -e "${YELLOW}[STEP 3/6] Résolution de la version cible...${NC}"

if [ "$TARGET_VERSION" = "main" ]; then
    TARGET_REF="upstream/main"
    TARGET_DESCRIPTION="latest main"
else
    # Vérifier si c'est un tag existant
    if git rev-parse "refs/tags/$TARGET_VERSION" >/dev/null 2>&1; then
        TARGET_REF="$TARGET_VERSION"
        TARGET_DESCRIPTION="tag $TARGET_VERSION"
    elif git rev-parse "upstream/$TARGET_VERSION" >/dev/null 2>&1; then
        TARGET_REF="upstream/$TARGET_VERSION"
        TARGET_DESCRIPTION="branch $TARGET_VERSION"
    else
        echo -e "${RED}[ERROR] Version introuvable: $TARGET_VERSION${NC}"
        echo "  Versions disponibles:"
        git tag --list 'v*' | tail -n 10
        exit 1
    fi
fi

TARGET_COMMIT=$(git rev-parse "$TARGET_REF")

echo "  Target: $TARGET_DESCRIPTION"
echo "  Commit: $TARGET_COMMIT"

# Vérifier si on est déjà à jour
if [ "$CURRENT_COMMIT" = "$TARGET_COMMIT" ]; then
    echo -e "${GREEN}[INFO] Déjà à jour! Aucune mise à jour nécessaire.${NC}"
    exit 0
fi

# Étape 4: Créer une branche de backup
echo -e "${YELLOW}[STEP 4/6] Création d'une sauvegarde...${NC}"

BACKUP_BRANCH="${PATCH_BRANCH}-backup-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH" "$CURRENT_COMMIT"

echo "  [OK] Backup créé: $BACKUP_BRANCH"
echo "  (Si le rebase échoue, restaurez avec: git reset --hard $BACKUP_BRANCH)"

# Étape 5: Rebase sur la nouvelle version
echo -e "${YELLOW}[STEP 5/6] Rebase sur $TARGET_DESCRIPTION...${NC}"

echo ""
echo -e "${BLUE}┌─────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ ATTENTION: Rebase en cours                      │${NC}"
echo -e "${BLUE}│                                                 │${NC}"
echo -e "${BLUE}│ Si des conflits apparaissent:                  │${NC}"
echo -e "${BLUE}│ 1. Résolvez les conflits manuellement          │${NC}"
echo -e "${BLUE}│ 2. git add <fichiers-résolus>                  │${NC}"
echo -e "${BLUE}│ 3. git rebase --continue                        │${NC}"
echo -e "${BLUE}│                                                 │${NC}"
echo -e "${BLUE}│ Pour annuler:                                   │${NC}"
echo -e "${BLUE}│   git rebase --abort                            │${NC}"
echo -e "${BLUE}│   git reset --hard $BACKUP_BRANCH               │${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────┘${NC}"
echo ""

# Tenter le rebase
if git rebase "$TARGET_REF"; then
    echo -e "${GREEN}[OK] Rebase réussi sans conflits!${NC}"
else
    echo -e "${RED}[ERROR] Conflits détectés pendant le rebase${NC}"
    echo ""
    echo "  Résolvez les conflits, puis:"
    echo "    1. git add <fichiers>"
    echo "    2. git rebase --continue"
    echo "    3. Relancez ce script pour pusher"
    echo ""
    echo "  Ou annulez avec:"
    echo "    git rebase --abort"
    echo "    git reset --hard $BACKUP_BRANCH"
    exit 1
fi

# Étape 6: Push vers GitHub
echo -e "${YELLOW}[STEP 6/6] Push vers GitHub (force)...${NC}"

echo "  [INFO] Un force push est nécessaire car nous avons rebasé"
echo "  [WARN] Cela va réécrire l'historique sur GitHub"
echo ""

read -p "Continuer le force push? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}[ABORT] Force push annulé${NC}"
    echo "  Vous pouvez le faire manuellement avec:"
    echo "    cd $SUBMODULE_PATH"
    echo "    git push --force-with-lease origin $PATCH_BRANCH"
    exit 0
fi

git push --force-with-lease origin "$PATCH_BRANCH"

echo -e "${GREEN}[OK] Push réussi${NC}"

# Mettre à jour le commit du submodule dans le repo principal
cd ../..

git add "$SUBMODULE_PATH"
git commit -m "Update OpenSlide submodule to $TARGET_DESCRIPTION

Updated from:
  $CURRENT_COMMIT

To:
  $TARGET_COMMIT

Patches rebased on new version.
"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Mise à jour terminée avec succès!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}État final:${NC}"
echo "  - OpenSlide mis à jour vers: $TARGET_DESCRIPTION"
echo "  - Patchs rebasés et appliqués"
echo "  - Backup disponible: $BACKUP_BRANCH"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "  1. Recompiler OpenSlide:"
echo "     cd openslide-patch && bash build-openslide.sh"
echo ""
echo "  2. Tester que tout fonctionne"
echo ""
echo "  3. Si tout est OK, supprimer le backup:"
echo "     cd $SUBMODULE_PATH"
echo "     git branch -D $BACKUP_BRANCH"
echo ""
