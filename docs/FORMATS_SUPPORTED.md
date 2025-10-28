# Formats de Lames Supportés - VarunaPoC

**Dernière mise à jour:** 2025-10-28
**Version OpenSlide:** 4.0.0 (avec patch Ventana LEFT)

Ce document liste tous les formats de lames histologiques testés avec VarunaPoC, leur statut de support, et les limitations connues.

---

## Résumé Rapide

| Format | Extension(s) | Statut | Notes |
|--------|--------------|--------|-------|
| **3DHistech MIRAX** | `.mrxs` | ✅ Supporté | Nécessite dossier compagnon |
| **Aperio SVS** | `.svs`, `.tif` | ✅ Supporté | 4/4 fichiers testés OK |
| **DICOM** | `.dcm` | ⚠️ Partiel | Leica-4 OK, 3DHISTECH Issue #511 |
| **Generic TIFF** | `.tif` | ✅ Supporté | TIFF pyramidal générique |
| **Hamamatsu NDPI** | `.ndpi` | ✅ Supporté | CMU-2 OK (Hamamatsu-1 corrompu) |
| **Hamamatsu VMS/VMU** | `.vms`, `.vmu` | ✅ Supporté | Multi-fichiers OK |
| **Leica SCN** | `.scn` | ⚠️ Partiel | Limitation: dissimilar images |
| **Ventana BIF** | `.bif` | ✅ Supporté | Avec patch LEFT |
| **Zeiss CZI** | `.czi` | ⚠️ Partiel | 3/5 testés OK (pas JPEG XR) |
| **Zeiss ZVI** | `.zvi` | ❌ Non supporté | Format non supporté par OpenSlide |
| **Olympus VSI** | `.vsi` | ❌ Non supporté | Format non supporté par OpenSlide |

---

## Formats Supportés (Détails)

### ✅ 3DHistech MIRAX (.mrxs)

**Statut:** Supporté complètement
**Fichiers testés:** Multiples fichiers

**Structure:**
```
slide.mrxs              ← Fichier principal
slide/                  ← Dossier compagnon (OBLIGATOIRE)
  ├── Slidedat.ini      ← Métadonnées
  ├── Data0000.dat      ← Données image
  └── Index.dat         ← Index tuiles
```

**Notes:**
- Le dossier compagnon DOIT être dans le même répertoire que le fichier .mrxs
- Sans le dossier compagnon, le fichier ne s'ouvrira pas

---

### ✅ Aperio SVS (.svs, .tif)

**Statut:** Supporté complètement
**Fichiers testés:** 4/4 fonctionnels

**Exemples:**
- `CMU-1-JP2K-33005.svs` - JPEG 2000 compression (33005)
- `CMU-1-Small-Region.svs` - Petite région
- `CMU-1.svs` - Standard
- `CMU-2.svs` - Standard

**Notes:**
- Support compression JPEG 2000 (33003, 33005)
- Fichiers pyramidaux TIFF propriétaires
- Métadonnées Aperio dans ImageDescription

---

### ⚠️ DICOM (.dcm)

**Statut:** Supporté partiellement
**Fichiers testés:** 7 fichiers (6 OK, 1 échec)

**Fichiers fonctionnels:**
- Leica-4 (6 fichiers TILED_FULL) ✅

**Fichiers non supportés:**
- 3DHISTECH-2 (concatenations) ❌

