# Etude des Solutions Existantes - Ecosysteme WSI

**Date:** 2026-02-04
**Contexte:** Analyse comparative avant developpement VarunaPoC
**Objectif:** Eviter de reinventer la roue, identifier les angles morts du marche

---

## Table des Matieres

1. [Resume Executif](#1-resume-executif)
2. [OHIF Viewer + Cornerstone3D](#2-ohif-viewer--cornerstone3d)
3. [ITK / SimpleITK](#3-itk--simpleitk)
4. [napari](#4-napari)
5. [libvips](#5-libvips)
6. [Bio-Formats / OME](#6-bio-formats--ome)
7. [Plateformes WSI Existantes](#7-plateformes-wsi-existantes)
8. [Matrice de Decision](#8-matrice-de-decision)
9. [Recommandations pour VarunaPoC](#9-recommandations-pour-varunapoc)
10. [Sources](#10-sources)

---

## 1. Resume Executif

### Positionnement VarunaPoC

VarunaPoC occupe une position **unique et non-concurrencee** dans l'ecosysteme:

```
SPECTRE D'USAGE:
+-- Desktop Rich Analysis      --> QuPath (academique)
+-- Large Organization Archive --> DSA/Orthanc (IT)
+-- Team Collaboration Focus   --> Cytomine (research)
+-- MLOps Integration          --> Slideflow (data scientists)
+-- Enterprise PACS            --> Mainecoon (hospitals)
+-- Radical Simplicity         --> VarunaPoC (cliniciens)
```

### Conclusion Principale

**L'approche VarunaPoC (OpenSlide + OpenSeadragon + Vanilla JS) est architecturalement saine** car:

1. **Preuve de concept** - demontre viabilite viewer web
2. **Vendor-neutral** - tous formats proprietaires supportes
3. **Minimal stack** - performance, maintenabilite
4. **Future-proof** - OpenSlide 4.0+ supportera DICOM natif

### Les 3 Angles Morts du Marche (Opportunites VarunaPoC)

| Angle Mort | Gap Identifie | Opportunite |
|------------|---------------|-------------|
| **Quality-First Annotations** | Aucune plateforme ne structure la qualite des annotations | Metriques IAA, workflows consensus |
| **MLOps Integration** | Viewer != ML platform (separation) | Middleware viewer <-> Slideflow |
| **Radical Simplicity** | Meme systemes "simples" necessitent formation | UX 1-click pour cliniciens |

---

## 2. OHIF Viewer + Cornerstone3D

### Architecture Technique

**Cornerstone3D** utilise **vtk.js** comme backbone de rendu avec WebGL 2.0 pour acceleration GPU.

```
Frontend (OHIF)
    +-- Cornerstone3D Extension (rendering)
    +-- DICOM Segmentation Extension
    +-- RTSTRUCT Extension
    +-- Microscopy Extension (pathologie WSI)

Backend Services
    +-- DICOMweb APIs (QIDO-RS, WADO-RS, STOW-RS)
    +-- DICOM servers/PACS
    +-- AI servers (MONAI Label, etc.)
```

**Pipeline de Rendu:**
- **TiledRenderingEngine:** Canvas offscreen unique pour tous viewports
- **ContextPoolRenderingEngine (defaut):** Reduit pertes contexte WebGL
- Chargement streaming image par image (pas de chargement complet volume)

### DICOM Supplement 145: WSI Standard

**Caracteristiques:**
- Images multi-frames tiled permettant acces aleatoire aux sous-regions
- Pyramides de resolutions multiples
- Stockage organise en tuiles pour efficacite streaming
- Metadonnees standardisees (patient, specimen, scanner)

### Ecosysteme Python DICOM

| Outil | Role |
|-------|------|
| **pydicom** | Fondation pure Python pour lire/modifier/ecrire DICOM |
| **highdicom** | Abstraction pour devs ML/image, interface pythonique |
| **pynetdicom** | Networking DICOM (C-FIND, C-MOVE, C-STORE) |
| **dcm4che** | Framework enterprise Java pour DICOM complet |

### Comparaison OpenSlide vs DICOM WSI

| Critere | OpenSlide | DICOM WSI |
|---------|-----------|-----------|
| **Formats proprietaires** | Support natif | Via conversion |
| **Interoperabilite PACS** | Non natif | Complete |
| **Metadonnees cliniques** | Basique | Completes |
| **AI/ML facilite** | Python simple | MONAI integre |
| **Annotations standards** | Custom | DICOM Seg |
| **Performance** | Leger | Serveur requis |
| **Courbe apprentissage** | Facile | Complexe |

### Quand Choisir OHIF/Cornerstone3D vs OpenSeadragon

**OHIF/Cornerstone3D ideal pour:**
- Hospital deployment (PACS integration)
- Clinical production (compliance FDA/ISO)
- Multi-site pathology networks
- AI/MLOps integration (MONAI)

**OpenSeadragon ideal pour:**
- Research environments
- Multi-vendor proprietary format support
- Minimal infrastructure
- Prototype rapide/MVP

**Verdict VarunaPoC:** OpenSeadragon est le bon choix pour Phase 1 (PoC). Migration OHIF possible Phase 2+ si compliance PACS requise.

---

## 3. ITK / SimpleITK

### Architecture Fondamentale

**ITK (Insight Toolkit)** est une bibliotheque C++ pour traitement d'images N-dimensionnelles construite sur une **architecture spatialisee**.

**Capacites Principales:**

| Categorie | Algorithmes |
|-----------|-------------|
| **Segmentation** | Level Sets, Watershed, Thresholding, Connected Components |
| **Registration** | Rigide, Affine, B-spline deformable, LDDMM diffeomorphique |
| **Filtrage** | Gaussien, Laplacien, gradient, morphologique, Fourier |

### Pipeline ITK

```
Input Image --> [Filter Chain] --> [Transform] --> Output
   |                 |                  |            |
 Reader         Preprocessing      Registration   Writer
               (denoise, resample)  (alignment)
```

Chaque etape est **lazy-evaluated**: ITK ne calcule que ce dont vous avez besoin.

### Ecosysteme Dependant

| Outil | Description |
|-------|-------------|
| **3D Slicer** | Plateforme chirurgicale (ITK + VTK) |
| **MITK** | Medical Imaging Interaction Toolkit |
| **ANTs** | Registration hyper-specialisee neuroimagerie |
| **Elastix** | Registration intensity-based |
| **HistomicsTK** | Pathologie numerique (ITK-based) |

### Limitation Critique pour WSI

**Probleme:** SimpleITK charge images **entierement en memoire**.

- Lame histologie 100k x 80k pixels RGB = **24 GB** non-compresse
- SimpleITK crash a ~500M voxels
- Registration 2 lames gigapixel = **infaisable naivement**

**Solution:** Utiliser **OpenSlide + ITK** (ITKIOOpenSlide module) pour streaming par tiles.

### Pertinence pour VarunaPoC

| Usage | Recommandation |
|-------|----------------|
| **Viewer (Phase 1)** | Ne pas utiliser ITK (trop heavy) |
| **Segmentation nuclei (Phase 2+)** | ITK watershed post-CNN |
| **Color normalization** | HistomicsTK (ITK-based) |
| **Registration multi-lames** | Elastix/ANTs |

---

## 4. napari

### Architecture

**napari** est un visualiseur **intrinsequement n-dimensionnel** avec rendering GPU via VisPy/OpenGL.

**Pipeline de Rendu:**
1. **Viewing** (`ViewerModel.dims`): Region visible du espace n-dimensionnel
2. **Slicing** (`Layer._slice_dims`): Charge region en RAM
3. **Drawing** (`VispyBaseLayer`): Transfert RAM -> VRAM (GPU)

### 6 Types de Couches

| Type | Usage | Cas d'Usage Pathologie |
|------|-------|------------------------|
| **Image** | Donnees raster 2D/3D | Images de lames |
| **Labels** | Masques de segmentation | Annotations regions |
| **Points** | Coordonnees spatiales | Detections cellules |
| **Vectors** | Champs directionnels | Gradients |
| **Shapes** | Polygones, rectangles | Annotations freehand |
| **Surface** | Mailles 3D | Reconstructions |

### Plugins Pertinents pour WSI

| Plugin | Auteur | Description |
|--------|--------|-------------|
| **napari-lazy-openslide** | Trevor Manz | Lazy loading via OpenSlide + Dask |
| **napari-wsi** | AstraZeneca | Interface unifiee Zarr pour WSI |
| **napari-wsireg** | Nathan Patterson | Alignement multi-lames (CZI-funded) |

### napari vs OpenSeadragon

| Aspect | napari | OpenSeadragon |
|--------|--------|---------------|
| **Plateforme** | Desktop (Qt) + Python | Web (JavaScript) |
| **GPU Rendering** | VisPy/OpenGL obligatoire | Canvas 2D HTML5 |
| **Paradigme** | Interactive scientific tool | Passive viewer embed |
| **Annotations** | Native (Shapes, Labels) | Plugins tiers |
| **ML Integration** | Tight (Python ecosystem) | Difficile |
| **Deployment** | Single machine + Docker | Distributed web |

### Verdict pour VarunaPoC

**OpenSeadragon est meilleur pour VarunaPoC car:**
1. Requirement web (hospital IT infrastructure)
2. Multi-users concurrents (architecture stateless)
3. JS frontend + Python backend separes (flexibilite)
4. Mature et stable (10+ ans production)

**napari utile pour Phase 2+:** Research/AI lab en parallele du viewer web clinique.

---

## 5. libvips

### Architecture Streaming Demand-Driven

libvips implemente un systeme **evaluation retardee horizontalement threadee** ou les operations calculent que les pixels demandes, jamais l'image entiere.

**Mecanisme:**
```
Une image partielle = fonction(x,y) plutot que pixel_array[x,y]

Fonction = 3 parties:
- start()    --> initialiser etat thread
- generate() --> calculer pixels demandes
- stop()     --> nettoyer ressources
```

### Performance vs ImageMagick

| Metrique | libvips | ImageMagick | Ratio |
|----------|---------|-------------|-------|
| **Memoire (10000x10000)** | 200 MB | 3 GB | **15x moins** |
| **Vitesse crop+resize+sharpen** | 1.2s | 7.5s | **6x plus rapide** |
| **I/O disque** | Minimal | Massif | **5-8x moins** |

### Support Formats WSI (via OpenSlide)

- MRXS (3DHistech)
- SVS (Aperio)
- NDPI (Hamamatsu)
- BIF (Roche/Ventana)
- TIFF pyramidal

### pyvips vs Pillow

| Operation | pyvips | Pillow |
|-----------|--------|--------|
| Charger 1GB TIFF | 5ms | 3s (load complet!) |
| Crop + resize 1GB | 500ms, ~100MB | >3GB RAM |
| Memoire gigapixel | ~100MB | CRASH |
| Niveaux pyramidaux | Via OpenSlide | Non |

### Pertinence pour VarunaPoC

**Phase 1 (PoC):** Garder OpenSlide + Pillow (correct, simple)

**Phase 2+ (Production):** Envisager pyvips SI:
- Tile serving devient bottleneck CPU (>20% du temps)
- Memory spikes observes (>500MB)
- Benchmarks montrent Pillow >30% plus lent

**Integration optimale:** Hybrid (OpenSlide pour parsing, pyvips pour streaming)

---

## 6. Bio-Formats / OME

### Capacites

Bio-Formats supporte **160+ formats proprietaires** incluant:

| Categorie | Formats |
|-----------|---------|
| **Histopathologie** | MRXS, BIF, TIF, CZI, NDPI, VSI |
| **Microscopie** | Zeiss LSM, Nikon ND2, Leica LIF |
| **Standards** | OME-TIFF, OME-Zarr, DICOM |

### Comparaison OpenSlide vs Bio-Formats

| Critere | OpenSlide | Bio-Formats |
|---------|-----------|-------------|
| **Vitesse tile** | 50-100ms | 100-200ms |
| **Formats pathology** | ~20 | ~160 |
| **Multidimensionnel** | Non | Oui (Z/C/T) |
| **Python integration** | Natif | java-bridge |
| **Maintenance** | Stagnant | Actif |
| **Metadonnees** | Reduites | Completes OME |

### OME-TIFF vs OME-Zarr

| Aspect | OME-TIFF | OME-Zarr |
|--------|----------|----------|
| **Format** | BigTIFF + XML | Zarr v3 + JSON |
| **Cloud-native** | Non (download complet) | Oui (HTTP range) |
| **Performance cloud** | Baseline | **10x+ plus rapide** |
| **Dask compatible** | Non | Oui |

### Ecosysteme Dependant

| Outil | Usage Bio-Formats |
|-------|-------------------|
| **QuPath** | Extension (v0.1.2 seulement) |
| **OMERO** | Moteur central depuis 2007 |
| **ImageJ/Fiji** | Via SCIFIO wrapper |
| **CellProfiler** | python-bioformats |

### Recommandation VarunaPoC

**Phase 1:** OpenSlide suffisant (plus rapide, Python natif)

**Phase 2+ (si formats additionnels requis):**
1. Conversion prealable via bioformats2raw + Zarr
2. Laisser OpenSlide lire les Zarr convertis

---

## 7. Plateformes WSI Existantes

### 7.1 QuPath - Leader Academique

**Architecture:** Desktop Java/Python pour analyse WSI

**Forces:**
- Deep Learning integre (PyTorch, TensorFlow)
- Workflow Groovy scripting
- Export GeoJSON pour pipelines Python
- Communaute scientifique active

**Limites:**
- Desktop-only (pas web)
- Pas oriente production clinique
- Interface technique

### 7.2 Digital Slide Archive (DSA) + HistomicsTK

**Architecture Modulaire:**
```
HistomicsTK (Python processing)
    |
HistomicsUI (Web annotation)
    |
Girder (MongoDB + REST API)
    |
Digital Slide Archive (Plateforme complete)
```

**Forces:**
- Web-based, multi-utilisateur
- API REST robuste
- Open-source

**Limites:**
- 4 composants a gerer
- MongoDB legacy
- Interface datee

### 7.3 Cytomine - Collaboration Pionniere

**Forces:**
- Annotation collaborative multi-utilisateurs
- Semi-automatic via ML
- Scalabilite horizontale

**Limites:**
- Moins documente
- UX moins moderne

### 7.4 ASAP - Minimaliste Desktop

**Forces:**
- Ultra-leger et rapide
- Multi-vendor support
- Bonne performance locale

**Limites:**
- Desktop-only
- Pas de ML moderne

### 7.5 Slideflow - MLOps Native

**TRES PERTINENT pour Phase 2+**

**Capacites:**
- Processing optimise WSI (40X en 2.5sec/slide)
- Support 6 foundation models (UNI, GigaPath, PLIP, etc.)
- Weakly-supervised classification
- Uncertainty quantification
- Explainability tools

**Forces:**
- **Seule plateforme avec vrai MLOps integre**
- Performance optimisee
- Slideflow Labs (2025) = commercialisation

### 7.6 Orthanc WSI + DICOM

**Forces:**
- DICOM-native
- Integration PACS complete
- Enterprise-ready

**Limites:**
- Interface legacy (OpenLayers)
- Pas de collaboration annotation native

### 7.7 Mainecoon - Architecture Moderne 2025

**Architecture:** React + Node.js + Raccoon PACS

**Forces:**
- DICOM-native WSI viewer web
- AI model integration
- Valide DICOM WG26 Connectathon

**Limites:**
- Tres nouveau (2025)
- Specialise DICOM

### 7.8 Solutions Commerciales (Contexte)

| Solution | Status FDA | Prix |
|----------|------------|------|
| **Philips IntelliSite** | FDA 2017 (leader) | >100k EUR |
| **Sectra** | FDA 2024 | Enterprise |
| **Leica Aperio GT 450 DX** | FDA 2024 | Enterprise |
| **3DHISTECH CaseViewer** | CE marked | Mid-range |

---

## 8. Matrice de Decision

### Comparaison Multi-Criteres

| Critere | QuPath | DSA | Cytomine | Slideflow | Mainecoon | **VarunaPoC** |
|---------|--------|-----|----------|-----------|-----------|---------------|
| **Web-based** | Non | Oui | Oui | Oui | Oui | **Oui** |
| **Multi-user** | Non | Limite | Oui | Limite | Oui | Phase 2 |
| **ML/AI integre** | Oui | Plugin | Limite | **Full MLOps** | Oui | Phase 2 |
| **DICOM native** | Non | Non | Non | Non | Oui | Phase 2 |
| **Multi-format** | Oui | Oui | Oui | Oui | DICOM | **Oui** |
| **UX Simplicity** | Limite | Limite | Limite | Limite | Limite | **Oui** |
| **Quality metrics** | Non | Non | Non | Limite | Non | **Phase 2** |

### OpenSeadragon vs Alternatives

| Critere | OpenSeadragon | Cornerstone3D | OpenLayers |
|---------|---------------|---------------|------------|
| **Performance WSI** | Excellent | Excellent | Bon |
| **JavaScript ecosystem** | Mieux documente | Moderne | Legacy |
| **DICOM support** | Via backend | Natif | Via backend |
| **Memory usage** | Lean | Optimise | Plus gourmand |
| **Recommandation** | **PoC Phase 1** | Phase 2+ PACS | Non |

---

## 9. Recommandations pour VarunaPoC

### Phase 1 (Actuelle): Maintenir le Focus

**Continuer avec:**
- OpenSeadragon comme viewer (performant, eprouve)
- FastAPI + OpenSlide (stack moderne, Python mature)
- Vanilla JS + Vite (simple, performant)
- Multi-format support (MRXS, BIF, TIFF)

### Phase 2: Annotations Quality-First

**Priorite 1 - Annotations:**
- Multi-reviewer workflow (blind + consensus)
- Data dictionary par projet
- Metriques Inter-Annotator Agreement (IAA)
- Export GeoJSON (compatible Python/R/ML)

**Priorite 2 - ML Pipeline:**
- REST API pour lier Slideflow
- Provenance tracking (slide -> annotation -> model -> prediction)
- Feature generation hooks

**Priorite 3 - DICOM Compatibility:**
- Export-to-DICOM converter
- Compatible ANN standard
- Import depuis Orthanc

### Ce qu'on NE DOIT PAS Faire

- Repliquer Cytomine's full collaboration (trop complexe)
- Construire notre propre ML engine (utiliser Slideflow)
- Imposer DICOM en Phase 1 (paralyse adoption)
- Desktop application (rester web)

### Roadmap Ideale

```
PHASE 1 (Actuelle): Open + Navigate
+-- Multi-format support
+-- Web access
+-- Minimal learning curve

PHASE 2: Quality-First Annotations
+-- Multi-reviewer workflow
+-- IAA metrics + consensus
+-- Export GeoJSON

PHASE 3: MLOps Pipeline
+-- Slideflow integration
+-- Provenance tracking
+-- Feature generation API

PHASE 4: DICOM Ready
+-- Export-to-DICOM
+-- ANN compliance
+-- Orthanc import
```

---

## 10. Sources

### OHIF / Cornerstone3D
- [Cornerstone3D Documentation](https://www.cornerstonejs.org/)
- [OHIF Viewers GitHub](https://github.com/OHIF/Viewers)
- [DICOM WSI Standard](https://dicom.nema.org/dicom/dicomwsi/)
- [DICOM Supplement 145](https://pmc.ncbi.nlm.nih.gov/articles/PMC3097525/)

### ITK / SimpleITK
- [ITK Official](https://itk.org/)
- [SimpleITK Notebooks](https://github.com/InsightSoftwareConsortium/SimpleITK-Notebooks)
- [HistomicsTK GitHub](https://github.com/DigitalSlideArchive/HistomicsTK)
- [ITKIOOpenSlide](https://github.com/InsightSoftwareConsortium/ITKIOOpenSlide)

### napari
- [napari Official](https://napari.org/)
- [napari-lazy-openslide](https://github.com/manzt/napari-lazy-openslide)
- [napari-wsi](https://github.com/AstraZeneca/napari-wsi)
- [napari-wsireg](https://github.com/NHPatterson/napari-wsireg)

### libvips
- [libvips GitHub](https://github.com/libvips/libvips)
- [pyvips GitHub](https://github.com/libvips/pyvips)
- [Speed and Memory Benchmarks](https://github.com/libvips/libvips/wiki/Speed-and-memory-use)

### Bio-Formats / OME
- [Bio-Formats Official](https://www.openmicroscopy.org/bio-formats/)
- [OME-Zarr Specification](https://ngff.openmicroscopy.org/latest/)
- [OMERO Platform](https://www.openmicroscopy.org/omero/)

### Plateformes WSI
- [QuPath Documentation](https://qupath.readthedocs.io/)
- [Digital Slide Archive](https://github.com/DigitalSlideArchive)
- [Cytomine](https://cytomine.com/)
- [Slideflow GitHub](https://github.com/slideflow/slideflow)
- [Orthanc WSI Plugin](https://orthanc.uclouvain.be/book/plugins/wsi.html)
- [Mainecoon Publication 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12701149/)

### Standards et Best Practices
- [DICOM WG26 Connectathon](https://www.dicomstandard.org/)
- [Annotation Best Practices](https://pmc.ncbi.nlm.nih.gov/articles/PMC8822374/)
- [Leeds Guide to Digital Pathology](https://leicabiosystems.com/knowledge-pathway/the-leeds-guide)

---

**Document genere:** 2026-02-04
**Methode:** Recherche web + documentation officielle + publications scientifiques
**Agent:** Claude Opus 4.5 (recherche parallelisee via 6 sous-agents)
