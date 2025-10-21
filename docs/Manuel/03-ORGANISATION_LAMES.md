# Guide Utilisateur - Structure des Fichiers Slides

**Version:** 1.0
**Date:** 2025-10-21
**Contexte:** VarunaPoC - Histopathology Slide Viewer

---

## Table des Matières

1. [Introduction](#introduction)
2. [Principes Généraux](#principes-généraux)
3. [Formats Supportés](#formats-supportés)
4. [Règles de Structure des Fichiers](#règles-de-structure-des-fichiers)
5. [Détection des Slides](#détection-des-slides)
6. [Dépendances et Fichiers Associés](#dépendances-et-fichiers-associés)
7. [Navigation dans les Dossiers](#navigation-dans-les-dossiers)
8. [Fichiers Sans Extension](#fichiers-sans-extension)
9. [Ajout de Nouveaux Formats](#ajout-de-nouveaux-formats)
10. [Exemples Pratiques](#exemples-pratiques)

---

## Introduction

Ce guide décrit comment VarunaPoC détecte, organise et ouvre les lames histologiques stockées dans différents formats. Il est essentiel de comprendre ces règles pour:

- **Utilisateurs:** Organiser correctement leurs lames sur le disque
- **Développeurs:** Ajouter le support de nouveaux formats
- **Administrateurs:** Configurer des répertoires de lames sur le serveur

---

## Principes Généraux

### Racine des Slides

**Répertoire racine par défaut:** `C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides`

- Tous les chemins de navigation partent de cette racine
- L'utilisateur ne peut pas remonter au-delà de cette racine (sécurité)
- Navigation hiérarchique comme un explorateur de fichiers

### Types de Structures

Les lames peuvent avoir 3 types de structures:

1. **Fichier unique** (`single-file`)
   - Un seul fichier contient toutes les données
   - Exemple: `.svs`, `.ndpi`, certains `.tif`

2. **Multi-fichiers** (`multi-file`)
   - Plusieurs fichiers dans le même dossier
   - Exemple: `.vms` + `.vmu`, DICOM series

3. **Avec dossier companion** (`with-companion-dir`)
   - Un fichier principal + un dossier de même nom (sans extension)
   - Exemple: `.mrxs` + dossier `slide_name/`

---

## Formats Supportés

### Formats Officiellement Supportés (via OpenSlide)

| Extension | Format | Vendor | Structure | Notes |
|-----------|--------|--------|-----------|-------|
| `.svs` | Aperio SVS | Leica/Aperio | `single-file` | Format le plus courant |
| `.tif`, `.tiff` | Generic TIFF | Divers | `single-file` | Pyramidal TIFF uniquement |
| `.ndpi` | Hamamatsu NDPI | Hamamatsu | `single-file` | Très répandu |
| `.vms`, `.vmu` | Hamamatsu VMS/VMU | Hamamatsu | `multi-file` | Nécessite `.vms` + `.vmu` |
| `.scn` | Leica SCN | Leica | `single-file` | BigTIFF interne |
| `.mrxs` | MIRAX | 3DHistech | `with-companion-dir` | **Nécessite dossier companion!** |
| `.bif` | Ventana BIF | Roche/Ventana | `single-file` | Patch appliqué pour direction LEFT |
| `.svslide` | Aperio SVS (alt) | Leica/Aperio | `single-file` | Variante de `.svs` |

### Formats en Développement

| Extension | Format | Status | Notes |
|-----------|--------|--------|-------|
| `.dcm` | DICOM | En cours | Nécessite gestion des séries |
| `.czi` | Carl Zeiss CZI | En cours | Format multi-résolution |

### Fichiers Sans Extension

- **Détectés mais marqués non supportés** pour le moment
- Nécessitent analyse par signature de fichier (magic bytes)
- Futur: Détection par contenu plutôt que par extension

---

## Règles de Structure des Fichiers

### Règle 1: Fichier Unique (Single-File)

**Condition:** Un seul fichier suffit pour ouvrir la lame

**Exemple:**
```
Slides/
└── project_a/
    ├── patient_001.svs          ← Point d'entrée (fichier unique)
    ├── patient_002.ndpi         ← Point d'entrée (fichier unique)
    └── sample_tissue.tif        ← Point d'entrée (fichier unique)
```

**Détection:**
- Extension connue dans la liste des formats `single-file`
- Aucun fichier ou dossier associé requis

---

### Règle 2: Multi-Fichiers (Multi-File)

**Condition:** Plusieurs fichiers **dans le même dossier** sont nécessaires

**Exemple VMS/VMU:**
```
Slides/
└── hamamatsu_slides/
    ├── CMU-1.vms                ← Point d'entrée
    ├── CMU-1.vmu                ← Fichier associé (REQUIS)
    ├── CMU-2.vms                ← Point d'entrée
    └── CMU-2.vmu                ← Fichier associé (REQUIS)
```

**Règles de nommage:**
- Les fichiers associés doivent avoir **le même nom de base**
- Extension différente (`.vms` et `.vmu`)
- Tous dans le **même dossier**

**Détection:**
- Détecter le fichier principal (`.vms`)
- Vérifier la présence du fichier associé (`.vmu`)
- Si absent: marquer comme **non supporté** avec note explicative

---

### Règle 3: Avec Dossier Companion (With-Companion-Dir)

**Condition:** Un fichier principal + un dossier de même nom (sans extension)

**Exemple MRXS (3DHistech):**
```
Slides/
└── 3dhistech_slides/
    ├── sample_kidney.mrxs       ← Point d'entrée (petit fichier index)
    ├── sample_kidney/           ← Dossier companion (REQUIS, nom identique!)
    │   ├── Slidedat.ini         ← Métadonnées (dimensions, niveaux, etc.)
    │   ├── Data0000.dat         ← Données image (tuiles)
    │   ├── Data0001.dat
    │   ├── Data0002.dat
    │   └── Index.dat            ← Index des tuiles
    ├── sample_liver.mrxs        ← Point d'entrée
    └── sample_liver/            ← Dossier companion
        ├── Slidedat.ini
        ├── Data0000.dat
        └── ...
```

**Règles de nommage STRICTES:**

1. **Fichier principal:** `{nom}.mrxs`
2. **Dossier companion:** `{nom}/` (EXACTEMENT le même nom, sans extension)
3. **Fichiers internes:** Structure imposée par le fabricant

**Détection:**
- Détecter le fichier `.mrxs`
- Vérifier la présence du dossier `{nom}/`
- Vérifier la présence de `Slidedat.ini` dans le dossier
- Si absent: marquer comme **non supporté**

**Erreurs Courantes:**

❌ **INCORRECT:**
```
sample_kidney.mrxs
sample_kidney_data/          ← Mauvais nom!
```

❌ **INCORRECT:**
```
sample_kidney.mrxs
sample_kidney.mrxs/          ← Extension incluse dans le nom du dossier!
```

✅ **CORRECT:**
```
sample_kidney.mrxs
sample_kidney/               ← Nom identique sans extension
```

---

## Détection des Slides

### Processus de Détection

La détection se fait en **2 phases**:

#### Phase 1: Détection par Extension

```python
KNOWN_EXTENSIONS = {
    # Single-file formats
    '.svs', '.tif', '.tiff', '.ndpi', '.scn', '.svslide', '.bif',

    # Multi-file formats
    '.vms',  # Nécessite .vmu

    # Companion-dir formats
    '.mrxs',  # Nécessite dossier companion

    # En développement
    '.dcm', '.czi'
}
```

#### Phase 2: Validation de Structure

Pour chaque fichier détecté:

1. **Identifier le type de structure** (single/multi/companion)
2. **Vérifier les dépendances:**
   - Fichiers associés présents?
   - Dossier companion présent?
   - Contenu du dossier valide?
3. **Tester l'ouverture avec OpenSlide:**
   - Peut-on ouvrir le fichier?
   - Erreurs connues? (ex: BIF direction LEFT)
4. **Marquer le status:**
   - `is_supported: true` → Prêt à ouvrir
   - `is_supported: false` → Détecté mais non ouvrable (avec raison)

### Ajout Dynamique d'Extensions

Le système permet d'ajouter de nouvelles extensions **sans recompiler**:

```python
# Dans config ou base de données
CUSTOM_EXTENSIONS = [
    {
        "extension": ".czi",
        "format_name": "Carl Zeiss CZI",
        "structure_type": "single-file",
        "vendor": "Carl Zeiss",
        "detection_method": "openslide"
    }
]
```

**Avantages:**
- Évolutivité sans modification du code
- Configuration centralisée
- Tests progressifs de nouveaux formats

---

## Dépendances et Fichiers Associés

### Norme de Localisation

**Règle générale:** Les fichiers associés doivent être:

1. **Dans le même dossier** que le fichier principal (pour multi-file)
2. **Dans un sous-dossier** nommé comme le fichier (sans extension) pour companion-dir

### Vérification des Dépendances

```python
def verify_dependencies(entry_point: Path, structure_type: str) -> dict:
    """
    Vérifie que tous les fichiers nécessaires sont présents.

    Returns:
        {
            "is_complete": bool,
            "missing_files": [list],
            "notes": str
        }
    """
    if structure_type == "single-file":
        return {"is_complete": True, "missing_files": [], "notes": ""}

    elif structure_type == "multi-file":
        # Exemple: .vms nécessite .vmu
        base_name = entry_point.stem
        vmu_file = entry_point.parent / f"{base_name}.vmu"

        if not vmu_file.exists():
            return {
                "is_complete": False,
                "missing_files": [str(vmu_file)],
                "notes": "Missing .vmu companion file"
            }
        return {"is_complete": True, "missing_files": [], "notes": ""}

    elif structure_type == "with-companion-dir":
        # Exemple: .mrxs nécessite dossier companion
        companion_dir = entry_point.parent / entry_point.stem

        if not companion_dir.is_dir():
            return {
                "is_complete": False,
                "missing_files": [str(companion_dir)],
                "notes": f"Missing companion directory: {companion_dir.name}/"
            }

        # Vérifier Slidedat.ini pour MRXS
        slidedat = companion_dir / "Slidedat.ini"
        if not slidedat.exists():
            return {
                "is_complete": False,
                "missing_files": [str(slidedat)],
                "notes": "Missing Slidedat.ini in companion directory"
            }

        return {"is_complete": True, "missing_files": [], "notes": ""}
```

---

## Navigation dans les Dossiers

### Comportement de l'Explorateur

**Racine:** `C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides`

```
Slides/                          ← Niveau 0 (racine, non remontable)
├── 3DHistech/                   ← Niveau 1 (dossier)
│   ├── sample_a.mrxs            ← Slide détectable
│   ├── sample_a/                ← Companion (caché ou affiché comme dépendance)
│   └── sample_b.mrxs
├── ROCHE/                       ← Niveau 1 (dossier)
│   ├── Ventana-1.bif            ← Slide détectable
│   └── HE_BIF_1.bif
└── projects/                    ← Niveau 1 (dossier)
    ├── project_2024/            ← Niveau 2 (sous-dossier)
    │   └── patient_001.svs
    └── project_2025/
        └── patient_002.ndpi
```

### API de Navigation

**Endpoint:** `GET /api/browse?path={relative_path}`

**Exemples:**

1. **Lister la racine:**
   ```
   GET /api/browse?path=/

   Response:
   {
       "current_path": "/",
       "parent_path": null,  // Racine, pas de parent
       "items": [
           {"type": "folder", "name": "3DHistech", "path": "/3DHistech"},
           {"type": "folder", "name": "ROCHE", "path": "/ROCHE"},
           {"type": "folder", "name": "projects", "path": "/projects"}
       ]
   }
   ```

2. **Lister un sous-dossier:**
   ```
   GET /api/browse?path=/3DHistech

   Response:
   {
       "current_path": "/3DHistech",
       "parent_path": "/",
       "items": [
           {
               "type": "slide",
               "name": "sample_a.mrxs",
               "path": "/3DHistech/sample_a.mrxs",
               "format": "MIRAX",
               "is_supported": true,
               "structure_type": "with-companion-dir",
               "dependencies": ["/3DHistech/sample_a/"]
           },
           {
               "type": "slide",
               "name": "sample_b.mrxs",
               "path": "/3DHistech/sample_b.mrxs",
               "format": "MIRAX",
               "is_supported": false,
               "notes": "Missing companion directory: sample_b/"
           }
       ]
   }
   ```

### Sécurité

**Prévention Path Traversal:**

```python
def is_safe_path(requested_path: str, base_dir: Path) -> bool:
    """
    Empêche l'accès en dehors de la racine Slides/.

    Exemples d'attaques bloquées:
    - ../../../etc/passwd
    - /3DHistech/../../Windows/System32
    """
    resolved = (base_dir / requested_path).resolve()
    return resolved.is_relative_to(base_dir)
```

---

## Fichiers Sans Extension

### Problématique

Certains formats n'ont **pas d'extension** mais sont valides:

```
Slides/
└── legacy_data/
    ├── SLIDE_2023_001          ← Pas d'extension!
    └── SAMPLE_KIDNEY           ← Pas d'extension!
```

### Stratégie Actuelle (Phase 1)

**Status:** Détectés mais marqués **non supportés**

```json
{
    "type": "file",
    "name": "SLIDE_2023_001",
    "extension": null,
    "is_supported": false,
    "notes": "No file extension - cannot determine format"
}
```

### Stratégie Future (Phase 2+)

**Détection par Magic Bytes:**

```python
MAGIC_BYTES = {
    b'\x89PNG': 'PNG',
    b'\xff\xd8\xff': 'JPEG',
    b'II\x2a\x00': 'TIFF (little-endian)',
    b'MM\x00\x2a': 'TIFF (big-endian)',
    # DICOM
    b'\x00' * 128 + b'DICM': 'DICOM'
}

def detect_format_by_content(filepath: Path) -> Optional[str]:
    """Détecte le format par lecture des premiers octets"""
    with open(filepath, 'rb') as f:
        header = f.read(256)
        for magic, format_name in MAGIC_BYTES.items():
            if header.startswith(magic):
                return format_name
    return None
```

---

## Ajout de Nouveaux Formats

### Checklist pour Ajouter un Format

1. **Documenter le format:**
   - Extension(s)
   - Vendor/fabricant
   - Type de structure (single/multi/companion)
   - Dépendances requises

2. **Ajouter à la configuration:**
   ```python
   # backend/config/slide_formats.py
   FORMATS = {
       '.newformat': {
           'name': 'New Format Name',
           'vendor': 'Vendor Name',
           'structure_type': 'single-file',
           'openslide_support': True,
           'notes': 'Additional information'
       }
   }
   ```

3. **Implémenter la détection:**
   - Ajouter dans `format_detector.py`
   - Créer méthode `_detect_newformat()`
   - Gérer les dépendances spécifiques

4. **Tester avec fichiers réels:**
   - Ajouter échantillons dans `/Slides/test_formats/`
   - Vérifier détection, ouverture, navigation
   - Documenter erreurs dans `/docs/ERROR_*.md` si nécessaire

5. **Mettre à jour ce guide:**
   - Ajouter dans tableau "Formats Supportés"
   - Documenter règles de structure spécifiques
   - Ajouter exemples pratiques

---

## Exemples Pratiques

### Exemple 1: Organisation Recommandée

```
Slides/
├── by_vendor/
│   ├── aperio/
│   │   ├── case_001.svs
│   │   ├── case_002.svs
│   │   └── case_003.svs
│   ├── hamamatsu/
│   │   ├── slide_a.ndpi
│   │   ├── slide_b.vms
│   │   └── slide_b.vmu
│   └── 3dhistech/
│       ├── sample_1.mrxs
│       ├── sample_1/           ← Companion directory
│       │   ├── Slidedat.ini
│       │   └── Data*.dat
│       ├── sample_2.mrxs
│       └── sample_2/
│           └── ...
└── by_project/
    ├── lung_cancer_2024/
    │   ├── patient_001.svs
    │   ├── patient_002.svs
    │   └── controls/
    │       └── control_01.ndpi
    └── kidney_study_2025/
        └── ...
```

### Exemple 2: Déplacement de Lames depuis Autre Source

**Scénario:** Vous avez une lame MRXS sur `D:\Medical_Data\old_slides\`

**Structure source:**
```
D:\Medical_Data\old_slides\
├── important_case.mrxs
└── important_case/
    ├── Slidedat.ini
    └── Data*.dat
```

**Action:** Copier **LES DEUX** (fichier + dossier) vers Slides:

```
C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides\imported\
├── important_case.mrxs          ← Copier le fichier
└── important_case/              ← Copier le dossier COMPLET
    ├── Slidedat.ini
    └── Data*.dat
```

⚠️ **Ne JAMAIS copier uniquement le fichier .mrxs!** Il ne fonctionnera pas sans son dossier companion.

---

## Résumé des Règles Clés

1. ✅ **Single-file:** Un seul fichier suffit
2. ✅ **Multi-file:** Fichiers associés **dans le même dossier**, **même nom de base**
3. ✅ **Companion-dir:** Dossier nommé **exactement comme le fichier (sans extension)**
4. ✅ **Navigation:** Racine fixée à `Slides/`, pas de remontée au-delà
5. ✅ **Détection:** Par extension + validation de structure + test d'ouverture
6. ✅ **Extensions dynamiques:** Ajout sans recompilation
7. ✅ **Fichiers sans extension:** Détectés mais non supportés (pour l'instant)
8. ✅ **Sécurité:** Path traversal bloqué, accès limité à la racine

---

## Références

- **OpenSlide Formats:** https://openslide.org/formats/
- **DICOM Standard:** https://www.dicomstandard.org/
- **Error Documentation:** Voir `/docs/ERROR_*.md` pour erreurs connues
- **CLAUDE.md:** Instructions complètes pour développeurs

---

**Dernière mise à jour:** 2025-10-21
**Auteur:** VarunaPoC Development Team
**Version:** 1.0 (Phase 1.6+)