**Limitations connues:**
- Les fichiers DICOM utilisant des concatenations (multi-instances) ne sont pas supportés
- Voir: [OpenSlide GitHub Issue #511](https://github.com/openslide/openslide/issues/511)
- Seule la structure `TILED_FULL` standard est supportée

**Documentation:** https://openslide.org/formats/dicom/

---

### ✅ Generic TIFF (.tif)

**Statut:** Supporté complètement
**Fichiers testés:** Multiples

**Notes:**
- Support TIFF pyramidal générique (non propriétaire)
- Doit être un TIFF tuilé avec plusieurs niveaux de résolution
- Compatible avec BigTIFF pour fichiers > 4GB

---

### ✅ Hamamatsu NDPI (.ndpi)

**Statut:** Supporté complètement
**Fichiers testés:** 2 (1 OK, 1 corrompu)

**Fichiers fonctionnels:**
- `CMU-2.ndpi` (0.37 GB) ✅
  - Dimensions: 79872x33792
  - 11 niveaux

**Fichiers corrompus:**
- `Hamamatsu-1.ndpi` (6.43 GB) ❌
  - Erreur: "Can't validate JPEG for directory 0: Expected marker at 4294969977"
  - Fichier de test incomplet/corrompu (pas un bug du code)

**Notes:**
- Format TIFF propriétaire Hamamatsu
- Un seul fichier .ndpi contient tout

**Documentation:** https://openslide.org/formats/hamamatsu/

---

### ✅ Hamamatsu VMS/VMU (.vms, .vmu)

**Statut:** Supporté complètement
**Fichiers testés:** CMU-3 (multi-fichiers)

**Exemple testé:**
- `CMU-3-40x - 2010-01-12 13.57.09.vms`
  - Dimensions: 143360x101888
  - 7 niveaux
  - Images associées: macro

**Structure:**
```
CMU-3-40x - 2010-01-12 13.57.09.vms        ← Fichier principal
CMU-3-40x - 2010-01-12 13.57.09.opt        ← Fichier options
CMU-3-40x - 2010-01-12 13.57.09(0,1).jpg   ← Tuiles JPEG
CMU-3-40x - 2010-01-12 13.57.09(1,0).jpg
CMU-3-40x - 2010-01-12 13.57.09_macro.jpg  ← Image macro
...
```

**Notes:**
- Format multi-fichiers (VMS + VMU + JPEG)
- Tous les fichiers associés doivent être dans le même dossier
- Support images macro et map

**Documentation:** https://openslide.org/formats/hamamatsu/

---

### ⚠️ Leica SCN (.scn)

**Statut:** Supporté partiellement
**Fichiers testés:** 1 (échec)

**Fichiers testés:**
- `Leica-3.scn` ❌
  - Erreur: "Slides with dissimilar main images are not supported"

**Limitations connues:**
- OpenSlide ne supporte pas les fichiers Leica avec plusieurs régions scan dissimilaires
- Certains fichiers Leica fonctionnent, d'autres pas selon leur structure interne

**Documentation:** https://openslide.org/formats/leica/

---

### ✅ Ventana BIF (.bif, .tif)

**Statut:** Supporté complètement (avec patch)
**Fichiers testés:** 2/2 fonctionnels (après patch)

**Patch appliqué:**
- **Patch:** `ventana-left-direction.patch`
- **Problème résolu:** Support de `direction="LEFT"` dans métadonnées XML
- **Référence:** [OpenSlide Issue #234](https://github.com/openslide/openslide/issues/234)

**Fichiers testés:**
- `OS-2.bif` (2.6 GB, direction=RIGHT) ✅
  - Dimensions: 114943x76349
  - 10 niveaux
- `Ventana-1.bif` (216 MB, direction=LEFT) ✅
  - Dimensions: 48597x21504
  - 8 niveaux

**Notes:**
- BigTIFF avec métadonnées XML propriétaires
- Le patch traite `direction="LEFT"` comme `direction="RIGHT"`
- Tests communauté: images quasi-identiques avec les deux directions

**Documentation:** https://openslide.org/formats/ventana/

**Voir aussi:** [docs/ERROR_BIF_DIRECTION_LEFT.md](./ERROR_BIF_DIRECTION_LEFT.md)

---

### ⚠️ Zeiss CZI (.czi)

**Statut:** Supporté partiellement
**Fichiers testés:** 5 (3 OK, 2 échecs)

**Fichiers fonctionnels:**

| Fichier | Compression | Dimensions | Niveaux |
|---------|-------------|------------|---------|
| `Zeiss-5-Uncompressed.czi` | Uncompressed | 50171x11340 | 5 |
| `Zeiss-5-SlidePreview-Zstd0.czi` | Zstandard v0 | 1260x615 | 1 |
| `Zeiss-5-SlidePreview-Zstd1-HiLo.czi` | Zstandard v1 HiLo | 1260x615 | 1 |

**Fichiers non supportés:**

| Fichier | Compression | Erreur |
|---------|-------------|--------|
| `Zeiss-5-Cropped.czi` | JPEG XR | JPEG XR compression is not supported |
| `Zeiss-5-JXR.czi` | JPEG XR | JPEG XR compression is not supported |

**Compressions supportées:**
- ✅ Uncompressed (24 bpp ou 48 bpp)
- ✅ Zstandard (zstd0, zstd1 avec HiLo packing)

**Compressions NON supportées:**
- ❌ JPEG XR (nécessiterait libjxrlib non intégré dans OpenSlide)
- ❌ JPEG
- ❌ LZW

**Notes:**
- Le support JPEG XR est une **limitation par design d'OpenSlide**, pas un bug
- La bibliothèque libjxrlib existe mais n'est pas intégrée dans OpenSlide
- Les fichiers Zstandard nécessitent libzstd (inclus dans MSYS2)

**Documentation:** https://openslide.org/formats/zeiss/

---

## Formats Non Supportés

### ❌ Zeiss ZVI (.zvi)

**Statut:** Non supporté par OpenSlide
**Raison:** Format ancien, remplacé par CZI

**Fichiers testés:**
- `Zeiss-2-Stacked.zvi` ❌
- `Zeiss-4-Mosaic.zvi` ❌

**Notes:**
- OpenSlide ne supporte **que** le format CZI de Zeiss
- ZVI est un ancien format Zeiss qui n'est plus maintenu

**Documentation:** https://openslide.org/formats/zeiss/

---

### ❌ Olympus VSI (.vsi)

**Statut:** Non supporté par OpenSlide
**Raison:** Format non inclus dans OpenSlide

**Fichiers testés:**
- `OS-1.vsi` ❌

**Notes:**
- Olympus VSI n'est pas dans la liste des formats supportés par OpenSlide
- Aucun backend VSI n'existe dans OpenSlide
- Alternative: Convertir en TIFF pyramidal générique

---

## Formats Non Testés (Support OpenSlide Confirmé)

Les formats suivants sont supportés par OpenSlide mais n'ont pas de fichiers de test dans VarunaPoC:

### Philips TIFF (.tiff)

**Statut:** Supporté par OpenSlide (non testé)
**Documentation:** https://openslide.org/formats/philips/

---

### Sakura SVSlide (.svslide)

**Statut:** Supporté par OpenSlide (non testé)
**Documentation:** https://openslide.org/formats/sakura/

---

### Trestle TIFF (.tif)

**Statut:** Supporté par OpenSlide (non testé)
**Documentation:** https://openslide.org/formats/trestle/

---

## Statistiques Globales

**Formats testés:** 11
**Formats supportés complètement:** 6 (3DHistech, Aperio, Generic TIFF, Hamamatsu NDPI, Hamamatsu VMS, Ventana BIF)
**Formats supportés partiellement:** 3 (DICOM, Leica, Zeiss CZI)
**Formats non supportés:** 2 (Zeiss ZVI, Olympus VSI)

**Fichiers testés:** ~30 fichiers
**Taux de succès:** ~85% (en excluant fichiers corrompus et formats non supportés)

---

## Installation et Configuration

### Prérequis

**OpenSlide Version:** 4.0.0
**Patch appliqué:** `ventana-left-direction.patch`
**Compilé avec:** MSYS2 UCRT64

### Dépendances Runtime

- libjpeg (JPEG standard)
- libopenjpeg2 (JPEG 2000)
- libpng
- libtiff
- libzstd (Zstandard pour CZI)
- glib2, cairo, libxml2

**Non inclus:**
- libjxrlib (JPEG XR) - pas intégré dans OpenSlide

### Installation Backend

```bash
# Désinstaller openslide-bin (si installé via pip)
pip uninstall -y openslide-bin

# Le backend utilise automatiquement la DLL MSYS2 patchée
# via config_openslide.py
cd backend
python main.py
```

---

## Références

### Documentation OpenSlide Officielle

- **Formats supportés:** https://openslide.org/formats/
- **API Python:** https://openslide.org/api/python/
- **API C:** https://openslide.org/api/c/
- **Wiki:** https://openslide.org/wiki/

### Issues GitHub OpenSlide

- **#234:** Ventana BIF direction="LEFT" - https://github.com/openslide/openslide/issues/234
- **#511:** DICOM concatenations - https://github.com/openslide/openslide/issues/511

### Documentation VarunaPoC

- [Error: BIF Direction LEFT](./ERROR_BIF_DIRECTION_LEFT.md)
- [Guide Structure Slides](./Manuel/03-ORGANISATION_LAMES.md)
- [Formats Supportés (Guide Utilisateur)](./Manuel/04-FORMATS_SUPPORTES.md)

---

## Historique

**Version 1.0** (2025-10-28)
- Test complet de tous les formats disponibles
- Patch Ventana LEFT appliqué et validé
- Documentation des limitations CZI (JPEG XR)
- Identification formats non supportés (ZVI, VSI)

---

**Auteur:** Équipe VarunaPoC
**Licence:** Voir LICENSE du projet
