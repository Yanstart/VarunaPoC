# backend/services

## But
Couche metier du backend. Toute la logique non-HTTP: lecture de lames, detection de formats, annotations spatiales, ML, standards medicaux.

## Structure
```
services/
  # --- Coeur (obligatoire) ---
  slide_scanner.py         # Scan recursif /Slides, detection auto des lames
  slide_loader.py          # OpenSlide: metadata, overview, proprietes
  format_detector.py       # Detection formats multi-fichiers (MRXS, BIF...) [35K lignes]
  folder_browser.py        # Navigation hierarchique des dossiers
  tile_server.py           # Streaming tuiles DZI vers OpenSeadragon
  annotation_service.py    # CRUD annotations + requetes spatiales PostGIS

  # --- ML (optionnel) ---
  ml/
    tag_extractor.py       # Auto-tag: organe, coloration, marqueur
    tag_router.py          # Routing vers modele specialise selon tags
    clustering.py          # Clustering spatial d'annotations
    counting.py            # Comptage cellules/objets
    drift.py               # Detection derive donnees/predictions
    retraining.py          # Pipeline retraining automatique
    similarity_index.py    # Recherche similarite FAISS
  detection/
    pipeline.py            # Orchestration: heatmap -> contours -> GeoJSON
    postprocessing.py      # Extraction contours, simplification Douglas-Peucker

  # --- Cache ---
  cache/
    disk_cache.py          # Cache numpy .npy (embeddings, heatmaps)
    memory_cache.py        # LRU in-memory

  # --- Lecteurs pluggables ---
  readers/
    base.py                # Interface Reader
    openslide_reader.py    # Lecteur par defaut (OpenSlide)
    ome_tiff_reader.py     # OME-TIFF
    ome_zarr_reader.py     # OME-Zarr (cloud-native)
    bioformats_reader.py   # Bio-Formats (Java bridge)
    selector.py            # Selection auto du lecteur

  # --- Standards medicaux ---
  dicomweb.py              # WADO-RS, STOW-RS, QIDO-RS
  dicom_export.py          # Export annotations en DICOM SR
  hl7v2_parser.py          # Parsing messages HL7v2
  terminology.py           # SNOMED CT, LOINC
  # + abdm.py, apsr.py, ehealth_be.py, ssmix2.py (standards regionaux)
```
