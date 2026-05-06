# readers

## But
Systeme de lecteurs de lames enfichables implementant les patterns Strategy et Chain of Responsibility.

## Pourquoi
Les lames histologiques existent dans de nombreux formats proprietaires ; un systeme de lecteurs interchangeables permet de supporter chaque format via le backend le plus adapte.

## Comment
Le contrat est un Protocol PEP 544 stateful : `core.interfaces.slide_reader.SlideReader`. Chaque reader est instancie, ouvre un slide via `open(path)`, est utilise pour de multiples `read_region(...)`, puis `close()`. La pattern stateful amortit le cout d'ouverture (handle fichier, init OpenSlide natif) sur de nombreux appels tile.

Les readers concrets satisfont le Protocol par duck typing (PEP 544) — ils n'ont pas a heriter explicitement. Une mini classe utilitaire `SlideReaderBase` fournit le support context-manager (`with reader: ...`).

## Structure
- `__init__.py` -- Re-exports SlideReader (Protocol), ISlideReader (alias backward-compat), readers concrets, et le selector.
- `base.py` -- SlideMetadata dataclass + SlideReaderBase utility (context manager). ISlideReader est re-exporte comme alias de SlideReader (Protocol).
- `selector.py` -- ReaderSelector : selection automatique par score de confiance avec fallback. Validation duck-type structurelle au register().
- `openslide_reader.py` -- Adaptateur OpenSlide : SVS, NDPI, MRXS, BIF, SCN, TIFF pyramidal.
- `ome_tiff_reader.py` -- Lecteur OME-TIFF via tifffile : metadata OME-XML, canaux, Z-stacks.
- `ome_zarr_reader.py` -- Lecteur OME-Zarr/NGFF via zarr : acces par chunks, pyramides multi-resolution.
- `bioformats_reader.py` -- Lecteur BioFormats (stub) : CZI, ND2, LIF, VSI (necessite JRE).

## Migration historique
Auparavant `ISlideReader` etait une `ABC` (fichier `base.py`). Le projet a migre vers PEP 544 Protocols (cf. `core/interfaces/`). L'API et les implementations restent identiques ; seule la mecanique d'enforcement change (duck typing au lieu d'@abstractmethod).
