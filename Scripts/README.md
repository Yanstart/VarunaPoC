# Scripts de Gestion du Fork OpenSlide

**Version:** 1.0
**Dernière mise à jour:** 2025-10-28
**Auteur:** Équipe VarunaPoC

---

## Vue d'Ensemble

Ce dossier contient des scripts pour gérer le fork OpenSlide avec les patchs personnalisés de VarunaPoC.

**Objectifs:**
- ✅ Maintenir un fork OpenSlide avec patchs personnalisés
- ✅ Rester à jour avec les versions officielles d'OpenSlide
- ✅ Ajouter facilement de nouveaux patchs
- ✅ Garder un historique clair des modifications

---

## Architecture du Fork

```
VarunaPoC/
├── .gitmodules                          # Configuration submodule
├── openslide-patch/
│   ├── openslide/                       # Submodule → fork Yanstart/openslide
│   │   ├── .git/                        # Git du submodule
│   │   │   └── config                   # Remotes configurés:
│   │   │                                #   - origin: Yanstart/openslide (fork)
│   │   │                                #   - upstream: openslide/openslide (officiel)
│   │   └── src/                         # Code OpenSlide avec patchs
│   │
│   ├── ventana-left-direction.patch     # Patch Ventana LEFT
│   └── build-openslide.sh               # Script de compilation
│
└── Scripts/                             # Ce dossier
    ├── 01_setup_fork.sh                 # Configuration initiale
    ├── 02_update_from_upstream.sh       # Mise à jour depuis officiel
    ├── 03_add_new_patch.sh              # Ajouter nouveau patch
    ├── 04_rebuild_openslide.sh          # Recompiler
    └── README.md                        # Ce fichier
```

---

## Workflow Git

### Branches

**Fork (Yanstart/openslide):**
- `main` - Copie du repo officiel (ne pas modifier)
- `varuna-patches` - **Branche de travail avec patchs** ✨

**Repo officiel (openslide/openslide):**
- `main` - Version officielle stable
- `v4.0.0`, `v4.1.0`, etc. - Tags de versions

### Remotes

Dans le submodule `openslide-patch/openslide`:

```bash
git remote -v
# origin    https://github.com/Yanstart/openslide.git (fetch)
# origin    https://github.com/Yanstart/openslide.git (push)
# upstream  https://github.com/openslide/openslide.git (fetch)
# upstream  https://github.com/openslide/openslide.git (push)
```

---

## Scripts Disponibles

### 01. Configuration Initiale

**Fichier:** `01_setup_fork.sh`

**Usage:**
```bash
cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC
bash Scripts/01_setup_fork.sh
```

**Ce qu'il fait:**
1. Supprime le submodule OpenSlide officiel
2. Ajoute votre fork comme submodule
3. Configure les remotes (origin = fork, upstream = officiel)
4. Crée la branche `varuna-patches` depuis la dernière version stable
5. Applique le patch Ventana LEFT
6. Push vers GitHub

**Quand l'utiliser:**
- ⚠️ **Une seule fois** lors de la première configuration
- Ou pour reconfigurer complètement le fork

**Prérequis:**
- Fork OpenSlide créé sur GitHub (`Yanstart/openslide`)
- Accès Git configuré

---

### 02. Mise à Jour depuis Upstream

**Fichier:** `02_update_from_upstream.sh`

**Usage:**
```bash
# Mettre à jour vers la dernière version de main
bash Scripts/02_update_from_upstream.sh

# Mettre à jour vers une version spécifique
bash Scripts/02_update_from_upstream.sh v4.1.0
```

**Ce qu'il fait:**
1. Fetch les dernières modifications d'OpenSlide officiel
2. Crée une sauvegarde de votre branche actuelle
3. Rebase `varuna-patches` sur la nouvelle version
4. Gère les conflits si nécessaire
5. Force push vers GitHub

**Quand l'utiliser:**
- 🔄 Quand OpenSlide sort une nouvelle version
- 🔄 Pour bénéficier des correctifs de sécurité
- 🔄 Pour intégrer de nouvelles fonctionnalités

