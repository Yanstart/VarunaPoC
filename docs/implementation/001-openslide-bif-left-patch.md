# OpenSlide BIF direction=LEFT Patch

## Probleme

Certains fichiers Ventana BIF utilisent `direction="LEFT"` dans leur XML interne.
OpenSlide 4.0.0 officiel ne reconnait que `RIGHT` et `UP`, ce qui provoque :

```
OpenSlideError: Bad direction attribute "LEFT"
```

Le fichier est **detecte** par `OpenSlide.detect_format()` mais **non-ouvrable** par `OpenSlide()`.

## Diagnostic

- `openslide-bin` (pip) bundle sa propre `libopenslide.so.1` dans le venv
- Cette lib prend priorite sur la lib systeme (`/usr/lib/`)
- Le patch existait dans `openslide-patch/ventana-left-direction.patch` mais :
  - N'etait jamais compile sur Linux (script cible MSYS2/Windows)
  - Le submodule `openslide-patch/openslide/` n'avait pas le patch applique

## Patch

Fichier : `openslide-patch/ventana-left-direction.patch`

```c
// Dans openslide-vendor-ventana.c :
// 1. Ajouter la constante
static const char DIRECTION_LEFT[] = "LEFT";

// 2. Ajouter le handler (traite LEFT comme RIGHT)
} else if (!xmlStrcmp(direction, BAD_CAST DIRECTION_LEFT)) {
    struct tile *tile =
      &area->tiles[tile2_row * area->tiles_across + tile2_col];
    joint = &tile->left;
    ok = (tile2_col == tile1_col + 1 && tile2_row == tile1_row);
}
```

## Procedure de compilation (Linux)

```bash
# Prerequis
apt-get install -y meson libsqlite3-dev ninja-build \
  libcairo2-dev libglib2.0-dev libgdk-pixbuf-2.0-dev \
  libxml2-dev libtiff-dev libopenjp2-7-dev libpng-dev \
  libjpeg-dev zlib1g-dev libzstd-dev

# Appliquer le patch
cd openslide-patch/openslide
git apply ../ventana-left-direction.patch

# Compiler
meson setup builddir --buildtype=release --default-library=shared
meson compile -C builddir

# Remplacer dans le venv
OPENSLIDE_BIN="backend/venv/lib/python3.13/site-packages/openslide_bin"
cp "$OPENSLIDE_BIN/libopenslide.so.1" "$OPENSLIDE_BIN/libopenslide.so.1.BACKUP"
cp builddir/src/libopenslide.so.1.0.0 "$OPENSLIDE_BIN/libopenslide.so.1"

# Installer libdicom (dependance runtime)
cp builddir/subprojects/libdicom-1.2.0/libdicom.so.1.2.0 /usr/local/lib/libdicom.so.1
ldconfig
```

## Verification

```bash
cd backend && source venv/bin/activate
python3 -c "
import openslide, glob
for f in glob.glob('../Slides/**/*.bif', recursive=True):
    slide = openslide.OpenSlide(f)
    print(f'OK: {f} -> {slide.dimensions}')
    slide.close()
"
```

## Resultat

| Fichier | Avant patch | Apres patch |
|---------|-------------|-------------|
| Ventana-1.bif | Bad direction "LEFT" | 48597x21504, 8 niveaux |
| OS-1.bif | OK | OK |
| OS-2.bif | OK | OK |
| HE_BIF_1.bif | OK | OK |

## Rollback

```bash
cp "$OPENSLIDE_BIN/libopenslide.so.1.BACKUP" "$OPENSLIDE_BIN/libopenslide.so.1"
```

## Attention

- `pip install --upgrade openslide-bin` ecrasera le .so patche — il faudra re-appliquer
- Le backup est dans `libopenslide.so.1.BACKUP`
- Ref upstream : https://github.com/openslide/openslide/issues/234
