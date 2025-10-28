# Formats de Lames Supportés

**Statut:** ✅ Validé et prêt à l'emploi
**Dernière mise à jour:** 2025-10-28
**Fonctionnalité:** Visualisation de lames histologiques multi-formats

---

## Vue d'Ensemble

VarunaPoC supporte les principaux formats de lames histologiques utilisés en pathologie numérique. Cette page liste les formats validés et leurs particularités.

---

## Formats Supportés

### ✅ Formats Complètement Supportés

Ces formats fonctionnent sans limitation dans VarunaPoC:

| Format | Extensions | Fabricant | Notes |
|--------|------------|-----------|-------|
| **3DHistech** | `.mrxs` | 3DHistech | Nécessite dossier compagnon |
| **Aperio** | `.svs`, `.tif` | Leica Biosystems | Format standard US |
| **Hamamatsu NDPI** | `.ndpi` | Hamamatsu | Fichier unique |
| **Hamamatsu VMS** | `.vms`, `.vmu` | Hamamatsu | Multi-fichiers |
| **Generic TIFF** | `.tif` | Standard | TIFF pyramidal |
| **Ventana BIF** | `.bif` | Roche/Ventana | Avec patch spécial |

---

### ⚠️ Formats Partiellement Supportés

Ces formats fonctionnent selon certaines conditions:

| Format | Extensions | Limitations |
|--------|------------|-------------|
| **Zeiss CZI** | `.czi` | Seulement compression Uncompressed et Zstandard (pas JPEG XR) |
| **DICOM** | `.dcm` | Seulement structure TILED_FULL standard |
| **Leica** | `.scn` | Certains fichiers multi-régions non supportés |

---

### ❌ Formats Non Supportés

Ces formats ne peuvent pas être ouverts:

| Format | Extensions | Raison |
|--------|------------|--------|
| **Zeiss ZVI** | `.zvi` | Format ancien, non supporté par OpenSlide |
| **Olympus VSI** | `.vsi` | Non implémenté dans OpenSlide |

---

## Comment Savoir si Mon Fichier Est Supporté?

### Méthode 1: Via l'Explorateur

1. Ouvrez VarunaPoC
2. Naviguez vers le dossier contenant votre lame
3. Les fichiers supportés apparaissent avec une **pastille verte** ✅
4. Les fichiers non supportés apparaissent avec une **pastille rouge** ❌

### Méthode 2: Essayez de l'Ouvrir

Cliquez simplement sur le fichier. Si la visionneuse s'ouvre, le fichier est supporté!

---

## Cas d'Usage par Format

### 3DHistech (.mrxs)

**Quand l'utiliser:**
- Scanners 3DHistech (Pannoramic)
- Format standard en Europe

**Structure de fichiers:**
```
ma_lame.mrxs              ← Fichier principal à ouvrir
ma_lame/                  ← Dossier compagnon (NE PAS SUPPRIMER!)
  ├── Slidedat.ini
  ├── Data0000.dat
  └── Index.dat
```

**⚠️ Important:** Ne jamais supprimer ou déplacer le dossier compagnon (même nom que le fichier .mrxs) !

---

### Aperio SVS (.svs)

**Quand l'utiliser:**
- Scanners Aperio/Leica
- Format standard aux États-Unis
- Archives de pathologie

**Particularités:**
- Un seul fichier (pas de dossier compagnon)
- Peut être très volumineux (plusieurs GB)
- Compression JPEG 2000 supportée

---

### Hamamatsu NDPI (.ndpi)

**Quand l'utiliser:**
- Scanners Hamamatsu NanoZoomer
- Fichier unique facile à archiver

**Particularités:**
- Un seul fichier .ndpi
- Très haute résolution (> 100 000 pixels)

---

### Hamamatsu VMS/VMU (.vms, .vmu)

**Quand l'utiliser:**
- Ancien format Hamamatsu
- Archives historiques

**Structure de fichiers:**
```
ma_lame.vms               ← Fichier principal à ouvrir
ma_lame.opt               ← Options (optionnel)
ma_lame(0,0).jpg          ← Tuiles JPEG
ma_lame(0,1).jpg
ma_lame_macro.jpg         ← Image macro
...
```

**⚠️ Important:** Tous les fichiers doivent rester ensemble dans le même dossier !

---

### Ventana BIF (.bif)

**Quand l'utiliser:**
- Scanners Roche/Ventana iScan
- Immunohistochimie