**Gestion des conflits:**

Si des conflits apparaissent:

```bash
# Le script s'arrête et vous indique les fichiers en conflit

# 1. Résolvez manuellement les conflits
vim src/openslide-vendor-ventana.c  # Éditez les fichiers

# 2. Marquez comme résolus
git add src/openslide-vendor-ventana.c

# 3. Continuez le rebase
git rebase --continue

# 4. Relancez le script pour pusher
bash Scripts/02_update_from_upstream.sh
```

**Annuler en cas de problème:**

```bash
cd openslide-patch/openslide

# Annuler le rebase
git rebase --abort

# Restaurer depuis le backup
git reset --hard varuna-patches-backup-YYYYMMDD-HHMMSS
```

---

### 03. Ajouter un Nouveau Patch

**Fichier:** `03_add_new_patch.sh`

**Usage:**
```bash
# Appliquer un patch
bash Scripts/03_add_new_patch.sh openslide-patch/mon-patch.patch

# Avec message de commit personnalisé
bash Scripts/03_add_new_patch.sh openslide-patch/czi-fix.patch "Fix CZI JPEG XR support"
```

**Ce qu'il fait:**
1. Vérifie que le patch peut être appliqué
2. Applique le patch au code
3. Commit les changements avec un message descriptif
4. Push vers GitHub
5. Met à jour le submodule dans le repo principal

**Quand l'utiliser:**
- ➕ Pour ajouter un nouveau patch personnalisé
- ➕ Pour corriger un bug spécifique à VarunaPoC
- ➕ Pour ajouter une fonctionnalité non supportée officiellement

**Création d'un patch:**

```bash
cd openslide-patch/openslide

# Faire des modifications
vim src/openslide-vendor-zeiss.c

# Créer le patch
git diff > ../mon-nouveau-patch.patch

# Appliquer avec le script
cd ../..
bash Scripts/03_add_new_patch.sh openslide-patch/mon-nouveau-patch.patch
```

---

### 04. Recompiler OpenSlide

**Fichier:** `04_rebuild_openslide.sh`

**Usage:**
```bash
bash Scripts/04_rebuild_openslide.sh
```

**Ce qu'il fait:**
1. Nettoie les builds précédents
2. Compile OpenSlide avec MSYS2
3. Installe la DLL dans `/c/msys64/ucrt64/bin/`
4. Teste avec Python

**Quand l'utiliser:**
- 🔨 Après avoir ajouté un patch
- 🔨 Après une mise à jour depuis upstream
- 🔨 Pour tester des modifications locales

**Durée:** ~5-10 minutes selon votre machine

---

## Workflows Courants

### Workflow 1: Configuration Initiale (Une fois)

```bash
# 1. Créer le fork sur GitHub (déjà fait)
# https://github.com/openslide/openslide → Fork → Yanstart/openslide

# 2. Configurer le submodule avec le fork
cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC
bash Scripts/01_setup_fork.sh

# 3. Compiler
bash Scripts/04_rebuild_openslide.sh

# 4. Tester
cd backend && python main.py
```

---

### Workflow 2: Mise à Jour vers Nouvelle Version OpenSlide

```bash
# Exemple: OpenSlide v4.1.0 vient de sortir

# 1. Mettre à jour et rebaser les patchs
cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC
bash Scripts/02_update_from_upstream.sh v4.1.0

# 2. Recompiler avec la nouvelle version
bash Scripts/04_rebuild_openslide.sh

# 3. Tester que tout fonctionne
cd backend && python main.py

# 4. Push vers GitHub
git push origin develop
```

---

### Workflow 3: Ajouter un Patch pour Corriger un Bug

