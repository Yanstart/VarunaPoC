# readers

## But
Systeme de lecteurs de lames enfichables implementant les patterns Strategy et Chain of Responsibility.

## Pourquoi
Les lames histologiques existent dans de nombreux formats proprietaires ; un systeme de lecteurs interchangeables permet de supporter chaque format via le backend le plus adapte.

## Structure
- `__init__.py` -- Package readers ; expose default_selector, OpenSlideReader et les classes principales.
- `base.py` -- Classe abstraite ISlideReader : interface commune que tous les lecteurs doivent implementer.
- `selector.py` -- ReaderSelector : selection automatique du meilleur lecteur par score de confiance et fallback.
- `openslide_reader.py` -- Adaptateur OpenSlide : SVS, NDPI, MRXS, BIF, SCN, TIFF pyramidal.
- `ome_tiff_reader.py` -- Lecteur OME-TIFF via tifffile : metadata OME-XML, canaux, Z-stacks.
- `ome_zarr_reader.py` -- Lecteur OME-Zarr/NGFF via zarr : acces par chunks, pyramides multi-resolution.
- `bioformats_reader.py` -- Lecteur BioFormats (stub) : CZI, ND2, LIF, VSI (necessite JRE).
