# Système de Sélection de Readers - Architecture et Design

**Version:** 1.0
**Date:** 2026-02-04
**Statut:** Document de conception (non implémenté)
**Auteur:** Design Patterns Specialist + Algorithms Specialist

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Contexte et Problématique](#2-contexte-et-problématique)
3. [Design Patterns Recommandés](#3-design-patterns-recommandés)
4. [Structures de Données](#4-structures-de-données)
5. [Algorithme de Sélection](#5-algorithme-de-sélection)
6. [Architecture Détaillée](#6-architecture-détaillée)
7. [Interface Python](#7-interface-python)
8. [Exemple Concret](#8-exemple-concret)
9. [Gestion des Erreurs et Fallback](#9-gestion-des-erreurs-et-fallback)
10. [Analyse de Complexité](#10-analyse-de-complexité)
11. [Extensibilité et Plugins](#11-extensibilité-et-plugins)
12. [Implémentation Progressive](#12-implémentation-progressive)

---

## 1. Vue d'Ensemble

### 1.1 Objectif

Concevoir un système robuste permettant de sélectionner automatiquement le meilleur "reader" (bibliothèque de lecture) pour ouvrir une lame histologique, en fonction de:
- **Format détecté** (MRXS, BIF, DICOM, etc.)
- **Capacités du reader** (score de compatibilité)
- **Fallback automatique** si le meilleur reader échoue
- **Extensibilité** via plugins

### 1.2 Principe KISS (Keep It Simple, Stupid)

Le système doit être:
- Simple à comprendre (lisible en 5 minutes)
- Simple à étendre (ajouter un reader = 3 lignes de code)
- Simple à déboguer (logs clairs à chaque étape)
- Performant (O(n) où n = nombre de readers, typiquement 5-10)

### 1.3 Schéma Conceptuel

```
┌────────────────────────────────────────────────────────────────┐
│                      Slide File (.mrxs, .bif, .dcm, etc.)      │
└────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Format Detector       │
                        │   (détecte format)      │
                        └──────────┬──────────────┘
                                   │ format = "MRXS"
                                   ▼
                        ┌─────────────────────────┐
                        │  Reader Selector        │
                        │  (sélectionne reader)   │
                        └──────────┬──────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      │                            │                            │
      ▼                            ▼                            ▼
┌──────────┐              ┌──────────────┐            ┌──────────────┐
│OpenSlide │ Score: 100   │ Bio-Formats  │ Score: 80  │   libvips    │ Score: 60
│  Reader  │              │    Reader    │            │   Reader     │
└────┬─────┘              └──────────────┘            └──────────────┘
     │
     │ Try open()
     ▼
┌─────────────┐
│  SUCCESS    │  Return OpenSlideReader instance
└─────────────┘

┌─────────────┐
│  FAILURE    │  Fallback to Bio-Formats (score 80)
└─────────────┘
```

---

## 2. Contexte et Problématique

### 2.1 Situation Actuelle

VarunaPoC utilise **uniquement OpenSlide** pour lire toutes les lames. Cela fonctionne bien pour la majorité des formats, mais présente des limitations:

**Limitations OpenSlide:**
- ❌ Zeiss CZI (JPEG XR compression non supportée)
- ❌ Olympus VSI (format propriétaire non supporté)
- ⚠️ DICOM (problème concatenations - Issue #511)
- ⚠️ Ventana BIF (nécessite patch pour direction LEFT)

**Fichiers de test actuels:**
```
Slides/
├── OPENSLIDE-testdata/
│   ├── Aperio/          ✅ OpenSlide excellent
│   ├── Hamamatsu/       ✅ OpenSlide excellent
│   ├── Leica/           ⚠️ OpenSlide partiel (DICOM concatenations)
│   ├── Zeiss/           ⚠️ OpenSlide partiel (CZI JPEG XR)
│   └── Olympus/         ❌ OpenSlide ne supporte pas VSI
```

### 2.2 Problématique

Comment choisir automatiquement le meilleur reader parmi plusieurs options?

**Contraintes:**
1. **Performance:** Sélection rapide (< 10ms)
2. **Robustesse:** Fallback si le meilleur échoue
3. **Extensibilité:** Nouveaux readers ajoutables sans modifier le core
4. **Simplicité:** Code maintenable par toute l'équipe

**Questions de design:**
- Comment scorer la compatibilité d'un reader avec un format?
- Comment gérer les cas où plusieurs readers peuvent lire le même format?
- Comment implémenter le fallback de manière élégante?
- Comment permettre aux plugins d'enregistrer leurs readers?

---

## 3. Design Patterns Recommandés

### 3.1 Strategy Pattern (Stratégie)

**Pourquoi:** Encapsuler chaque reader dans une stratégie interchangeable.

**Avantages:**
- ✅ Chaque reader est isolé (Single Responsibility Principle)
- ✅ Facile d'ajouter/retirer des readers
- ✅ Testable indépendamment

**Exemple conceptuel:**
```
ReaderStrategy (interface)
├── OpenSlideReader (implémentation)
├── BioFormatsReader (implémentation)
├── LibvipsReader (implémentation)
└── DicomReader (implémentation)
```

### 3.2 Chain of Responsibility (Chaîne de responsabilité)

**Pourquoi:** Implémenter le fallback automatique.

**Avantages:**
- ✅ Chaque reader tente l'ouverture dans l'ordre de priorité
- ✅ Si échec, passe au suivant automatiquement
- ✅ Pas de code conditionnel complexe (if/else imbriqués)

**Exemple conceptuel:**
```
Request: Open slide "example.mrxs"
│
├─► OpenSlideReader (priority 1)
│   └─► try_open() → Success → STOP
│
├─► BioFormatsReader (priority 2)
│   └─► try_open() → Fail → Continue
│
└─► LibvipsReader (priority 3)
    └─► try_open() → Fail → Raise Error
```

### 3.3 Registry Pattern (Registre)

**Pourquoi:** Permettre aux plugins d'enregistrer leurs readers dynamiquement.

**Avantages:**
- ✅ Découplage total (plugins ne connaissent pas le core)
- ✅ Chargement dynamique des readers
- ✅ Pas de modification du code core pour ajouter un reader

**Exemple conceptuel:**
```python
# Core system
reader_registry = ReaderRegistry()

# Plugin A
reader_registry.register(MyCustomReader, priority=80)

# Plugin B
reader_registry.register(AnotherReader, priority=60)

# Utilisation
best_reader = reader_registry.get_best_reader(format="MRXS")
```

### 3.4 Factory Pattern (Fabrique) - Optionnel

**Pourquoi:** Créer des instances de readers de manière contrôlée.

**Quand l'utiliser:**
- Si les readers nécessitent configuration complexe
- Si on veut pool/cache des instances

**Pour Phase 1:** Pas nécessaire (KISS). Les readers peuvent être instanciés directement.

---

## 4. Structures de Données

### 4.1 ReaderCapability (Capacité d'un Reader)

Représente la capacité d'un reader à lire un format spécifique.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ReaderCapability:
    """
    Capacité d'un reader pour un format donné.

    Attributes:
        format: Format de slide (ex: "MRXS", "BIF", "DICOM")
        score: Score de compatibilité (0-100)
                100 = Support parfait
                80  = Support bon avec limitations mineures
                60  = Support partiel avec limitations majeures
                0   = Non supporté
        notes: Explications sur le score (limitations, patches requis, etc.)

    Examples:
        >>> OpenSlideReader capability for MRXS:
        ReaderCapability(
            format="MRXS",
            score=100,
            notes="Support natif excellent"
        )

        >>> OpenSlideReader capability for CZI:
        ReaderCapability(
            format="CZI",
            score=60,
            notes="JPEG XR compression non supportée"
        )
    """
    format: str
    score: int  # 0-100
    notes: Optional[str] = None

    def __post_init__(self):
        if not 0 <= self.score <= 100:
            raise ValueError(f"Score must be 0-100, got {self.score}")
```

**Rationale du score:**
- **100:** Reader de référence pour ce format (ex: OpenSlide pour MRXS)
- **80:** Bon support avec limitations documentées (ex: OpenSlide pour CZI sans JPEG XR)
- **60:** Support partiel, risque d'échec sur certains fichiers
- **40:** Expérimental, non testé en production
- **0:** Non supporté

### 4.2 ReaderMetadata (Métadonnées d'un Reader)

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ReaderMetadata:
    """
    Métadonnées d'un reader.

    Attributes:
        name: Nom unique du reader (ex: "openslide", "bioformats")
        version: Version de la bibliothèque (ex: "4.0.0")
        capabilities: Dictionnaire {format: ReaderCapability}
        priority: Priorité globale si scores égaux (0-100, plus élevé = prioritaire)

    Examples:
        >>> OpenSlideReader metadata:
        ReaderMetadata(
            name="openslide",
            version="4.0.0",
            capabilities={
                "MRXS": ReaderCapability("MRXS", 100, "Support natif"),
                "BIF": ReaderCapability("BIF", 100, "Avec patch LEFT"),
                "CZI": ReaderCapability("CZI", 60, "Pas JPEG XR"),
                "VSI": ReaderCapability("VSI", 0, "Non supporté")
            },
            priority=90
        )
    """
    name: str
    version: str
    capabilities: Dict[str, ReaderCapability]
    priority: int = 50  # Priorité par défaut si scores égaux

    def get_score(self, format: str) -> int:
        """Retourne le score pour un format donné (0 si non supporté)."""
        cap = self.capabilities.get(format)
        return cap.score if cap else 0
```

### 4.3 ReaderRegistry (Registre des Readers)

```python
from typing import List, Optional, Tuple

class ReaderRegistry:
    """
    Registre centralisé des readers disponibles.

    Structure interne:
        _readers: List[Tuple[ReaderClass, ReaderMetadata]]
                  Trié par priorité décroissante

    Performance:
        - register(): O(n log n) où n = nombre de readers (rare, fait au startup)
        - get_ranked_readers(): O(n) où n = nombre de readers (~5-10)
        - get_best_reader(): O(1) si un seul reader à score max, sinon O(n)
    """

    def __init__(self):
        self._readers: List[Tuple[type, ReaderMetadata]] = []

    def register(self, reader_class: type, metadata: ReaderMetadata) -> None:
        """
        Enregistre un reader dans le registre.

        Args:
            reader_class: Classe du reader (doit implémenter ReaderInterface)
            metadata: Métadonnées du reader

        Technical Notes:
            - Vérifie que reader_class implémente ReaderInterface
            - Trie la liste par priorité après insertion
            - Permet de réenregistrer (mise à jour)
        """
        # Validation
        if not issubclass(reader_class, ReaderInterface):
            raise TypeError(f"{reader_class} must implement ReaderInterface")

        # Retirer si déjà enregistré (permet mise à jour)
        self._readers = [
            (cls, meta) for cls, meta in self._readers
            if meta.name != metadata.name
        ]

        # Ajouter
        self._readers.append((reader_class, metadata))

        # Trier par priorité décroissante (priorité globale, pas score format)
        self._readers.sort(key=lambda x: x[1].priority, reverse=True)

    def get_ranked_readers(self, format: str) -> List[Tuple[type, ReaderMetadata, int]]:
        """
        Retourne tous les readers capables de lire le format, triés par score.

        Args:
            format: Format de slide (ex: "MRXS")

        Returns:
            List[(reader_class, metadata, score)] triée par score décroissant

        Examples:
            >>> registry.get_ranked_readers("MRXS")
            [
                (OpenSlideReader, metadata, 100),
                (BioFormatsReader, metadata, 80),
                (LibvipsReader, metadata, 60)
            ]
        """
        ranked = []
        for reader_class, metadata in self._readers:
            score = metadata.get_score(format)
            if score > 0:  # Ignorer les readers qui ne supportent pas le format
                ranked.append((reader_class, metadata, score))

        # Trier par score décroissant, puis par priorité si égalité
        ranked.sort(key=lambda x: (x[2], x[1].priority), reverse=True)
        return ranked

    def get_best_reader(self, format: str) -> Optional[Tuple[type, ReaderMetadata]]:
        """
        Retourne le meilleur reader pour un format donné.

        Returns:
            (reader_class, metadata) ou None si aucun reader disponible
        """
        ranked = self.get_ranked_readers(format)
        return (ranked[0][0], ranked[0][1]) if ranked else None
```

---

## 5. Algorithme de Sélection

### 5.1 Pseudo-code Simplifié

```
FUNCTION select_reader(file_path):
    # Étape 1: Détection du format
    format = detect_format(file_path)

    # Étape 2: Récupérer readers classés par score
    ranked_readers = registry.get_ranked_readers(format)

    IF ranked_readers est vide:
        RAISE UnsupportedFormatError(format)

    # Étape 3: Fallback chain - essayer chaque reader dans l'ordre
    FOR (reader_class, metadata, score) IN ranked_readers:
        LOG "Trying {metadata.name} (score={score})"

        TRY:
            reader_instance = reader_class(file_path)
            reader_instance.open()
            LOG "SUCCESS with {metadata.name}"
            RETURN reader_instance

        EXCEPT ReaderError as e:
            LOG "FAILED with {metadata.name}: {e}"
            CONTINUE  # Essayer le suivant

    # Étape 4: Tous les readers ont échoué
    RAISE NoCompatibleReaderError(format, file_path)
```

### 5.2 Diagramme de Flux

```
                    START
                      │
                      ▼
            ┌─────────────────┐
            │ Detect Format   │
            │ format="MRXS"   │
            └────────┬────────┘
                     │
                     ▼
       ┌─────────────────────────┐
       │ Get Ranked Readers      │
       │ [(OpenSlide,100),       │
       │  (BioFormats,80),       │
       │  (Libvips,60)]          │
       └────────┬────────────────┘
                │
                ▼
         ┌──────────────┐
         │ Readers list │
         │ empty?       │
         └──┬────────┬──┘
            │ YES    │ NO
            │        │
            ▼        ▼
      ┌─────────┐  ┌──────────────────┐
      │ RAISE   │  │ FOR each reader  │◄──────┐
      │ Unsup-  │  │ in order         │       │
      │ ported  │  └─────────┬────────┘       │
      └─────────┘            │                 │
                             ▼                 │
                   ┌──────────────────┐        │
                   │ Try open() with  │        │
                   │ current reader   │        │
                   └────────┬─────────┘        │
                            │                  │
                   ┌────────┴────────┐         │
                   │                 │         │
                SUCCESS          FAILURE       │
                   │                 │         │
                   ▼                 │         │
            ┌──────────┐             │         │
            │ RETURN   │             │         │
            │ reader   │             └─────────┘ Continue to next
            └──────────┘

            If all fail:
            ┌──────────┐
            │ RAISE    │
            │ NoCompat-│
            │ ibleRead-│
            │ er       │
            └──────────┘
```

### 5.3 Algorithme Détaillé (Python-like pseudocode)

```python
def select_and_open_reader(file_path: str) -> ReaderInterface:
    """
    Sélectionne et ouvre le meilleur reader pour un fichier.

    Algorithm:
        1. Detect format (via magic bytes, extension, metadata)
        2. Get ranked readers from registry
        3. Try each reader in order until success
        4. Raise error if all fail

    Complexity:
        - Temps: O(n*m) où n=nombre readers, m=coût d'ouverture (dominé par I/O)
        - Espace: O(n) pour stocker ranked readers

    Args:
        file_path: Chemin vers la lame

    Returns:
        ReaderInterface instance (opened and ready)

    Raises:
        UnsupportedFormatError: Format non reconnu
        NoCompatibleReaderError: Aucun reader n'a pu ouvrir le fichier
    """

    # Étape 1: Détection format
    logger.info(f"Detecting format for {file_path}")
    format_info = format_detector.detect(file_path)
    format_name = format_info.format  # Ex: "MRXS", "BIF", "DICOM"

    logger.info(f"Detected format: {format_name}")

    # Étape 2: Récupérer readers classés
    ranked_readers = reader_registry.get_ranked_readers(format_name)

    if not ranked_readers:
        raise UnsupportedFormatError(
            f"No reader available for format '{format_name}'"
        )

    logger.info(
        f"Found {len(ranked_readers)} compatible readers: "
        f"{[meta.name for _, meta, _ in ranked_readers]}"
    )

    # Étape 3: Fallback chain
    errors = []  # Accumuler les erreurs pour diagnostic

    for i, (reader_class, metadata, score) in enumerate(ranked_readers):
        logger.info(
            f"[{i+1}/{len(ranked_readers)}] Trying {metadata.name} "
            f"(score={score}, version={metadata.version})"
        )

        try:
            # Instancier reader
            reader = reader_class()

            # Ouvrir fichier
            reader.open(file_path)

            # Vérifier validité (certains readers peuvent ouvrir sans erreur
            # mais ne pas lire correctement le format)
            if not reader.is_valid():
                raise ReaderValidationError("Reader opened file but failed validation")

            # Succès
            logger.info(
                f"SUCCESS: Opened with {metadata.name} "
                f"(dimensions={reader.dimensions})"
            )

            return reader

        except Exception as e:
            # Logger l'échec
            logger.warning(
                f"FAILED with {metadata.name}: {type(e).__name__}: {e}"
            )

            # Accumuler pour rapport d'erreur final
            errors.append({
                "reader": metadata.name,
                "score": score,
                "error": str(e),
                "error_type": type(e).__name__
            })

            # Continuer avec le reader suivant
            continue

    # Étape 4: Tous ont échoué - rapport détaillé
    error_report = "\n".join([
        f"  - {err['reader']} (score={err['score']}): "
        f"{err['error_type']}: {err['error']}"
        for err in errors
    ])

    raise NoCompatibleReaderError(
        f"No reader could open {file_path} (format={format_name}).\n"
        f"Attempted {len(errors)} readers:\n{error_report}"
    )
```

---

## 6. Architecture Détaillée

### 6.1 Diagramme de Classes UML

```
┌─────────────────────────────────────────────────────────────┐
│                    <<interface>>                            │
│                   ReaderInterface                           │
├─────────────────────────────────────────────────────────────┤
│ + open(path: str) -> None                                   │
│ + close() -> None                                           │
│ + is_valid() -> bool                                        │
│ + get_metadata() -> SlideMetadata                           │
│ + read_region(x, y, level, w, h) -> Image                   │
│ + get_thumbnail(max_size) -> Image                          │
├─────────────────────────────────────────────────────────────┤
│ <<properties>>                                              │
│ + dimensions: Tuple[int, int]                               │
│ + level_count: int                                          │
│ + level_dimensions: List[Tuple[int, int]]                   │
└─────────────────────────────────────────────────────────────┘
                        ▲
                        │ implements
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
┌───────┴──────┐ ┌──────┴──────┐ ┌─────┴─────┐ ┌─────┴──────┐
│ OpenSlide    │ │ BioFormats  │ │  Libvips  │ │   DICOM    │
│   Reader     │ │   Reader    │ │  Reader   │ │   Reader   │
├──────────────┤ ├─────────────┤ ├───────────┤ ├────────────┤
│ - _slide     │ │ - _bf_img   │ │ - _vips   │ │ - _dicom   │
│ - _metadata  │ │ - _metadata │ │ - _meta   │ │ - _dataset │
└──────────────┘ └─────────────┘ └───────────┘ └────────────┘


┌─────────────────────────────────────────────────────────────┐
│                   ReaderRegistry                            │
├─────────────────────────────────────────────────────────────┤
│ - _readers: List[Tuple[type, ReaderMetadata]]              │
├─────────────────────────────────────────────────────────────┤
│ + register(cls, metadata) -> None                           │
│ + get_ranked_readers(format) -> List[...]                   │
│ + get_best_reader(format) -> Optional[Tuple[...]]           │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ uses
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  ReaderMetadata                             │
├─────────────────────────────────────────────────────────────┤
│ + name: str                                                 │
│ + version: str                                              │
│ + capabilities: Dict[str, ReaderCapability]                 │
│ + priority: int                                             │
├─────────────────────────────────────────────────────────────┤
│ + get_score(format: str) -> int                             │
└─────────────────────────────────────────────────────────────┘
                        │ contains
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  ReaderCapability                           │
├─────────────────────────────────────────────────────────────┤
│ + format: str                                               │
│ + score: int (0-100)                                        │
│ + notes: Optional[str]                                      │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                   ReaderSelector                            │
├─────────────────────────────────────────────────────────────┤
│ - _registry: ReaderRegistry                                 │
│ - _format_detector: FormatDetector                          │
├─────────────────────────────────────────────────────────────┤
│ + select_and_open(path) -> ReaderInterface                  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Diagramme de Séquence

```
User          ReaderSelector    Registry    FormatDetector   OpenSlideReader   BioFormatsReader
 │                  │               │              │                │                 │
 │ open("x.mrxs")   │               │              │                │                 │
 ├─────────────────>│               │              │                │                 │
 │                  │ detect(path)  │              │                │                 │
 │                  ├──────────────────────────────>│                │                 │
 │                  │               │              │                │                 │
 │                  │<──────────────────────────────┤                │                 │
 │                  │ format="MRXS" │              │                │                 │
 │                  │               │              │                │                 │
 │                  │ get_ranked_readers("MRXS")   │                │                 │
 │                  ├──────────────>│              │                │                 │
 │                  │               │              │                │                 │
 │                  │<──────────────┤              │                │                 │
 │                  │ [(OpenSlide,100), (BioFormats,80)]            │                 │
 │                  │               │              │                │                 │
 │                  │ new()         │              │                │                 │
 │                  ├──────────────────────────────────────────────>│                 │
 │                  │               │              │                │                 │
 │                  │ open(path)    │              │                │                 │
 │                  ├──────────────────────────────────────────────>│                 │
 │                  │               │              │                │                 │
 │                  │<──────────────────────────────────────────────┤                 │
 │                  │ reader (success)             │                │                 │
 │                  │               │              │                │                 │
 │<─────────────────┤               │              │                │                 │
 │ reader instance  │               │              │                │                 │
 │                  │               │              │                │                 │

┌──────────────────────────────────────────────────────────────────────────────────┐
│ Cas d'échec (fallback):                                                          │
│                                                                                  │
│ ReaderSelector                                                                   │
│      │                                                                           │
│      │ Try OpenSlide.open() → FAIL (OpenSlideError)                             │
│      │ Log: "FAILED with openslide: Cannot read file"                           │
│      │                                                                           │
│      │ Try BioFormats.open() → SUCCESS                                          │
│      │ Log: "SUCCESS with bioformats"                                           │
│      │                                                                           │
│      └──> Return BioFormatsReader instance                                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Interface Python

### 7.1 ReaderInterface (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
from PIL import Image
from dataclasses import dataclass

@dataclass
class SlideMetadata:
    """Métadonnées standard d'une lame."""
    vendor: str
    format: str
    dimensions: Tuple[int, int]  # Level 0
    level_count: int
    level_dimensions: List[Tuple[int, int]]
    level_downsamples: List[float]
    properties: dict  # Propriétés spécifiques au reader


class ReaderInterface(ABC):
    """
    Interface abstraite pour tous les readers de lames.

    Contrat:
        - open() doit être appelé avant toute autre opération
        - close() doit être appelé pour libérer les ressources
        - Utilisation recommandée: context manager (with statement)

    Examples:
        >>> with OpenSlideReader() as reader:
        ...     reader.open("slide.mrxs")
        ...     thumbnail = reader.get_thumbnail(512)
    """

    @abstractmethod
    def open(self, path: str) -> None:
        """
        Ouvre une lame.

        Args:
            path: Chemin vers le fichier de lame

        Raises:
            ReaderError: Si le fichier ne peut pas être ouvert
            FileNotFoundError: Si le fichier n'existe pas
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Ferme la lame et libère les ressources."""
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """
        Vérifie que la lame est correctement ouverte et lisible.

        Returns:
            True si la lame est valide et lisible

        Technical Notes:
            Vérifie que:
            - Le fichier est bien ouvert
            - Les métadonnées sont cohérentes
            - Au moins une région peut être lue
        """
        pass

    @abstractmethod
    def get_metadata(self) -> SlideMetadata:
        """
        Retourne métadonnées de la lame.

        Returns:
            SlideMetadata avec vendor, format, dimensions, etc.
        """
        pass

    @abstractmethod
    def read_region(
        self,
        x: int,
        y: int,
        level: int,
        width: int,
        height: int
    ) -> Image:
        """
        Extrait une région de la lame.

        Args:
            x, y: Coordonnées (niveau 0, top-left)
            level: Niveau pyramidal (0 = pleine résolution)
            width, height: Dimensions de la région à extraire

        Returns:
            PIL.Image RGB

        Technical Notes:
            - Coordonnées toujours exprimées en niveau 0
            - Retour toujours RGB (pas RGBA)
        """
        pass

    @abstractmethod
    def get_thumbnail(self, max_size: int = 1024) -> Image:
        """
        Retourne miniature de la lame.

        Args:
            max_size: Dimension maximale (width ou height)

        Returns:
            PIL.Image RGB redimensionnée (aspect ratio préservé)
        """
        pass

    # Properties (to be implemented as @property in subclasses)
    @property
    @abstractmethod
    def dimensions(self) -> Tuple[int, int]:
        """Dimensions niveau 0 (width, height)."""
        pass

    @property
    @abstractmethod
    def level_count(self) -> int:
        """Nombre de niveaux pyramidaux."""
        pass

    @property
    @abstractmethod
    def level_dimensions(self) -> List[Tuple[int, int]]:
        """Dimensions de chaque niveau pyramidal."""
        pass

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### 7.2 Exceptions Hiérarchie

```python
class ReaderError(Exception):
    """Erreur de base pour tous les readers."""
    pass


class UnsupportedFormatError(ReaderError):
    """Format de lame non supporté par aucun reader."""
    pass


class NoCompatibleReaderError(ReaderError):
    """Aucun reader n'a pu ouvrir le fichier."""
    pass


class ReaderValidationError(ReaderError):
    """Reader a ouvert le fichier mais validation a échoué."""
    pass
```

### 7.3 ReaderSelector (Classe Principale)

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ReaderSelector:
    """
    Sélectionne automatiquement le meilleur reader pour une lame.

    Usage:
        >>> selector = ReaderSelector(registry, format_detector)
        >>> reader = selector.select_and_open("slide.mrxs")
        >>> thumbnail = reader.get_thumbnail(512)
        >>> reader.close()
    """

    def __init__(
        self,
        registry: ReaderRegistry,
        format_detector: FormatDetector
    ):
        """
        Args:
            registry: Registre des readers disponibles
            format_detector: Détecteur de formats
        """
        self._registry = registry
        self._format_detector = format_detector

    def select_and_open(self, path: str) -> ReaderInterface:
        """
        Sélectionne et ouvre le meilleur reader pour un fichier.

        Voir pseudo-code section 5.3 pour détails algorithme.

        Args:
            path: Chemin vers la lame

        Returns:
            ReaderInterface instance (opened and validated)

        Raises:
            UnsupportedFormatError: Format non reconnu
            NoCompatibleReaderError: Aucun reader compatible
            FileNotFoundError: Fichier inexistant
        """
        # Implementation matching pseudo-code in section 5.3
        # (voir pseudo-code détaillé plus haut)
        pass
```

---

## 8. Exemple Concret

### 8.1 Implémentation OpenSlideReader

```python
import openslide
from openslide import OpenSlideError
from typing import Tuple, List
from PIL import Image


class OpenSlideReader(ReaderInterface):
    """
    Reader basé sur OpenSlide.

    Technical Notes:
        - Wrapper autour de openslide-python
        - Gère automatiquement fichiers compagnons (.mrxs)
        - Retourne toujours RGB (convertit RGBA)
    """

    def __init__(self):
        self._slide: Optional[openslide.OpenSlide] = None
        self._path: Optional[str] = None

    def open(self, path: str) -> None:
        """Ouvre lame avec OpenSlide."""
        try:
            self._slide = openslide.OpenSlide(path)
            self._path = path
        except OpenSlideError as e:
            raise ReaderError(f"OpenSlide cannot open file: {e}")

    def close(self) -> None:
        """Ferme lame."""
        if self._slide:
            self._slide.close()
            self._slide = None

    def is_valid(self) -> bool:
        """Vérifie validité."""
        if not self._slide:
            return False

        try:
            # Vérifie qu'on peut lire métadonnées
            _ = self._slide.dimensions
            _ = self._slide.level_count

            # Vérifie qu'on peut lire au moins 1 pixel
            _ = self._slide.read_region((0, 0), 0, (1, 1))

            return True
        except:
            return False

    def get_metadata(self) -> SlideMetadata:
        """Extrait métadonnées."""
        if not self._slide:
            raise ReaderError("Slide not opened")

        return SlideMetadata(
            vendor=self._slide.properties.get(
                openslide.PROPERTY_NAME_VENDOR, "Unknown"
            ),
            format=self._detect_format(),
            dimensions=self._slide.dimensions,
            level_count=self._slide.level_count,
            level_dimensions=list(self._slide.level_dimensions),
            level_downsamples=list(self._slide.level_downsamples),
            properties=dict(self._slide.properties)
        )

    def read_region(
        self,
        x: int,
        y: int,
        level: int,
        width: int,
        height: int
    ) -> Image:
        """Extrait région."""
        if not self._slide:
            raise ReaderError("Slide not opened")

        # OpenSlide retourne RGBA, convertir en RGB
        region = self._slide.read_region((x, y), level, (width, height))
        return region.convert('RGB')

    def get_thumbnail(self, max_size: int = 1024) -> Image:
        """Retourne thumbnail."""
        if not self._slide:
            raise ReaderError("Slide not opened")

        return self._slide.get_thumbnail((max_size, max_size))

    @property
    def dimensions(self) -> Tuple[int, int]:
        return self._slide.dimensions if self._slide else (0, 0)

    @property
    def level_count(self) -> int:
        return self._slide.level_count if self._slide else 0

    @property
    def level_dimensions(self) -> List[Tuple[int, int]]:
        return list(self._slide.level_dimensions) if self._slide else []

    def _detect_format(self) -> str:
        """Détecte format depuis vendor."""
        vendor = self._slide.properties.get(
            openslide.PROPERTY_NAME_VENDOR, ""
        )

        if "3DHISTECH" in vendor.upper():
            return "MRXS"
        elif "Ventana" in vendor or "Roche" in vendor:
            return "BIF"
        elif "Aperio" in vendor:
            return "SVS"
        else:
            return f"Unknown ({vendor})"


# Métadonnées OpenSlideReader
OPENSLIDE_METADATA = ReaderMetadata(
    name="openslide",
    version="4.0.0",
    capabilities={
        "MRXS": ReaderCapability(
            format="MRXS",
            score=100,
            notes="Support natif excellent"
        ),
        "BIF": ReaderCapability(
            format="BIF",
            score=100,
            notes="Avec patch direction LEFT"
        ),
        "SVS": ReaderCapability(
            format="SVS",
            score=100,
            notes="Support natif excellent (Aperio)"
        ),
        "NDPI": ReaderCapability(
            format="NDPI",
            score=100,
            notes="Support natif excellent (Hamamatsu)"
        ),
        "DICOM": ReaderCapability(
            format="DICOM",
            score=80,
            notes="Limitation: concatenations non supportées (Issue #511)"
        ),
        "CZI": ReaderCapability(
            format="CZI",
            score=60,
            notes="JPEG XR compression non supportée"
        ),
        "VSI": ReaderCapability(
            format="VSI",
            score=0,
            notes="Format non supporté (Olympus)"
        )
    },
    priority=90  # Priorité élevée (reader de référence)
)
```

### 8.2 Implémentation BioFormatsReader (Skeleton)

```python
class BioFormatsReader(ReaderInterface):
    """
    Reader basé sur Bio-Formats (via python-bioformats ou jpype).

    Technical Notes:
        - Nécessite Java Runtime Environment (JRE)
        - Support quasi-universel (>150 formats)
        - Plus lent que readers natifs
    """

    def __init__(self):
        self._reader = None
        self._metadata = None

    def open(self, path: str) -> None:
        """Ouvre avec Bio-Formats."""
        try:
            # Code simplifié - nécessite python-bioformats
            import bioformats
            self._reader = bioformats.ImageReader(path)
            self._metadata = bioformats.get_omexml_metadata(path)
        except Exception as e:
            raise ReaderError(f"Bio-Formats cannot open file: {e}")

    # ... autres méthodes (même signature que ReaderInterface)


# Métadonnées BioFormatsReader
BIOFORMATS_METADATA = ReaderMetadata(
    name="bioformats",
    version="6.14.0",
    capabilities={
        "MRXS": ReaderCapability("MRXS", 80, "Support bon mais plus lent"),
        "BIF": ReaderCapability("BIF", 80, "Support bon"),
        "CZI": ReaderCapability("CZI", 100, "Support excellent (JPEG XR OK)"),
        "VSI": ReaderCapability("VSI", 100, "Support excellent (Olympus)"),
        "DICOM": ReaderCapability("DICOM", 90, "Support excellent"),
        # ... autres formats
    },
    priority=70  # Priorité moyenne (fallback)
)
```

### 8.3 Setup et Utilisation

```python
# Configuration initiale (au démarrage de l'application)
def setup_readers():
    """Initialise le système de readers."""

    # Créer registre
    registry = ReaderRegistry()

    # Enregistrer OpenSlide
    registry.register(OpenSlideReader, OPENSLIDE_METADATA)

    # Enregistrer Bio-Formats (si disponible)
    try:
        import bioformats
        registry.register(BioFormatsReader, BIOFORMATS_METADATA)
    except ImportError:
        logger.warning("Bio-Formats not available, skipping")

    # Enregistrer autres readers (libvips, etc.)
    # ...

    return registry


# Utilisation
def open_slide(path: str) -> ReaderInterface:
    """
    Ouvre une lame avec le meilleur reader disponible.

    Examples:
        >>> reader = open_slide("slide.mrxs")
        >>> print(reader.dimensions)
        (120000, 80000)
        >>> thumbnail = reader.get_thumbnail(512)
        >>> reader.close()
    """
    registry = setup_readers()
    format_detector = FormatDetector()
    selector = ReaderSelector(registry, format_detector)

    return selector.select_and_open(path)


# Exemple avec context manager
def process_slide(path: str):
    """Traite une lame avec gestion automatique des ressources."""

    selector = ReaderSelector(setup_readers(), FormatDetector())

    with selector.select_and_open(path) as reader:
        # Reader automatiquement fermé à la fin du bloc
        metadata = reader.get_metadata()
        print(f"Vendor: {metadata.vendor}")
        print(f"Format: {metadata.format}")
        print(f"Dimensions: {metadata.dimensions}")

        thumbnail = reader.get_thumbnail(1024)
        thumbnail.save("overview.jpg")
```

---

## 9. Gestion des Erreurs et Fallback

### 9.1 Stratégie de Fallback

**Principe:** Chaque reader dans la chaîne tente d'ouvrir le fichier. Si échec, passe au suivant automatiquement.

**Logging détaillé:**
```
INFO: Detecting format for /Slides/example.czi
INFO: Detected format: CZI
INFO: Found 3 compatible readers: ['openslide', 'bioformats', 'libvips']
INFO: [1/3] Trying openslide (score=60, version=4.0.0)
WARNING: FAILED with openslide: OpenSlideError: Cannot decode JPEG XR
INFO: [2/3] Trying bioformats (score=100, version=6.14.0)
INFO: SUCCESS: Opened with bioformats (dimensions=(120000, 80000))
```

### 9.2 Cas d'Erreur Possibles

| Erreur | Cause | Fallback | Log |
|--------|-------|----------|-----|
| **FileNotFoundError** | Fichier inexistant | STOP (pas de fallback) | ERROR |
| **UnsupportedFormatError** | Format inconnu | STOP | ERROR |
| **OpenSlideError** | OpenSlide ne peut pas lire | CONTINUE (essayer BioFormats) | WARNING |
| **BioFormatsError** | Bio-Formats échec | CONTINUE (essayer suivant) | WARNING |
| **ReaderValidationError** | Fichier ouvert mais invalide | CONTINUE | WARNING |
| **NoCompatibleReaderError** | Tous ont échoué | STOP | ERROR |

### 9.3 Gestion des Ressources

**Problème:** Si un reader échoue après avoir ouvert le fichier, il faut fermer proprement.

**Solution:**
```python
def select_and_open(self, path: str) -> ReaderInterface:
    """Gestion sécurisée des ressources."""

    for reader_class, metadata, score in ranked_readers:
        reader = None
        try:
            reader = reader_class()
            reader.open(path)

            if not reader.is_valid():
                raise ReaderValidationError("Validation failed")

            return reader  # Succès - reader reste ouvert

        except Exception as e:
            # Fermer reader si ouvert
            if reader:
                try:
                    reader.close()
                except:
                    pass  # Ignorer erreurs de fermeture

            # Logger et continuer
            logger.warning(f"FAILED with {metadata.name}: {e}")
            continue

    # Tous ont échoué
    raise NoCompatibleReaderError(...)
```

### 9.4 Timeout et Ressources

**Problème:** Certains readers peuvent bloquer longtemps (ex: Bio-Formats avec fichiers corrompus).

**Solution Phase 2:**
```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """Context manager avec timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation exceeded {seconds}s")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


# Utilisation
try:
    with timeout(30):  # 30 secondes max
        reader.open(path)
except TimeoutError:
    logger.warning(f"Reader {metadata.name} timed out")
    continue  # Fallback au suivant
```

---

## 10. Analyse de Complexité

### 10.1 Complexité Temporelle

**Notation:**
- `n` = nombre de readers (typiquement 3-10)
- `m` = coût d'ouverture d'un fichier (dominé par I/O, ~100ms-1s)
- `k` = nombre de formats (typiquement 10-20)

**Opérations:**

| Opération | Complexité | Justification |
|-----------|------------|---------------|
| `register()` | O(n log n) | Tri après insertion (rare, au startup) |
| `get_ranked_readers()` | O(n) | Parcours de tous les readers + tri |
| `select_and_open()` (best case) | O(n + m) | Tri + 1 ouverture réussie |
| `select_and_open()` (worst case) | O(n*m) | Tous les readers échouent |
| `select_and_open()` (average) | O(n + m) | Premier reader fonctionne généralement |

**Optimisations possibles:**
- **Cache format → readers:** Si format détecté plusieurs fois, éviter re-tri
- **Memoization:** Cache résultat get_ranked_readers() par format
- **Early stop:** Si score=100 et reader fonctionne, skip validation approfondie

### 10.2 Complexité Spatiale

| Structure | Espace | Justification |
|-----------|--------|---------------|
| `ReaderRegistry._readers` | O(n) | Liste des readers |
| `ReaderMetadata.capabilities` | O(k) | Dictionnaire format→capability |
| `get_ranked_readers()` | O(n) | Liste temporaire triée |
| **Total** | **O(n*k)** | n readers × k formats chacun |

**Avec valeurs réelles:**
- n = 5 readers
- k = 15 formats
- Espace = 5 × 15 = 75 entrées × ~100 bytes/entrée = **7.5 KB** (négligeable)

### 10.3 Optimisation: Cache Format→Readers

**Problème:** Si on ouvre plusieurs lames du même format, on re-trie à chaque fois.

**Solution:**
```python
class ReaderRegistry:
    def __init__(self):
        self._readers = []
        self._cache = {}  # format → ranked_readers

    def get_ranked_readers(self, format: str):
        # Check cache
        if format in self._cache:
            return self._cache[format]

        # Compute
        ranked = self._compute_ranked_readers(format)

        # Cache
        self._cache[format] = ranked

        return ranked

    def register(self, reader_class, metadata):
        # ... registration logic ...

        # Invalider cache car liste a changé
        self._cache.clear()
```

**Gain:**
- Première ouverture format X: O(n log n)
- Ouvertures suivantes format X: O(1)
- Utile si on ouvre beaucoup de lames du même format

---

## 11. Extensibilité et Plugins

### 11.1 Architecture Plugins

**Principe:** Les plugins peuvent enregistrer leurs readers sans modifier le code core.

**Structure:**
```
VarunaPoC/
├── backend/
│   ├── services/
│   │   └── readers/
│   │       ├── __init__.py
│   │       ├── base.py             ← ReaderInterface
│   │       ├── registry.py         ← ReaderRegistry
│   │       ├── selector.py         ← ReaderSelector
│   │       ├── openslide_reader.py
│   │       └── bioformats_reader.py
│   └── plugins/
│       ├── __init__.py
│       ├── loader.py               ← Plugin loader
│       └── custom_reader_plugin/
│           ├── __init__.py
│           ├── reader.py           ← Custom reader
│           └── metadata.py         ← Capabilities
```

### 11.2 Plugin Interface

```python
# backend/plugins/loader.py

from typing import List, Type
import importlib
import pkgutil


class PluginLoader:
    """
    Charge dynamiquement les plugins de readers.

    Usage:
        >>> loader = PluginLoader(registry)
        >>> loader.discover_plugins("backend.plugins")
    """

    def __init__(self, registry: ReaderRegistry):
        self._registry = registry

    def discover_plugins(self, package_name: str) -> List[str]:
        """
        Découvre et charge tous les plugins dans un package.

        Args:
            package_name: Nom du package à scanner (ex: "backend.plugins")

        Returns:
            Liste des noms de plugins chargés
        """
        package = importlib.import_module(package_name)
        plugins_loaded = []

        for _, plugin_name, _ in pkgutil.iter_modules(package.__path__):
            try:
                # Importer plugin
                plugin_module = importlib.import_module(
                    f"{package_name}.{plugin_name}"
                )

                # Chercher fonction register_reader()
                if hasattr(plugin_module, 'register_reader'):
                    plugin_module.register_reader(self._registry)
                    plugins_loaded.append(plugin_name)
                    logger.info(f"Loaded plugin: {plugin_name}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")

        return plugins_loaded
```

### 11.3 Exemple de Plugin

```python
# backend/plugins/custom_reader_plugin/__init__.py

from backend.services.readers.base import ReaderInterface, ReaderMetadata, ReaderCapability
from backend.services.readers.registry import ReaderRegistry
from .reader import CustomReader


def register_reader(registry: ReaderRegistry):
    """
    Point d'entrée du plugin.
    Appelé automatiquement par PluginLoader.
    """

    # Définir capabilities
    metadata = ReaderMetadata(
        name="custom_reader",
        version="1.0.0",
        capabilities={
            "VSI": ReaderCapability(
                format="VSI",
                score=90,
                notes="Support Olympus VSI via custom implementation"
            ),
            "MRXS": ReaderCapability(
                format="MRXS",
                score=70,
                notes="Alternative to OpenSlide"
            )
        },
        priority=60  # Priorité moyenne
    )

    # Enregistrer
    registry.register(CustomReader, metadata)


# backend/plugins/custom_reader_plugin/reader.py

class CustomReader(ReaderInterface):
    """Custom reader implementation."""

    def open(self, path: str) -> None:
        # ... custom implementation ...
        pass

    # ... autres méthodes ReaderInterface ...
```

### 11.4 Configuration Plugins

**Fichier config (plugins.yaml):**
```yaml
plugins:
  enabled: true
  auto_discover: true
  package: "backend.plugins"

  # Whitelist (si vide, tous acceptés)
  whitelist: []

  # Blacklist
  blacklist:
    - "untrusted_plugin"

  # Timeout par reader (secondes)
  timeout: 30
```

**Chargement:**
```python
# backend/main.py

def setup_application():
    """Configure l'application au démarrage."""

    # Créer registre
    registry = ReaderRegistry()

    # Enregistrer readers core
    registry.register(OpenSlideReader, OPENSLIDE_METADATA)

    # Charger plugins
    if config.plugins.enabled:
        loader = PluginLoader(registry)
        plugins = loader.discover_plugins(config.plugins.package)
        logger.info(f"Loaded {len(plugins)} plugins: {plugins}")

    return registry
```

---

## 12. Implémentation Progressive

### 12.1 Phase 1: Mono-Reader (Actuel)

**Objectif:** Continuer avec OpenSlide uniquement, mais préparer l'architecture.

**Actions:**
1. ✅ Garder code actuel (`slide_loader.py`)
2. ⚠️ Créer `ReaderInterface` (interface abstraite)
3. ⚠️ Implémenter `OpenSlideReader` (wrapper autour de code actuel)
4. ⚠️ Créer `ReaderRegistry` (avec 1 seul reader)

**Avantages:**
- Pas de régression (même comportement)
- Prépare migration future
- Code déjà testé en production

### 12.2 Phase 2: Multi-Reader (Court terme)

**Objectif:** Ajouter Bio-Formats comme fallback.

**Actions:**
1. Implémenter `BioFormatsReader`
2. Enregistrer dans `ReaderRegistry`
3. Tester fallback avec fichiers Olympus VSI
4. Documenter limitations

**Bénéfices:**
- Support Olympus VSI (actuellement non supporté)
- Support Zeiss CZI JPEG XR
- Validation du système de fallback

### 12.3 Phase 3: Plugin System (Moyen terme)

**Objectif:** Permettre plugins externes.

**Actions:**
1. Implémenter `PluginLoader`
2. Créer plugin template/exemple
3. Documenter API plugin
4. Ajouter tests plugin loader

**Bénéfices:**
- Extensibilité sans modifier core
- Communauté peut contribuer readers
- Formats propriétaires supportables

### 12.4 Phase 4: Optimisations (Long terme)

**Objectif:** Performance et robustesse.

**Actions:**
1. Cache format→readers
2. Timeout par reader
3. Métriques (temps ouverture, taux succès, etc.)
4. Health check readers (désactiver si trop d'échecs)

**Bénéfices:**
- Performance améliorée
- Fiabilité accrue
- Observabilité

---

## 13. Checklist Implémentation

### 13.1 Développeur Backend

Avant de commencer l'implémentation, vérifier:

- [ ] Architecture comprise (diagrammes UML, séquence)
- [ ] Patterns compris (Strategy, Chain of Responsibility, Registry)
- [ ] Interface `ReaderInterface` définie
- [ ] Structures de données définies (ReaderCapability, ReaderMetadata)
- [ ] Tests unitaires planifiés
- [ ] Documentation API écrite

### 13.2 Tests à Implémenter

**Tests unitaires:**
- [ ] `test_reader_capability` - Validation scores
- [ ] `test_reader_metadata` - get_score()
- [ ] `test_reader_registry_register` - Enregistrement
- [ ] `test_reader_registry_get_ranked` - Tri correct
- [ ] `test_reader_selector_fallback` - Chain of responsibility

**Tests d'intégration:**
- [ ] `test_openslide_reader_mrxs` - Ouvrir MRXS
- [ ] `test_bioformats_reader_vsi` - Ouvrir VSI
- [ ] `test_selector_fallback_real` - Fallback avec vrais fichiers
- [ ] `test_plugin_loader` - Chargement dynamique

**Tests de performance:**
- [ ] `benchmark_select_and_open` - Temps sélection (<10ms)
- [ ] `benchmark_fallback` - Temps fallback complet

### 13.3 Documentation à Créer

- [ ] `backend/services/readers/README.md` - Vue d'ensemble système
- [ ] `docs/Manuel/XX-FORMATS_MULTIPLES.md` - Pour utilisateurs
- [ ] `docs/architecture/PLUGIN_API.md` - API pour développeurs plugins
- [ ] Docstrings complets pour chaque classe/méthode

---

## 14. Conclusion

### 14.1 Récapitulatif

Ce document définit un système de sélection de readers:

**Simple:**
- 3 patterns bien connus (Strategy, Chain of Responsibility, Registry)
- Structures de données minimales (3 dataclasses)
- Algorithme linéaire O(n)

**Robuste:**
- Fallback automatique si échec
- Gestion erreurs granulaire
- Logging détaillé pour debug

**Extensible:**
- Plugin system pour ajout dynamique
- Interface claire (ReaderInterface)
- Configuration flexible

**Performant:**
- Sélection rapide (< 10ms)
- Cache format→readers
- Parallélisation possible (Phase 3+)

### 14.2 Prochaines Étapes

1. **Validation architecture:** Revue avec équipe backend
2. **Prototype:** Implémenter Phase 1 (mono-reader avec nouvelle architecture)
3. **Tests:** Valider avec fichiers réels
4. **Phase 2:** Ajouter Bio-Formats
5. **Documentation:** Compléter docs utilisateur/développeur

### 14.3 Ressources

**Patterns:**
- [Refactoring Guru - Strategy](https://refactoring.guru/design-patterns/strategy)
- [Refactoring Guru - Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility)

**Bibliothèques:**
- OpenSlide: https://openslide.org/
- Bio-Formats: https://www.openmicroscopy.org/bio-formats/
- libvips: https://www.libvips.org/

---

**VERSION:** 1.0
**DERNIÈRE RÉVISION:** 2026-02-04
**AUTEUR:** Design Patterns Specialist + Algorithms Specialist
**STATUT:** Prêt pour implémentation
