# OpenSlide Patch - Support Direction LEFT pour Ventana BIF

Ce dossier contient le code source d'OpenSlide patché pour supporter les fichiers Ventana BIF avec `direction="LEFT"`.

## Contexte

Certains fichiers BIF Ventana utilisent `direction="LEFT"` dans leurs métadonnées XML, ce qui cause l'erreur :
```
OpenSlideError: Bad direction attribute "LEFT"
```

OpenSlide ne supporte officiellement que `direction="RIGHT"` et `direction="UP"`.

## Solution Implémentée

Le patch traite `direction="LEFT"` comme `direction="RIGHT"`. Selon les tests de la communauté OpenSlide (issue #234), cette approche produit des images presque identiques.

### Fichiers Modifiés

- **`openslide/src/openslide-vendor-ventana.c`** :
  - Ligne 71 : Ajout de la constante `DIRECTION_LEFT`
  - Lignes 573-581 : Ajout du cas `else if` pour traiter LEFT comme RIGHT

## Compilation et Installation

### Prérequis

- **MSYS2** installé avec l'environnement **UCRT64**
- Accès administrateur (pour l'installation finale)

### Étapes Rapides

1. Ouvrir **MSYS2 UCRT64** (icône violette)
2. Naviguer vers ce dossier :
   ```bash
   cd /c/Users/junio/Desktop/CHU-UCL/VarunaPoC/openslide-patch
   ```
3. Exécuter le script de build :
   ```bash
   ./build-openslide.sh
   ```

Le script va :
1. Installer toutes les dépendances nécessaires
2. Configurer le projet avec Meson
3. Compiler OpenSlide
4. Installer la nouvelle DLL (remplace l'ancienne)

### Étapes Manuelles (si le script échoue)

#### 1. Installer les dépendances

Dans MSYS2 UCRT64 :
```bash
pacman -S --needed \
    mingw-w64-ucrt-x86_64-gcc \
    mingw-w64-ucrt-x86_64-meson \
    mingw-w64-ucrt-x86_64-ninja \
    mingw-w64-ucrt-x86_64-pkgconf \
    mingw-w64-ucrt-x86_64-glib2 \
    mingw-w64-ucrt-x86_64-cairo \
    mingw-w64-ucrt-x86_64-gdk-pixbuf2 \
    mingw-w64-ucrt-x86_64-libxml2 \
    mingw-w64-ucrt-x86_64-libtiff \
    mingw-w64-ucrt-x86_64-openjpeg2 \
    mingw-w64-ucrt-x86_64-sqlite3
```

#### 2. Configurer le build

```bash
cd openslide
meson setup builddir --prefix=/ucrt64 --buildtype=release
```

#### 3. Compiler

```bash
meson compile -C builddir
```

Durée : 2-5 minutes selon votre machine.

#### 4. Installer

```bash
meson install -C builddir
```

Cette commande remplace `C:\msys64\ucrt64\bin\libopenslide-1.dll` par la version patchée.

## Vérification

### Test 1 : Vérifier la version installée

Dans un terminal Windows (PowerShell/CMD) :
```powershell
cd C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend
python -c "import openslide; print(f'OpenSlide version: {openslide.__version__}'); print(f'Library version: {openslide.__library_version__}')"
```

### Test 2 : Tester un fichier BIF avec LEFT direction

```powershell
python -c "
import sys
sys.path.insert(0, '.')
import config_openslide
import openslide

# Fichier qui échouait avant le patch
slide = openslide.OpenSlide(r'C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides\Ventana BIF\Ventana-1.bif')
print(f'SUCCESS! Dimensions: {slide.dimensions}')
print(f'Levels: {slide.level_count}')
slide.close()
"
```

**Résultat attendu** :
```
[OK] OpenSlide DLL directory added: C:\msys64\ucrt64\bin
SUCCESS! Dimensions: (46000, 32914)
Levels: 5
```

### Test 3 : Scan complet

```bash
cd backend
python -c "
import sys
sys.path.insert(0, '.')
from services.slide_scanner import scan_slides_directory

slides = scan_slides_directory(r'../Slides')
bif_slides = [s for s in slides if s['format'] == 'Ventana BIF']

print(f'Total BIF slides: {len(bif_slides)}')
for s in bif_slides:
    status = 'SUPPORTED' if s['is_supported'] else 'UNSUPPORTED'
    print(f'  [{status}] {s[\"name\"]}')
"
```

**Résultat attendu** : Tous les fichiers BIF doivent maintenant être `SUPPORTED`.

## Troubleshooting

### Erreur : "command not found: meson"

Les dépendances ne sont pas installées. Exécutez l'étape 1 (installer les dépendances).

### Erreur : "Permission denied" lors de l'installation

Vous devez exécuter MSYS2 en tant qu'administrateur, ou modifier manuellement la DLL.

**Solution alternative** :
```bash
# Copier la DLL compilée manuellement
cp builddir/src/libopenslide-1.dll /ucrt64/bin/libopenslide-1.dll
```

### Erreur : Compilation échoue avec des erreurs de dépendances

Vérifiez que vous êtes bien dans **MSYS2 UCRT64** (pas MinGW64 ou MSYS2).
Le prompt doit afficher `UCRT64` en violet.

### Le patch ne semble pas fonctionner

1. Vérifiez que la nouvelle DLL a bien été installée :
   ```bash
   ls -lh /ucrt64/bin/libopenslide-1.dll
   ```
   La date de modification doit correspondre à votre compilation.

2. Redémarrez Python/le backend pour recharger la DLL.

3. Vérifiez que `config_openslide.py` pointe bien vers `C:\msys64\ucrt64\bin`.

## Retour à la Version Officielle

Si vous souhaitez revenir à la version OpenSlide officielle :

```bash
pacman -S --force mingw-w64-ucrt-x86_64-openslide
```

Cela réinstallera la version du package MSYS2 (sans le patch).

## Références

- **Issue OpenSlide #234** : https://github.com/openslide/openslide/issues/234
- **Issue OpenSlide #303** : https://github.com/openslide/openslide/issues/303
- **Documentation VarunaPoC** : `../docs/ERROR_BIF_DIRECTION_LEFT.md`
- **Patch file** : `ventana-left-direction.patch`

## Notes Techniques

### Pourquoi traiter LEFT comme RIGHT ?

D'après les tests de la communauté OpenSlide :
- Les fichiers avec `direction="LEFT"` et `direction="RIGHT"` produisent des images visuellement identiques
- La différence pourrait être liée à une configuration matérielle du scanner (miroir optique)
- Aucune documentation officielle Ventana n'explique la différence

### Impact sur les Coordonnées

Le patch n'affecte **que** la lecture des métadonnées de jointure entre tuiles. Les coordonnées pixel restent identiques et cohérentes avec OpenSeadragon.

### Maintenance

Ce patch est basé sur OpenSlide 4.0.0 (dernière version stable). Si vous mettez à jour OpenSlide via pacman, le patch sera écrasé et devra être réappliqué.

## Auteurs

- **Patch** : Équipe VarunaPoC (basé sur discussions communauté OpenSlide)
- **OpenSlide** : Carnegie Mellon University et contributeurs
- **Date** : 2025-10-21