**Particularités:**
- Un seul fichier
- VarunaPoC inclut un patch spécial pour support complet
- Peut contenir plusieurs focalisations (Z-stack)

---

### Zeiss CZI (.czi)

**Quand l'utiliser:**
- Scanners Zeiss Axio Scan
- Microscopie confocale

**⚠️ Limitations:**
- **Fonctionne:** Fichiers non compressés ou Zstandard
- **Ne fonctionne PAS:** Fichiers JPEG XR

**Comment vérifier:**
Essayez simplement d'ouvrir le fichier. Si erreur "JPEG XR compression is not supported", le fichier utilise une compression non supportée.

---

### DICOM (.dcm)

**Quand l'utiliser:**
- Intégration PACS hospitalier
- Archives médicales standardisées

**⚠️ Limitations:**
- Seuls les fichiers DICOM `TILED_FULL` standard fonctionnent
- Les fichiers multi-instances (concatenations) ne sont pas supportés

---

### Generic TIFF (.tif)

**Quand l'utiliser:**
- Export depuis autres logiciels
- Format universel

**Particularités:**
- Doit être un TIFF pyramidal (multi-résolutions)
- Peut supporter BigTIFF (> 4 GB)

---

## Organisation Recommandée des Fichiers

### Bonne Organisation ✅

```
/Slides/
  ├── 3DHistech/
  │   ├── patient_001.mrxs
  │   ├── patient_001/         ← Dossier compagnon
  │   ├── patient_002.mrxs
  │   └── patient_002/
  │
  ├── Aperio/
  │   ├── colon_2024_01.svs
  │   └── liver_2024_02.svs
  │
  └── Hamamatsu/
      ├── slide_A.ndpi
      └── VMS_Archives/
          ├── old_slide.vms
          ├── old_slide.opt
          └── old_slide(0,0).jpg
```

### Mauvaise Organisation ❌

```
/Slides/
  ├── patient_001.mrxs         ← Dossier compagnon manquant!
  ├── slide_A.vms              ← Fichiers JPEG manquants!
  └── random_mix/
      ├── file1.mrxs
      ├── file2/               ← Compagnon de file3, pas file1!
      └── file3.mrxs
```

---

## Dépannage

### Mon fichier .mrxs ne s'ouvre pas

**Cause probable:** Dossier compagnon manquant

**Solution:**
1. Vérifiez qu'un dossier portant le même nom existe
2. Exemple: `slide.mrxs` doit avoir un dossier `slide/`
3. Si le dossier manque, le fichier est incomplet

---

### Mon fichier .czi ne s'ouvre pas (erreur JPEG XR)

**Cause:** Compression JPEG XR non supportée

**Solution:**
- Utilisez un logiciel Zeiss pour ré-exporter en format non compressé ou Zstandard
- Ou convertissez en TIFF générique

---

### Mon fichier .vms ne s'ouvre pas

**Cause probable:** Fichiers JPEG manquants

**Solution:**
1. Vérifiez que tous les fichiers `.jpg` sont présents
2. Recherchez les fichiers `(x,y).jpg` dans le même dossier
3. Si fichiers manquants, l'archive est incomplète

---

### J'ai un format non supporté (ZVI, VSI)

**Solution:**
1. Utilisez le logiciel du fabricant pour visualiser
2. Ou exportez en TIFF pyramidal générique
3. Ou contactez-nous pour prioriser le support

---

## Formats Futurs

VarunaPoC pourra supporter ces formats dans les prochaines versions:

- **Philips TIFF** (.tiff) - Déjà supporté par OpenSlide, juste non testé
- **Sakura** (.svslide) - Déjà supporté par OpenSlide, juste non testé
- **Olympus VSI** (.vsi) - Nécessite développement spécifique

---

## Références Techniques

Pour plus de détails techniques (développeurs):
- [Documentation complète formats](../FORMATS_SUPPORTED.md)
- [OpenSlide formats officiels](https://openslide.org/formats/)

---

## Prochaines Étapes

**Si votre format est supporté:**
- Lisez [05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md) pour apprendre à naviguer

**Si votre format n'est pas supporté:**
- Consultez [99-FAQ.md](./99-FAQ.md) section "Formats non supportés"

---

**Version:** 1.0
**Dernière révision:** 2025-10-28
**Auteur:** Équipe VarunaPoC
