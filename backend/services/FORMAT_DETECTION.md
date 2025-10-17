# FORMAT_DETECTION.md

**Documentation officielle de détection multi-format pour VarunaPoC**

Version: 1.5.0
Auteur: VarunaPoC Team
Référence: https://openslide.org/formats/

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture de détection](#architecture-de-détection)
3. [Formats supportés](#formats-supportés)
4. [Structures de fichiers](#structures-de-fichiers)
5. [Validation et autorité](#validation-et-autorité)
6. [Cas particuliers et pièges](#cas-particuliers-et-pièges)
7. [Logs et debugging](#logs-et-debugging)
8. [Tests et validation](#tests-et-validation)

---

## Vue d'ensemble

### Principe fondamental

**OpenSlide.detect_format() est l'AUTORITÉ FINALE** pour toute validation de format.

Notre système de détection fonctionne en deux phases:

1. **Détection heuristique** - Analyse de la structure des fichiers, extensions, patterns
2. **Validation OpenSlide** - Confirmation avec `OpenSlide.detect_format()`

**Aucun fichier n'est retourné comme "supporté" sans validation OpenSlide.**

### Terminologie correcte

- **Point d'entrée (Entry Point)**: Le fichier à passer à `OpenSlide()` - OpenSlide trouve automatiquement les fichiers liés
- **Fichiers joints (Joint Files)**: Fichiers additionnels requis dans le même dossier ou sous-dossiers
- **Companion Directory**: Sous-dossier contenant des fichiers de données (ex: structure MIRAX)
- **Fichiers métadonnées**: Fichiers auxiliaires non-image (XML, INI, TXT)

---

## Architecture de détection

### Classe SlideFormat

```python
@dataclass
class SlideFormat:
    """Format de lame détecté avec structure complète."""
    name: str                           # Nom lisible (ex: "Hamamatsu VMS")
    entry_point: Path                   # Fichier point d'entrée
    is_supported: bool                  # Validé par OpenSlide
    joint_files: List[Path]             # Fichiers joints requis
    companion_dirs: List[Path]          # Dossiers companion
    metadata_files: List[Path]          # Fichiers métadonnées
    format_string: Optional[str]        # Retour OpenSlide ("hamamatsu", "mirax", etc.)
    structure_type: str                 # "single-file", "multi-file", "with-companion-dir"
    detection_method: str               # Méthode utilisée (pour debug)
    notes: str                          # Informations additionnelles
```

### Classe FormatDetector

**Pattern de dispatch par extension:**

```python
class FormatDetector:
    def __init__(self):
        self.dispatch_map = {
            '.vms': self._detect_hamamatsu_vms,
            '.vmu': self._detect_hamamatsu_vmu,
            '.ndpi': self._detect_hamamatsu_ndpi,
            '.mrxs': self._detect_mirax,
            '.svs': self._detect_aperio_svs,
            '.scn': self._detect_leica_scn,
            # ... etc
        }
```

**Avantages de cette architecture:**
- Évite les fichiers kilométriques
- Chaque format a sa propre méthode de détection
- Facilite le debugging et la maintenance
- Permet l'ajout facile de nouveaux formats

---

## Formats supportés

### 1. Hamamatsu VMS - Multi-file JPEG

**Documentation officielle:** https://openslide.org/formats/hamamatsu/

**Structure:**
```
CMU-1.vms           <- Point d'entrée (fichier INI)
CMU-1x01.jpg        <- Tuile JPEG 1
CMU-1x02.jpg        <- Tuile JPEG 2
...
CMU-1x99.jpg        <- Tuile JPEG 99
CMU-1_macro.jpg     <- Image macro (optionnel)
CMU-1_map.jpg       <- Image overview (optionnel)
```

**Détection:**
1. Vérifier que `.vms` est un fichier INI valide avec section `[Uncompressed Virtual Microscope Specimen]`
2. Chercher tous les fichiers `{basename}*.jpg` (excluant `_macro` et `_map`)
3. Valider avec `OpenSlide.detect_format(vms_file)`

**Code de détection:**
```python
def _detect_hamamatsu_vms(self, vms_file: Path) -> Optional[SlideFormat]:
    # 1. Vérifier structure INI
    if not self._is_vms_ini_file(vms_file):
        return None

    # 2. Trouver fichiers joints JPEG
    jpg_pattern = f"{vms_file.stem}*.jpg"
    jpg_files = list(vms_file.parent.glob(jpg_pattern))
    jpg_files = [f for f in jpg_files if '_macro' not in f.stem and '_map' not in f.stem]

    # 3. Validation OpenSlide (AUTORITÉ FINALE)
    format_str = self._validate_with_openslide(vms_file)
    if format_str is None:
        logger.warning(f"VMS structure detected but OpenSlide validation failed: {vms_file}")
        return None

    return SlideFormat(
        name="Hamamatsu VMS",
        entry_point=vms_file,
        is_supported=True,
        joint_files=joint_files,
        structure_type="multi-file",
        format_string=format_str,
        detection_method="VMS INI validation + JPEG joints detection",
        notes=f"VMS index with {len(jpg_files)} JPEG tiles"
    )
```

**Pièges courants:**
- ⚠️ **Ne jamais oublier les fichiers JPEG** - VMS seul est inutile sans les tuiles
- ⚠️ **Exclure _macro et _map** - Ce ne sont pas des tuiles de la pyramide
- ⚠️ **Pattern de nommage strict** - `{basename}x{number}.jpg`

---

### 2. Hamamatsu VMU - Multi-file NGR

**Documentation officielle:** https://openslide.org/formats/hamamatsu/

**Structure:**
```
specimen.vmu            <- Point d'entrée (fichier INI)
specimen001.ngr         <- Fichier NGR 1
specimen002.ngr         <- Fichier NGR 2
...
OptimisationFile.opt    <- Fichier d'optimisation (optionnel)
```

**Détection:**
1. Vérifier que `.vmu` est un fichier INI avec section `[Virtual Microscope Unit]`
2. Chercher fichiers `.ngr` avec pattern `{basename}*.ngr`
3. Chercher fichier `.opt` optionnel
4. Valider avec OpenSlide

**Code de détection:**
```python
def _detect_hamamatsu_vmu(self, vmu_file: Path) -> Optional[SlideFormat]:
    if not self._is_vmu_ini_file(vmu_file):
        return None

    # Trouver fichiers NGR
    ngr_pattern = f"{vmu_file.stem}*.ngr"
    ngr_files = list(vmu_file.parent.glob(ngr_pattern))

    # Chercher fichier OPT
    opt_files = list(vmu_file.parent.glob("*.opt"))

    format_str = self._validate_with_openslide(vmu_file)
    if format_str is None:
        return None

    return SlideFormat(
        name="Hamamatsu VMU",
        entry_point=vmu_file,
        is_supported=True,
        joint_files=ngr_files,
        metadata_files=opt_files,
        structure_type="multi-file",
        format_string=format_str,
        notes=f"VMU index with {len(ngr_files)} NGR files"
    )
```

---

### 3. Hamamatsu NDPI - Single file

**Documentation officielle:** https://openslide.org/formats/hamamatsu/

**Structure:**
```
slide.ndpi              <- Point d'entrée (fichier unique TIFF)
```

**Détection:**
- Fichier unique avec extension `.ndpi`
- Validation directe avec OpenSlide
- Pas de fichiers joints requis

**Caractéristiques:**
- Format TIFF propriétaire Hamamatsu
- Toutes les données dans un seul fichier
- Métadonnées dans tags TIFF personnalisés

---

### 4. MIRAX - Companion Directory Structure

**Documentation officielle:** https://openslide.org/formats/mirax/

**Structure:**
```
Slide1.mrxs                     <- Point d'entrée
Slidedat.ini                    <- Configuration (même dossier)
Slide1/                         <- Companion directory (REQUIS)
    ├── Index.dat               <- Index des tuiles
    ├── Data0001.dat            <- Données niveau 0
    ├── Data0002.dat
    └── ...
```

**Détection:**
1. Fichier `.mrxs` présent
2. Fichier `Slidedat.ini` dans le même dossier
3. Dossier companion `{basename}/` avec fichiers `.dat`
4. Validation OpenSlide

**Code de détection:**
```python
def _detect_mirax(self, mrxs_file: Path) -> Optional[SlideFormat]:
    # 1. Vérifier Slidedat.ini
    slidedat_ini = mrxs_file.parent / "Slidedat.ini"
    if not slidedat_ini.exists():
        logger.warning(f"MIRAX missing Slidedat.ini: {mrxs_file}")
        return None

    # 2. Chercher companion directory
    companion_dir = mrxs_file.parent / mrxs_file.stem
    if not companion_dir.is_dir():
        logger.warning(f"MIRAX missing companion directory: {companion_dir}")
        return None

    # 3. Trouver fichiers .dat dans companion
    dat_files = list(companion_dir.glob("*.dat"))
    if not dat_files:
        logger.warning(f"MIRAX companion directory empty: {companion_dir}")
        return None

    # 4. Validation OpenSlide
    format_str = self._validate_with_openslide(mrxs_file)
    if format_str is None:
        return None

    return SlideFormat(
        name="MIRAX",
        entry_point=mrxs_file,
        is_supported=True,
        companion_dirs=[companion_dir],
        joint_files=dat_files,
        metadata_files=[slidedat_ini],
        structure_type="with-companion-dir",
        format_string=format_str,
        notes=f"MIRAX with companion dir containing {len(dat_files)} data files"
    )
```

**Pièges courants:**
- ⚠️ **Companion directory est REQUIS** - Sans lui, impossible de lire la lame
- ⚠️ **Slidedat.ini critique** - Contient configuration globale
- ⚠️ **Pattern de nommage** - Le companion dir doit avoir le même basename que le .mrxs

---

### 5. Aperio SVS - Single file TIFF

**Documentation officielle:** https://openslide.org/formats/aperio/

**Structure:**
```
slide.svs                       <- Point d'entrée (TIFF pyramidal)
```

**Détection:**
- Extension `.svs`
- Validation OpenSlide (vérifie que c'est bien un TIFF Aperio valide)

**Caractéristiques:**
- Format TIFF BigTIFF propriétaire
- Métadonnées dans ImageDescription (tag 270)
- Support macro et label images

---

### 6. Leica SCN - Single file proprietary

**Documentation officielle:** https://openslide.org/formats/leica/

**Structure:**
```
slide.scn                       <- Point d'entrée (format propriétaire Leica)
```

**Détection:**
- Extension `.scn`
- Validation OpenSlide

**Caractéristiques:**
- Format binaire propriétaire Leica
- Support multi-séries (plusieurs images dans un fichier)

---

### 7. Ventana BIF - Single file TIFF

**Documentation officielle:** https://openslide.org/formats/ventana/

**Structure:**
```
slide.bif                       <- Point d'entrée (BigTIFF)
```

**Détection:**
- Extension `.bif`
- Validation OpenSlide (vérifie structure BigTIFF Ventana)

---

### 8. Sakura SVSLIDE - Single file proprietary

**Documentation officielle:** https://openslide.org/formats/sakura/

**Structure:**
```
slide.svslide                   <- Point d'entrée
```

**Détection:**
- Extension `.svslide`
- Validation OpenSlide

---

### 9. Trestle TIFF - Multi-file with overlaps

**Documentation officielle:** https://openslide.org/formats/trestle/

**Structure:**
```
slide.tif                       <- Point d'entrée (TIFF de base)
slide.tif-0b                    <- Overlap fichier 1
slide.tif-1b                    <- Overlap fichier 2
...
slide.tif.xml                   <- Métadonnées (optionnel)
```

**Détection:**
1. Fichier `.tif` présent
2. Chercher fichiers overlap: `{basename}.tif-*b`
3. Chercher métadonnées XML
4. Validation OpenSlide

**Code de détection:**
```python
def _detect_trestle_tiff(self, tif_file: Path) -> Optional[SlideFormat]:
    # Chercher overlap files
    overlap_pattern = f"{tif_file.name}-*b"
    overlap_files = list(tif_file.parent.glob(overlap_pattern))

    # Chercher XML métadonnées
    xml_file = tif_file.parent / f"{tif_file.name}.xml"
    metadata = [xml_file] if xml_file.exists() else []

    format_str = self._validate_with_openslide(tif_file)
    if format_str != "trestle":
        return None  # Pas un Trestle TIFF

    return SlideFormat(
        name="Trestle TIFF",
        entry_point=tif_file,
        is_supported=True,
        joint_files=overlap_files,
        metadata_files=metadata,
        structure_type="multi-file" if overlap_files else "single-file",
        format_string=format_str,
        notes=f"Trestle with {len(overlap_files)} overlap files"
    )
```

**Pièges courants:**
- ⚠️ **Overlap files pas toujours présents** - Certaines lames Trestle sont single-file
- ⚠️ **Pattern de nommage strict** - `{basename}-{number}b` (pas d'espace)

---

### 10. Generic Tiled TIFF

**Documentation officielle:** https://openslide.org/formats/generic-tiff/

**Structure:**
```
slide.tif                       <- Point d'entrée (TIFF pyramidal)
```

**Détection:**
- Extension `.tif` ou `.tiff`
- Validation OpenSlide retourne "generic-tiff"

**Caractéristiques:**
- TIFF pyramidal standard
- Pas de métadonnées propriétaires
- Supporte compression JPEG, LZW, etc.

---

### 11. Philips TIFF

**Documentation officielle:** https://openslide.org/formats/philips/

**Structure:**
```
slide.tif                       <- Point d'entrée (BigTIFF avec UUID)
```

**Détection:**
- Extension `.tif`
- Validation OpenSlide retourne "philips"

**Caractéristiques:**
- BigTIFF avec structure UUID
- Métadonnées dans tags personnalisés

---

## Structures de fichiers

### Classification par type de structure

**Single-file (fichier unique):**
- Hamamatsu NDPI
- Aperio SVS
- Leica SCN
- Ventana BIF
- Sakura SVSLIDE
- Generic TIFF (sans overlaps)

**Multi-file (fichiers joints dans même dossier):**
- Hamamatsu VMS (+ fichiers JPEG)
- Hamamatsu VMU (+ fichiers NGR)
- Trestle TIFF (+ fichiers overlap)

**With-companion-dir (dossier companion requis):**
- MIRAX (.mrxs + dossier companion + Slidedat.ini)

---

## Validation et autorité

### Méthode de validation OpenSlide

```python
def _validate_with_openslide(self, file_path: Path) -> Optional[str]:
    """
    Validation AUTORITÉ FINALE avec OpenSlide.detect_format().

    Returns:
        format_string si supporté (ex: "hamamatsu", "mirax", "aperio")
        None si non supporté
    """
    try:
        format_str = openslide.OpenSlide.detect_format(str(file_path))

        if format_str is None:
            logger.debug(f"OpenSlide returned None for: {file_path}")
            return None

        logger.info(f"✓ OpenSlide validated: {file_path} -> {format_str}")
        return format_str

    except Exception as e:
        logger.error(f"OpenSlide validation failed for {file_path}: {e}")
        return None
```

### Hiérarchie d'autorité

1. **OpenSlide.detect_format()** - AUTORITÉ ABSOLUE
2. **Détection heuristique** - Pré-filtre pour optimiser
3. **Extension de fichier** - Indice initial seulement

**Règle d'or:** Si OpenSlide dit NON, on ne retourne PAS la lame, même si la structure semble correcte.

---

## Cas particuliers et pièges

### 1. Fichiers JPEG/DAT isolés

**Problème:** Les fichiers `.jpg` et `.dat` peuvent être:
- Des tuiles VMS/MIRAX (VALIDES)
- Des fichiers orphelins (INVALIDES)

**Solution:**
```python
# Ne JAMAIS traiter .jpg/.dat directement
# Seulement via détection VMS/VMU/MIRAX
if extension in ['.jpg', '.dat']:
    logger.debug(f"Skipping isolated {extension} file: {file_path}")
    return None
```

### 2. TIFF ambigus

**Problème:** Un fichier `.tif` peut être:
- Aperio TIFF
- Ventana TIFF
- Trestle TIFF
- Philips TIFF
- Generic pyramidal TIFF
- Simple image TIFF non-pyramidale (INVALIDE)

**Solution:** Utiliser `OpenSlide.detect_format()` pour distinguer:
```python
format_str = openslide.OpenSlide.detect_format(tif_file)
# Returns: "aperio", "ventana", "trestle", "philips", "generic-tiff", ou None
```

### 3. Fichiers _macro et _map

**Problème:** Dans VMS, `slide_macro.jpg` et `slide_map.jpg` ne sont PAS des tuiles.

**Solution:**
```python
jpg_files = [f for f in jpg_files
             if '_macro' not in f.stem and '_map' not in f.stem]
```

### 4. Companion directory manquant

**Problème:** Fichier `.mrxs` sans dossier companion → lame inutilisable

**Solution:** Toujours vérifier existence du companion directory:
```python
companion_dir = mrxs_file.parent / mrxs_file.stem
if not companion_dir.is_dir():
    logger.warning(f"MIRAX missing companion directory: {companion_dir}")
    return None  # Ne PAS retourner la lame
```

---

## Logs et debugging

### Niveaux de logs

**INFO** - Détections réussies:
```
✓ OpenSlide validated: CMU-1.vms -> hamamatsu
Scan complete: 15 validated slides ready for API
```

**WARNING** - Structures incomplètes:
```
⚠ VMS structure detected but missing JPEG files: slide.vms
⚠ MIRAX missing companion directory: C:\Slides\specimen.mrxs
```

**DEBUG** - Décisions de détection:
```
Skipping isolated .jpg file: C:\Slides\image.jpg
Testing VMS detection for: CMU-1.vms
Found 99 JPEG tiles for VMS: CMU-1.vms
```

**ERROR** - Erreurs validation:
```
✗ OpenSlide validation failed for slide.svs: Invalid TIFF structure
```

### Exemple de log complet

```
2025-10-17 14:32:01 - INFO - Starting directory scan: C:\Slides
2025-10-17 14:32:01 - DEBUG - Found 156 files to analyze
2025-10-17 14:32:02 - DEBUG - Testing VMS detection for: CMU-1.vms
2025-10-17 14:32:02 - DEBUG - Found 99 JPEG tiles for VMS: CMU-1.vms
2025-10-17 14:32:02 - INFO - ✓ OpenSlide validated: CMU-1.vms -> hamamatsu
2025-10-17 14:32:03 - DEBUG - Testing MIRAX detection for: Slide1.mrxs
2025-10-17 14:32:03 - DEBUG - Found companion directory: Slide1/ (24 .dat files)
2025-10-17 14:32:03 - INFO - ✓ OpenSlide validated: Slide1.mrxs -> mirax
2025-10-17 14:32:04 - WARNING - ⚠ VMS structure detected but OpenSlide validation failed: broken.vms
2025-10-17 14:32:05 - DEBUG - Skipping isolated .jpg file: thumbnail.jpg
2025-10-17 14:32:10 - INFO - Scan complete: 15 validated slides ready for API
```

---

## Tests et validation

### Structure de tests

```python
# tests/test_format_detector.py

def test_hamamatsu_vms_detection():
    """Test détection VMS avec structure complète."""
    detector = FormatDetector()

    # Test avec vraie lame VMS
    vms_file = Path("test_data/CMU-1.vms")
    result = detector.detect_format(vms_file)

    assert result is not None
    assert result.name == "Hamamatsu VMS"
    assert result.is_supported == True
    assert result.format_string == "hamamatsu"
    assert result.structure_type == "multi-file"
    assert len(result.joint_files) > 0  # Doit avoir des JPEG

def test_mirax_with_companion():
    """Test MIRAX avec companion directory."""
    detector = FormatDetector()

    mirax_file = Path("test_data/Slide1.mrxs")
    result = detector.detect_format(mirax_file)

    assert result is not None
    assert result.name == "MIRAX"
    assert result.structure_type == "with-companion-dir"
    assert len(result.companion_dirs) == 1
    assert len(result.joint_files) > 0  # Fichiers .dat

def test_invalid_vms_rejected():
    """Test qu'un VMS invalide est rejeté."""
    detector = FormatDetector()

    # VMS sans fichiers JPEG
    invalid_vms = Path("test_data/broken.vms")
    result = detector.detect_format(invalid_vms)

    # Doit retourner None car OpenSlide.detect_format() échouera
    assert result is None
```

### Checklist de validation

Pour chaque format, valider:

- [ ] **Détection structure correcte** - Fichiers joints trouvés
- [ ] **Validation OpenSlide réussie** - `detect_format()` retourne non-None
- [ ] **Point d'entrée correct** - Le bon fichier est marqué comme entry_point
- [ ] **Métadonnées enrichies** - joint_files, companion_dirs correctement remplis
- [ ] **Structures incomplètes rejetées** - VMS sans JPEG, MIRAX sans companion
- [ ] **Fichiers isolés ignorés** - .jpg/.dat orphelins non retournés
- [ ] **Logs informatifs** - Décisions de détection tracées

---

## Références officielles

- **OpenSlide Main:** https://openslide.org/
- **OpenSlide Formats:** https://openslide.org/formats/
- **Hamamatsu:** https://openslide.org/formats/hamamatsu/
- **MIRAX:** https://openslide.org/formats/mirax/
- **Aperio:** https://openslide.org/formats/aperio/
- **Leica:** https://openslide.org/formats/leica/
- **Ventana:** https://openslide.org/formats/ventana/
- **Sakura:** https://openslide.org/formats/sakura/
- **Trestle:** https://openslide.org/formats/trestle/
- **Generic TIFF:** https://openslide.org/formats/generic-tiff/
- **Philips:** https://openslide.org/formats/philips/

---

## Contact et support

Pour toute question sur la détection de formats:

1. Consulter les logs de détection (niveau DEBUG)
2. Vérifier la documentation officielle OpenSlide pour le format concerné
3. Tester avec `OpenSlide.detect_format()` directement en Python REPL
4. Consulter le code source de FormatDetector pour le format spécifique

---

**Fin de documentation - Version 1.5.0**