```bash
# Exemple: Ajouter support JPEG XR pour CZI

# 1. Créer le patch manuellement
cd openslide-patch/openslide
git checkout varuna-patches

# Modifier le code
vim src/openslide-vendor-zeiss.c

# Générer le patch
git diff > ../czi-jpeg-xr-support.patch

# 2. Appliquer le patch avec le script
cd ../..
bash Scripts/03_add_new_patch.sh openslide-patch/czi-jpeg-xr-support.patch

# 3. Recompiler
bash Scripts/04_rebuild_openslide.sh

# 4. Tester
cd backend && python main.py

# 5. Commit et push le repo principal
git add openslide-patch/
git commit -m "Add JPEG XR support for CZI files"
git push origin develop
```

---

### Workflow 4: Maintenance Régulière

**Tous les 3 mois:**

```bash
# Vérifier s'il y a des mises à jour d'OpenSlide
cd openslide-patch/openslide
git fetch upstream

# Voir les nouveaux tags
git tag --list 'v*' | tail -n 10

# Si nouvelle version disponible
cd ../..
bash Scripts/02_update_from_upstream.sh v4.x.x
bash Scripts/04_rebuild_openslide.sh
```

---

## Gestion des Patchs

### Patchs Actuels

**1. Ventana LEFT Direction Patch**

**Fichier:** `openslide-patch/ventana-left-direction.patch`

**Problème résolu:**
- Ventana BIF avec `direction="LEFT"` non supportés officiellement
- Erreur: "Bad direction attribute LEFT"

**Solution:**
- Traite `direction="LEFT"` comme `direction="RIGHT"`
- Tests communauté: images quasi-identiques

**Référence:** [GitHub Issue #234](https://github.com/openslide/openslide/issues/234)

**Fichiers modifiés:**
- `src/openslide-vendor-ventana.c` (lignes 71, 573-581)

---

### Créer un Nouveau Patch

**Méthode 1: Depuis des modifications locales**

```bash
cd openslide-patch/openslide

# Faire des modifications
vim src/mon-fichier.c

# Créer le patch
git diff > ../mon-nouveau-patch.patch

# Appliquer avec le script
cd ../..
bash Scripts/03_add_new_patch.sh openslide-patch/mon-nouveau-patch.patch
```

**Méthode 2: Depuis un commit existant**

```bash
cd openslide-patch/openslide

# Identifier le commit
git log --oneline

# Extraire le patch
git format-patch -1 abc1234 --stdout > ../mon-patch.patch

# Appliquer avec le script
cd ../..
bash Scripts/03_add_new_patch.sh openslide-patch/mon-patch.patch
```

---

## Résolution de Problèmes

### Problème 1: Le Patch Ne S'Applique Pas

**Erreur:**
```
[ERROR] Le patch ne peut pas être appliqué!
```

**Causes possibles:**
1. Le patch a déjà été appliqué
2. Le code a changé dans cette zone
3. Le patch n'est pas compatible avec cette version

**Solutions:**

```bash
# Vérifier si déjà appliqué
cd openslide-patch/openslide
git log --oneline | grep "nom-du-patch"

# Tester manuellement
git apply --check ../mon-patch.patch

# Voir les différences
git apply --reject ../mon-patch.patch
# Fichiers .rej créés avec les parties non appliquées

# Appliquer manuellement et corriger
vim src/fichier.c  # Éditer selon .rej
git add .
git commit -m "Manual application of patch"
```

---

### Problème 2: Conflit Lors de la Mise à Jour

**Erreur:**
```
[ERROR] Conflits détectés pendant le rebase
```

**Solution:**

```bash
# Le rebase s'arrête sur le conflit

# 1. Voir les fichiers en conflit
git status

# 2. Éditer les fichiers
vim src/openslide-vendor-ventana.c

# Chercher les marqueurs de conflit:
# <<<<<<< HEAD
# ... code de la nouvelle version
# =======
# ... votre code patché
# >>>>>>> varuna-patches

# 3. Résoudre manuellement (garder les deux, ou choisir)

# 4. Marquer comme résolu
git add src/openslide-vendor-ventana.c

# 5. Continuer le rebase
git rebase --continue

# 6. Push avec force (historique réécrit)
git push --force-with-lease origin varuna-patches
```

---

### Problème 3: Python N'Utilise Pas la Bonne DLL

**Symptôme:**
```
Using DLL: C:\Users\...\AppData\Roaming\Python\...\openslide_bin\...
```

**Solution:**

```bash
# 1. Désinstaller openslide-bin (conflit)
pip uninstall -y openslide-bin

# 2. Vérifier config_openslide.py
cat backend/config_openslide.py
# OPENSLIDE_PATH doit pointer vers C:\msys64\ucrt64\bin

# 3. Recompiler
bash Scripts/04_rebuild_openslide.sh

# 4. Tester
cd backend
python -c "import config_openslide; import openslide; print(openslide._convert._dll._name)"
```

---

### Problème 4: La Compilation Échoue

**Erreur:**
```
[ERROR] Échec de la compilation
```

**Solutions:**

```bash
# 1. Vérifier MSYS2 UCRT64
pacman -S mingw-w64-ucrt-x86_64-meson mingw-w64-ucrt-x86_64-gcc

# 2. Nettoyer et recommencer
cd openslide-patch/openslide
rm -rf build
cd ../..
bash Scripts/04_rebuild_openslide.sh

# 3. Voir les logs détaillés
cd openslide-patch
bash build-openslide.sh 2>&1 | tee build.log
```

---

## Bonnes Pratiques

### ✅ À Faire

- **Toujours créer un backup** avant une mise à jour majeure
- **Tester après chaque modification** (compilation + tests réels)
- **Documenter vos patchs** (pourquoi, quoi, comment)
- **Committer régulièrement** avec des messages clairs
- **Garder le fork à jour** (tous les 3-6 mois)

### ❌ À Éviter

- **Ne jamais modifier `main`** dans votre fork (réservé pour sync upstream)
- **Ne pas forcer push sans `--force-with-lease`** (risque de perdre des commits)
- **Ne pas compiler sans les patchs** (utiliser toujours la branche `varuna-patches`)
- **Ne pas ignorer les tests** après une mise à jour

---

## Commandes Git Utiles

### Voir l'État du Submodule

```bash
# Status global
git submodule status

# Dans le submodule
cd openslide-patch/openslide
git branch -vv
git remote -v
git log --oneline --graph --all -10
```

### Synchroniser Fork avec Upstream

```bash
cd openslide-patch/openslide

# Récupérer upstream
git fetch upstream

# Voir les différences
git log --oneline HEAD..upstream/main

# Rebaser (fait par le script 02)
git rebase upstream/main
```

### Lister les Patchs Appliqués

```bash
cd openslide-patch/openslide

# Commits depuis la dernière version officielle
git log --oneline upstream/main..HEAD

# Voir les diff
git diff upstream/main..HEAD
```

---

## Référence Rapide

| Action | Script | Fréquence |
|--------|--------|-----------|
| Configuration initiale | `01_setup_fork.sh` | Une fois |
| Mise à jour OpenSlide | `02_update_from_upstream.sh [version]` | Tous les 3-6 mois |
| Ajouter un patch | `03_add_new_patch.sh <patch-file>` | Au besoin |
| Recompiler | `04_rebuild_openslide.sh` | Après chaque modif |

---

## Ressources

### Documentation OpenSlide

- Site officiel: https://openslide.org/
- GitHub: https://github.com/openslide/openslide
- Issues: https://github.com/openslide/openslide/issues
- Formats supportés: https://openslide.org/formats/

### Documentation VarunaPoC

- Formats supportés: `../docs/FORMATS_SUPPORTED.md`
- Error Ventana LEFT: `../docs/ERROR_BIF_DIRECTION_LEFT.md`
- Build OpenSlide: `../openslide-patch/README.md`

### Git Submodules

- Documentation: https://git-scm.com/book/en/v2/Git-Tools-Submodules
- Workflow: https://github.blog/2016-02-01-working-with-submodules/

---

## Support

**Questions ou problèmes:**
- Consultez la documentation VarunaPoC
- Vérifiez les issues GitHub d'OpenSlide
- Contactez l'équipe de développement

---

**Version:** 1.0
**Dernière révision:** 2025-10-28
**Auteur:** Équipe VarunaPoC
