# Carte de l'Écosystème VarunaPoC - Vue Exhaustive

**Version:** 1.0
**Date:** 2025-10-28
**Objectif:** Cartographier TOUS les objets, classes et fonctions (internes + externes) utilisés pour atteindre nos objectifs

---

## Table des Matières

1. [Inventaire Complet des Éléments](#1-inventaire-complet-des-éléments)
2. [Backend: Classes et Objets Python](#2-backend-classes-et-objets-python)
3. [Frontend: Classes et Objets JavaScript](#3-frontend-classes-et-objets-javascript)
4. [Diagramme de Classes Exhaustif](#4-diagramme-de-classes-exhaustif)
5. [Carte de l'Écosystème Global](#5-carte-de-lécosystème-global)
6. [Flux de Données Détaillés](#6-flux-de-données-détaillés)
7. [Interactions entre Composants](#7-interactions-entre-composants)

---

## 1. Inventaire Complet des Éléments

### 1.1 Vue d'Ensemble Quantitative

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| **Backend Python** |  |  |
| Classes personnalisées | 3 | `FormatDetector`, `TileServer`, `SlideFormat` (dataclass) |
| Fonctions personnalisées | 24 | Services, routes, utilitaires |
| Modules Python (internes) | 6 | main.py, config_openslide.py, routes/*, services/* |
| **Frontend JavaScript** |  |  |
| Fonctions composants | 7 | createFolderBrowser, createHomePage, initViewer, etc. |
| Fonctions API | 4 | fetchSlides, getSlideInfo, fetchBrowse, getOverviewUrl |
| Fonctions utilitaires | 6 | is_safe_path, generate_slide_id, etc. |
| **Dépendances Externes** |  |  |
| Bibliothèques Python | 5 | OpenSlide, FastAPI, Pillow, pathlib, hashlib |
| Bibliothèques JavaScript | 1 | OpenSeadragon |
| **Total Éléments Utilisés** | 56+ | Classes, fonctions, objets natifs inclus |

---

## 2. Backend: Classes et Objets Python

### 2.1 Classes Personnalisées (Nos Créations)

#### **FormatDetector** (services/format_detector.py)

```mermaid
classDiagram
    class FormatDetector {
        -Set~str~ detected_entries
        -Dict scan_stats
        +__init__()
        +detect_format(file_path: Path) SlideFormat
        +scan_directory(root_dir: Path, recursive: bool) List~SlideFormat~
        -_detect_hamamatsu_vms(vms_file: Path) SlideFormat
        -_detect_hamamatsu_vmu(vmu_file: Path) SlideFormat
        -_detect_hamamatsu_ndpi(ndpi_file: Path) SlideFormat
        -_detect_mirax(mrxs_file: Path) SlideFormat
        -_detect_aperio(svs_file: Path) SlideFormat
        -_detect_leica(scn_file: Path) SlideFormat
        -_detect_ventana_bif(bif_file: Path) SlideFormat
        -_detect_sakura(svslide_file: Path) SlideFormat
        -_detect_zeiss_czi(czi_file: Path) SlideFormat
        -_detect_zeiss_zvi(zvi_file: Path) SlideFormat
        -_detect_dicom(dcm_file: Path) SlideFormat
        -_detect_tiff_variant(tif_file: Path) SlideFormat
        -_validate_with_openslide(file_path: Path) str
        -_is_vms_ini_file(file_path: Path) bool
        -_is_vmu_ini_file(file_path: Path) bool
    }
```

**Attributs:**
- `detected_entries`: Set[str] - Évite détection multiple des mêmes fichiers
- `scan_stats`: Dict - Statistiques scan (scanned, detected, ignored, errors)

**Méthodes publiques:**
- `detect_format(file_path)` → Détecte format d'un fichier unique
- `scan_directory(root_dir, recursive)` → Scan complet d'un dossier

**Méthodes privées de détection (12):**
- Une par format supporté (.vms, .vmu, .ndpi, .mrxs, .svs, .scn, .bif, .svslide, .czi, .zvi, .dcm, .tif/.tiff)

---

#### **TileServer** (services/tile_server.py)

```mermaid
classDiagram
    class TileServer {
        -Dict~str,OpenSlide~ _slide_cache
        -int _max_cache_size
        +__init__()
        +get_slide(slide_path: str) OpenSlide
        +get_tile(slide_path: str, level: int, col: int, row: int, tile_size: int) bytes
        +get_dzi_metadata(slide_path: str) dict
        +close_all()
        +__del__()
    }
```

**Attributs:**
- `_slide_cache`: Dict[str, OpenSlide] - Cache des slides ouverts (max 5)
- `_max_cache_size`: int - Limite cache (5 slides)

**Méthodes:**
- `get_slide(slide_path)` → Ouvre ou récupère slide depuis cache
- `get_tile(...)` → Extrait tuile JPEG à position donnée
- `get_dzi_metadata(slide_path)` → Métadonnées pour OpenSeadragon
- `close_all()` → Ferme tous les slides en cache
- `__del__()` → Cleanup automatique

**Instance singleton:**
- `tile_server` (objet global partagé)

---

#### **SlideFormat** (dataclass - services/format_detector.py)

```mermaid
classDiagram
    class SlideFormat {
        +str name
        +Path entry_point
        +bool is_supported
        +List~Path~ joint_files
        +List~Path~ companion_dirs
        +List~Path~ metadata_files
        +str format_string
        +str structure_type
        +str detection_method
        +str notes
    }
```

**Dataclass Python** (décorateur @dataclass)

**Attributs:**
- `name`: Nom lisible (ex: "Hamamatsu VMS", "MIRAX")
- `entry_point`: Fichier à passer à OpenSlide()
- `is_supported`: True si OpenSlide peut l'ouvrir
- `joint_files`: Fichiers joints requis
- `companion_dirs`: Dossiers compagnons
- `metadata_files`: Fichiers métadonnées
- `format_string`: Retour de detect_format() ("hamamatsu", "mirax", etc.)
- `structure_type`: "single-file", "multi-file", "with-companion-dir"
- `detection_method`: Méthode utilisée (debug)
- `notes`: Informations additionnelles

---

### 2.2 Objets Externes Utilisés (Bibliothèques Python)

#### **OpenSlide (bibliothèque C, binding Python)**

```mermaid
classDiagram
    class OpenSlide {
        <<external>>
        +tuple dimensions
        +int level_count
        +tuple level_dimensions
        +tuple level_downsamples
        +dict properties
        +__init__(filename: str)
        +read_region(location: tuple, level: int, size: tuple) Image
        +get_thumbnail(size: tuple) Image
        +close()
        +detect_format(filename: str)$ str
    }

    class OpenSlideError {
        <<external exception>>
    }
```

**Attributs (propriétés en lecture):**
- `dimensions`: (width, height) niveau 0
- `level_count`: Nombre de niveaux pyramidaux
- `level_dimensions`: [(w,h), ...] pour chaque niveau
- `level_downsamples`: [1.0, 4.0, 16.0, ...] facteurs de réduction
- `properties`: Dict avec métadonnées vendor-specific (61+ clés)

**Méthodes:**
- `__init__(filename)` → Ouvre une lame
- `read_region(location, level, size)` → Extrait région RGBA
- `get_thumbnail(size)` → Génère thumbnail optimisé
- `close()` → Ferme la lame
- **Static:** `detect_format(filename)` → Détecte format sans ouvrir

**Constantes utilisées:**
- `PROPERTY_NAME_VENDOR` → Clé propriété vendor
- `PROPERTY_NAME_MPP_X` → Microns par pixel X
- `PROPERTY_NAME_MPP_Y` → Microns par pixel Y

---

#### **FastAPI (framework web)**

```mermaid
classDiagram
    class FastAPI {
        <<external>>
        +str title
        +str description
        +str version
        +__init__(...)
        +get(path: str, tags: list)
        +include_router(router: APIRouter)
        +add_middleware(middleware_class, ...)
    }

    class APIRouter {
        <<external>>
        +str prefix
        +__init__(prefix: str)
        +get(path: str, tags: list)
    }

    class HTTPException {
        <<external exception>>
        +int status_code
        +str detail
    }

    class Response {
        <<external>>
        +bytes content
        +str media_type
    }

    class JSONResponse {
        <<external>>
        +dict content
    }

    class Query {
        <<external>>
        +default
        +description: str
    }

    class Path {
        <<external>>
        +description: str
    }
```

**Classes utilisées:**
- `FastAPI` → Application principale
- `APIRouter` → Routage modulaire (slides.py)
- `HTTPException` → Erreurs HTTP (404, 500, etc.)
- `Response` → Réponses custom (JPEG bytes)
- `JSONResponse` → Réponses JSON
- `Query` → Paramètres query string
- `Path` → Paramètres path
- `CORSMiddleware` → Gestion CORS

---

#### **Pillow (PIL - traitement d'images)**

```mermaid
classDiagram
    class Image {
        <<external module>>
        +new(mode: str, size: tuple, color: tuple)$ Image
        +open(filename: str)$ Image
    }

    class ImageInstance {
        <<external>>
        +str mode
        +tuple size
        +convert(mode: str) Image
        +save(fp, format: str, quality: int, optimize: bool)
        +paste(image: Image, box: tuple)
    }
```

**Module PIL.Image:**
- `Image.new(mode, size, color)` → Crée image vide
- `Image.open(filename)` → Ouvre image

**Instance PIL.Image:**
- `convert(mode)` → Convertit format (RGBA → RGB)
- `save(fp, format, quality, optimize)` → Sauvegarde
- `paste(image, box)` → Colle image dans autre

**Utilisations dans VarunaPoC:**
- Conversion RGBA (OpenSlide) → RGB (JPEG)
- Création tuiles avec fond noir si incomplètes
- Encodage JPEG avec qualité 85

---

#### **Python Standard Library**

```mermaid
classDiagram
    class Path {
        <<pathlib>>
        +str name
        +str stem
        +str suffix
        +Path parent
        +exists() bool
        +is_file() bool
        +is_dir() bool
        +glob(pattern: str) Generator
        +resolve() Path
        +is_relative_to(other: Path) bool
    }

    class BytesIO {
        <<io>>
        +__init__(bytes)
        +getvalue() bytes
        +seek(pos: int)
    }

    class hashlib {
        <<module>>
        +md5(data: bytes) hashobject
    }

    class logging {
        <<module>>
        +getLogger(name: str) Logger
        +info(msg: str)
        +warning(msg: str)
        +error(msg: str)
        +debug(msg: str)
    }
```

**pathlib.Path:**
- Navigation système fichiers
- Manipulation chemins
- Glob patterns
- Validation chemins (security)

**io.BytesIO:**
- Conversion PIL.Image → bytes
- Buffer mémoire pour JPEG

**hashlib:**
- `md5()` → Génération IDs uniques slides

**logging:**
- Logs structurés (info, warning, error, debug)

---

### 2.3 Fonctions Globales Backend

#### **Routes (routes/slides.py)**

```python
# Endpoints API
async def list_slides() -> Dict
async def browse_slides_directory(path: str) -> Dict
async def get_slide_info(slide_id: str) -> Dict
async def get_overview(slide_id: str) -> Response
async def get_dzi_metadata(slide_id: str) -> JSONResponse
async def get_tile(slide_id: str, level: int, col: int, row: int) -> Response
```

**6 endpoints REST:**
1. `GET /api/slides/` → Liste toutes lames (récursif)
2. `GET /api/slides/browse?path=` → Navigation hiérarchique
3. `GET /api/slides/{id}/info` → Métadonnées lame
4. `GET /api/slides/{id}/overview` → Image overview (JPEG)
5. `GET /api/slides/{id}/dzi.json` → Métadonnées DZI
6. `GET /api/slides/{id}/tiles/{level}/{col}_{row}.jpg` → Tuile JPEG

---

#### **Services**

**slide_scanner.py:**
```python
def scan_slides_directory(slides_dir: str) -> List[Dict]
def get_slide_path_by_id(slide_id: str) -> Optional[str]
```

**slide_loader.py:**
```python
def get_slide_metadata(slide_path: str) -> Dict
def get_slide_overview_bytes(slide_path: str, max_size: int, quality: int) -> bytes
def _detect_format(slide_path: str, slide: OpenSlide) -> str
```

**folder_browser.py:**
```python
def browse_directory(relative_path: str) -> Dict
def is_safe_path(requested_path: str) -> bool
def get_breadcrumb(path: str) -> List[str]
def count_items_in_folder(folder_path: Path) -> int
def generate_slide_id(file_path: Path) -> str
def _get_dependency_paths(entry_point: Path, slide_format) -> List[str]
```

**config_openslide.py:**
```python
def configure_openslide_path() -> bool
```

**main.py:**
```python
async def root() -> Dict
async def health() -> Dict
```

---

## 3. Frontend: Classes et Objets JavaScript

### 3.1 Fonctions Composants (Vanilla JS)

#### **main.js (Entry Point)**

```javascript
// Variables globales
let currentPage: string  // 'home' | 'viewer'
let selectedSlide: Object
let viewer: OpenSeadragon.Viewer
let folderBrowser: HTMLElement

// Fonctions
async function init(): void
function showHomePage(): void
async function showViewerPage(slide: Object): void
function handleSlideSelect(slide: Object): void
async function loadSlide(slide: Object): void
```

**État global:**
- `currentPage` → Page actuelle (navigation SPA)
- `selectedSlide` → Lame sélectionnée
- `viewer` → Instance OpenSeadragon
- `folderBrowser` → Composant explorateur

---

#### **FolderBrowser.js**

```javascript
function createFolderBrowser(onSlideSelect: Function): HTMLElement

// Fonctions internes (closures)
async function loadDirectory(path: string): void
function renderBreadcrumb(segments: Array, parentPath: string): void
function renderContent(folders: Array, slides: Array, files: Array): void
function createFoldersSection(folders: Array): HTMLElement
function createSlidesSection(slides: Array): HTMLElement
function createFilesSection(files: Array): HTMLElement
function handleLocalFiles(files: Array): void
```

**Pattern:** Fonction factory retournant HTMLElement avec état encapsulé (closures)

---

#### **Viewer.js**

```javascript
function initViewer(elementId: string): OpenSeadragon.Viewer
async function loadSlideWithTiles(viewer: Viewer, slideId: string): void
function loadOverview(viewer: Viewer, overviewUrl: string): void  // legacy
```

**Configuration OpenSeadragon:**
- Navigator (mini-map) activé
- Contraintes navigation (visibilityRatio, constrainDuringPan)
- Tile source custom avec getLevelScale() et getNumTiles()

---

#### **SlideList.js**

```javascript
function createSlideList(slides: Array, onClick: Function): HTMLElement
function getStructureIcon(structureType: string): string
function getStructureLabel(structureType: string): string
```

---

#### **Home.js (Legacy - non utilisé Phase 1.8)**

```javascript
function createHomePage(slides: Array, onSlideSelect: Function): HTMLElement
function handleLocalFiles(files: Array): void
function updateHomeStats(filtered: Array, total: Array): void
```

---

### 3.2 API Client (utils/api.js)

```javascript
const API_BASE: string = 'http://localhost:8000'

async function fetchSlides(): Promise<Object>
async function getSlideInfo(slideId: string): Promise<Object>
function getOverviewUrl(slideId: string): string
async function fetchBrowse(path: string): Promise<Object>
```

**Toutes requêtes utilisent Fetch API:**
- GET uniquement (read-only PoC)
- Retourne JSON ou URL
- Gestion erreurs avec try/catch

---

### 3.3 Objets Externes JavaScript

#### **OpenSeadragon (bibliothèque)**

```mermaid
classDiagram
    class OpenSeadragon {
        <<external function>>
        +Viewer(options: Options)
    }

    class Viewer {
        <<external>>
        +Viewport viewport
        +Navigator navigator
        +open(tileSource: TileSource)
        +addHandler(event: string, handler: Function)
        +addOnceHandler(event: string, handler: Function)
        +goToPage(index: int)
        +close()
    }

    class Viewport {
        <<external>>
        +getBounds() Rect
        +getZoom() number
        +panTo(center: Point, immediately: bool)
        +zoomTo(zoom: number, refPoint: Point, immediately: bool)
    }

    class TileSource {
        <<external interface>>
        +number width
        +number height
        +number tileSize
        +number tileOverlap
        +number minLevel
        +number maxLevel
        +getLevelScale(level: int) number
        +getNumTiles(level: int) Object
        +getTileUrl(level: int, x: int, y: int) string
    }

    class ControlAnchor {
        <<external enum>>
        +TOP_LEFT
        +TOP_RIGHT
        +BOTTOM_LEFT
        +BOTTOM_RIGHT
    }
```

**OpenSeadragon() fonction:**
- Factory pour créer Viewer
- Prend Options object

**Viewer (instance):**
- `viewport` → Gestion zoom/pan
- `navigator` → Mini-map
- `open(tileSource)` → Charge source tuiles
- `addHandler(event, handler)` → Events (zoom, pan, etc.)
- `addOnceHandler(event, handler)` → Event une fois

**TileSource (interface custom):**
- `width`, `height` → Dimensions niveau 0
- `tileSize` → 256 pixels
- `getLevelScale(level)` → Facteur échelle (1/downsample)
- `getNumTiles(level)` → {x: cols, y: rows}
- `getTileUrl(level, x, y)` → URL backend

**Events OpenSeadragon utilisables:**
- `'open'` → Source ouverte
- `'viewport-change'` → Zoom/pan
- `'tile-loaded'` → Tuile chargée
- `'animation-finish'` → Animation terminée

---

#### **Web APIs (JavaScript natif)**

```mermaid
classDiagram
    class fetch {
        <<Web API>>
        +(url: string, options: Object) Promise~Response~
    }

    class Response {
        <<Web API>>
        +bool ok
        +int status
        +string statusText
        +json() Promise~Object~
        +text() Promise~string~
        +blob() Promise~Blob~
    }

    class document {
        <<DOM API>>
        +querySelector(selector: string) Element
        +querySelectorAll(selector: string) NodeList
        +createElement(tagName: string) Element
    }

    class Element {
        <<DOM API>>
        +string innerHTML
        +string className
        +classList: DOMTokenList
        +dataset: DOMStringMap
        +addEventListener(event: string, handler: Function)
        +appendChild(child: Node) Node
    }

    class console {
        <<Console API>>
        +log(...args)
        +error(...args)
        +warn(...args)
        +info(...args)
    }
```

**Fetch API:**
- `fetch(url, options)` → Requête HTTP
- `Response.json()` → Parse JSON
- `Response.ok` → Status 200-299

**DOM API:**
- `document.querySelector()` → Sélection élément
- `document.createElement()` → Création élément
- `Element.addEventListener()` → Gestion events
- `Element.classList` → Manipulation classes CSS

**Console API:**
- `console.log()`, `console.error()`, etc.

---

## 4. Diagramme de Classes Exhaustif

### 4.1 Backend Complet avec Dépendances

```mermaid
classDiagram
    %% ============= NOS CLASSES =============
    class FormatDetector {
        -Set detected_entries
        -Dict scan_stats
        +detect_format(Path) SlideFormat
        +scan_directory(Path, bool) List~SlideFormat~
        -_detect_*() SlideFormat
        -_validate_with_openslide(Path) str
    }

    class TileServer {
        -Dict~str,OpenSlide~ _slide_cache
        -int _max_cache_size
        +get_slide(str) OpenSlide
        +get_tile(str, int, int, int, int) bytes
        +get_dzi_metadata(str) dict
        +close_all()
    }

    class SlideFormat {
        <<dataclass>>
        +str name
        +Path entry_point
        +bool is_supported
        +List~Path~ joint_files
        +List~Path~ companion_dirs
        +str format_string
        +str structure_type
    }

    %% ============= OPENSLIDE =============
    class OpenSlide {
        <<external>>
        +tuple dimensions
        +int level_count
        +tuple level_dimensions
        +tuple level_downsamples
        +dict properties
        +read_region(tuple, int, tuple) Image
        +get_thumbnail(tuple) Image
        +close()
        +detect_format(str)$ str
    }

    class OpenSlideError {
        <<exception>>
    }

    %% ============= FASTAPI =============
    class FastAPI {
        <<external>>
        +str title
        +include_router(APIRouter)
        +add_middleware(...)
        +get(path, tags)
    }

    class APIRouter {
        <<external>>
        +str prefix
        +get(path, tags)
    }

    class HTTPException {
        <<exception>>
        +int status_code
        +str detail
    }

    class Response {
        <<external>>
        +bytes content
        +str media_type
    }

    %% ============= PIL =============
    class PILImage {
        <<external>>
        +str mode
        +tuple size
        +convert(str) Image
        +save(fp, format, quality, optimize)
    }

    %% ============= ROUTES (fonctions) =============
    class SlidesRoutes {
        <<module>>
        +list_slides() Dict
        +browse_slides_directory(str) Dict
        +get_slide_info(str) Dict
        +get_overview(str) Response
        +get_dzi_metadata(str) JSONResponse
        +get_tile(str, int, int, int) Response
    }

    %% ============= SERVICES (fonctions) =============
    class SlideScanner {
        <<module>>
        +scan_slides_directory(str) List~Dict~
        +get_slide_path_by_id(str) str
    }

    class SlideLoader {
        <<module>>
        +get_slide_metadata(str) Dict
        +get_slide_overview_bytes(str, int, int) bytes
    }

    class FolderBrowser {
        <<module>>
        +browse_directory(str) Dict
        +is_safe_path(str) bool
        +get_breadcrumb(str) List
        +generate_slide_id(Path) str
    }

    %% ============= RELATIONS =============

    %% FormatDetector utilise OpenSlide
    FormatDetector --> OpenSlide : utilise detect_format()
    FormatDetector --> OpenSlideError : gère exceptions
    FormatDetector ..> SlideFormat : crée

    %% TileServer utilise OpenSlide et PIL
    TileServer --> OpenSlide : ouvre/lit slides
    TileServer --> PILImage : convertit RGBA→RGB
    TileServer --> OpenSlideError : gère exceptions

    %% Routes utilisent services
    SlidesRoutes --> SlideScanner : appelle
    SlidesRoutes --> SlideLoader : appelle
    SlidesRoutes --> FolderBrowser : appelle
    SlidesRoutes --> TileServer : appelle get_tile()
    SlidesRoutes --> HTTPException : lève erreurs
    SlidesRoutes --> Response : retourne images

    %% Services utilisent classes
    SlideScanner --> FormatDetector : utilise scan_directory()
    SlideLoader --> OpenSlide : ouvre slides
    SlideLoader --> PILImage : génère JPEG
    FolderBrowser --> FormatDetector : utilise detect_format()

    %% FastAPI structure
    FastAPI --> APIRouter : inclut
    APIRouter --> SlidesRoutes : contient
```

### 4.2 Frontend Complet avec Dépendances

```mermaid
classDiagram
    %% ============= NOS COMPOSANTS =============
    class Main {
        <<module>>
        -string currentPage
        -Object selectedSlide
        -Viewer viewer
        -HTMLElement folderBrowser
        +init()
        +showHomePage()
        +showViewerPage(Object)
        +handleSlideSelect(Object)
        +loadSlide(Object)
    }

    class FolderBrowserComp {
        <<module>>
        +createFolderBrowser(Function) HTMLElement
        -loadDirectory(string)
        -renderBreadcrumb(Array, string)
        -renderContent(Array, Array, Array)
        -createFoldersSection(Array) HTMLElement
        -createSlidesSection(Array) HTMLElement
        -createFilesSection(Array) HTMLElement
    }

    class ViewerComp {
        <<module>>
        +initViewer(string) Viewer
        +loadSlideWithTiles(Viewer, string)
        +loadOverview(Viewer, string)
    }

    class SlideListComp {
        <<module>>
        +createSlideList(Array, Function) HTMLElement
        -getStructureIcon(string) string
        -getStructureLabel(string) string
    }

    class APIClient {
        <<module>>
        +API_BASE: string
        +fetchSlides() Promise~Object~
        +getSlideInfo(string) Promise~Object~
        +getOverviewUrl(string) string
        +fetchBrowse(string) Promise~Object~
    }

    %% ============= OPENSEADRAGON =============
    class OpenSeadragon {
        <<external function>>
        +(Options) Viewer
    }

    class Viewer {
        <<external>>
        +Viewport viewport
        +Navigator navigator
        +open(TileSource)
        +addHandler(string, Function)
        +addOnceHandler(string, Function)
        +close()
    }

    class TileSource {
        <<interface>>
        +number width
        +number height
        +number tileSize
        +number minLevel
        +number maxLevel
        +getLevelScale(int) number
        +getNumTiles(int) Object
        +getTileUrl(int, int, int) string
    }

    class Viewport {
        <<external>>
        +getBounds() Rect
        +getZoom() number
        +panTo(Point, bool)
        +zoomTo(number, Point, bool)
    }

    %% ============= WEB APIs =============
    class fetch {
        <<Web API>>
        +(string, Object) Promise~Response~
    }

    class Response {
        <<Web API>>
        +bool ok
        +int status
        +json() Promise~Object~
    }

    class document {
        <<DOM API>>
        +querySelector(string) Element
        +createElement(string) Element
    }

    class Element {
        <<DOM API>>
        +string innerHTML
        +classList: DOMTokenList
        +addEventListener(string, Function)
        +appendChild(Node) Node
    }

    class console {
        <<Console API>>
        +log(...args)
        +error(...args)
    }

    %% ============= RELATIONS =============

    %% Main utilise composants
    Main --> FolderBrowserComp : crée
    Main --> ViewerComp : initialise
    Main --> APIClient : appelle
    Main --> document : manipule DOM
    Main --> console : logs

    %% FolderBrowser utilise API et composants
    FolderBrowserComp --> APIClient : fetchBrowse()
    FolderBrowserComp --> SlideListComp : createSlideList()
    FolderBrowserComp --> document : crée éléments
    FolderBrowserComp --> Element : manipule

    %% Viewer utilise OpenSeadragon et API
    ViewerComp --> OpenSeadragon : appelle factory
    ViewerComp ..> Viewer : retourne
    ViewerComp --> TileSource : configure custom
    ViewerComp --> APIClient : fetchBrowse()
    ViewerComp --> fetch : charge DZI metadata
    ViewerComp --> console : logs

    %% Relations Viewer OpenSeadragon
    Viewer --> TileSource : ouvre
    Viewer --> Viewport : contient
    Viewer --> Viewport : utilise navigation
    TileSource ..> APIClient : génère URLs tiles

    %% SlideList utilise DOM
    SlideListComp --> document : crée éléments
    SlideListComp --> Element : manipule

    %% APIClient utilise fetch
    APIClient --> fetch : requêtes HTTP
    APIClient --> Response : traite réponses
    APIClient --> console : logs erreurs
```

---

## 5. Carte de l'Écosystème Global

### 5.1 Vue Intégrée Backend + Frontend

```mermaid
graph TB
    subgraph "Browser (Client)"
        User[👤 Utilisateur]

        subgraph "JavaScript Components"
            MainJS[main.js<br/>État global + Routing]
            FolderBrowserJS[FolderBrowser.js<br/>Navigation hiérarchique]
            ViewerJS[Viewer.js<br/>Visualisation]
            SlideListJS[SlideList.js<br/>Affichage lames]
            APIJS[api.js<br/>Client HTTP]
        end

        subgraph "External JS Libraries"
            OSD[OpenSeadragon 4.1<br/>Deep Zoom Viewer]
            FetchAPI[Fetch API<br/>HTTP natif]
            DOMAPI[DOM API<br/>Manipulation HTML]
        end
    end

    subgraph "Backend Server (Python)"
        subgraph "FastAPI Layer"
            FastAPIApp[FastAPI App<br/>main.py]
            SlidesRouter[Slides Router<br/>routes/slides.py]
        end

        subgraph "Service Layer"
            FormatDetectorSvc[FormatDetector<br/>Détection formats]
            TileServerSvc[TileServer<br/>Streaming tuiles]
            SlideScannerSvc[SlideScanner<br/>Scan récursif]
            SlideLoaderSvc[SlideLoader<br/>Chargement metadata]
            FolderBrowserSvc[FolderBrowser<br/>Navigation dossiers]
        end

        subgraph "External Python Libraries"
            OpenSlideLib[OpenSlide 4.0.0<br/>Lecture lames]
            PILLib[Pillow 10.x<br/>Traitement images]
            PathlibLib[pathlib<br/>Navigation fichiers]
            HashlibLib[hashlib<br/>Génération IDs]
        end
    end

    subgraph "File System"
        SlidesDir[(Slides Directory<br/>Lames histologiques)]

        subgraph "File Types"
            MRXS[.mrxs + companion/<br/>3DHistech]
            BIF[.bif<br/>Ventana]
            TIF[.tif<br/>Generic TIFF]
            VMS[.vms + .jpg<br/>Hamamatsu]
            Others[.ndpi, .svs, .scn, .czi, ...]
        end
    end

    %% User interactions
    User -->|Click, Navigate, Zoom| MainJS

    %% JS Component interactions
    MainJS --> FolderBrowserJS
    MainJS --> ViewerJS
    FolderBrowserJS --> SlideListJS
    FolderBrowserJS --> APIJS
    ViewerJS --> APIJS
    ViewerJS --> OSD
    APIJS --> FetchAPI

    MainJS --> DOMAPI
    FolderBrowserJS --> DOMAPI
    SlideListJS --> DOMAPI

    %% HTTP Communication
    FetchAPI -->|HTTP GET| FastAPIApp
    FastAPIApp --> SlidesRouter

    %% Backend service calls
    SlidesRouter --> SlideScannerSvc
    SlidesRouter --> SlideLoaderSvc
    SlidesRouter --> FolderBrowserSvc
    SlidesRouter --> TileServerSvc

    SlideScannerSvc --> FormatDetectorSvc
    FolderBrowserSvc --> FormatDetectorSvc

    %% OpenSlide usage
    FormatDetectorSvc --> OpenSlideLib
    TileServerSvc --> OpenSlideLib
    SlideLoaderSvc --> OpenSlideLib

    %% PIL usage
    TileServerSvc --> PILLib
    SlideLoaderSvc --> PILLib

    %% Pathlib & hashlib
    FormatDetectorSvc --> PathlibLib
    FolderBrowserSvc --> PathlibLib
    SlideScannerSvc --> HashlibLib
    FolderBrowserSvc --> HashlibLib

    %% File system access
    OpenSlideLib -->|Lit pixels| SlidesDir
    PathlibLib -->|Parcourt| SlidesDir

    SlidesDir --> MRXS
    SlidesDir --> BIF
    SlidesDir --> TIF
    SlidesDir --> VMS
    SlidesDir --> Others

    %% Styling
    style User fill:#4A90E2,color:#fff
    style MainJS fill:#F5A623
    style OSD fill:#7ED321
    style OpenSlideLib fill:#7ED321
    style SlidesDir fill:#D0021B,color:#fff
```

---

## 6. Flux de Données Détaillés

### 6.1 Flux: Ouverture d'une Lame (Streaming de Tuiles)

```mermaid
sequenceDiagram
    actor User as 👤 Utilisateur
    participant Main as main.js
    participant Browser as FolderBrowser.js
    participant API as api.js
    participant Fetch as Fetch API
    participant Router as slides.py
    participant TileSvr as TileServer
    participant OSL as OpenSlide
    participant FS as File System
    participant Viewer as Viewer.js
    participant OSD as OpenSeadragon

    User->>Main: Clique "Ouvrir"
    Main->>Browser: createFolderBrowser()
    Browser->>API: fetchBrowse("/")
    API->>Fetch: GET /api/slides/browse?path=/
    Fetch->>Router: browse_slides_directory("/")
    Router->>FolderBrowser: browse_directory("/")
    FolderBrowser->>FormatDetector: scan_directory()
    FormatDetector->>FS: glob("**/*")
    FS-->>FormatDetector: [files...]
    FormatDetector->>OSL: detect_format(file)
    OSL->>FS: read headers
    FS-->>OSL: file headers
    OSL-->>FormatDetector: "mirax"
    FormatDetector-->>FolderBrowser: [SlideFormat objects]
    FolderBrowser-->>Router: {folders, slides, files}
    Router-->>Fetch: JSON response
    Fetch-->>API: Response
    API-->>Browser: {folders, slides, files}
    Browser->>SlideList: createSlideList(slides)
    SlideList-->>Browser: HTMLElement
    Browser-->>User: Affiche explorateur + lames

    User->>Browser: Clique sur lame "sample.mrxs"
    Browser->>Main: handleSlideSelect(slide)
    Main->>Viewer: initViewer("viewer")
    Viewer->>OSD: OpenSeadragon(options)
    OSD-->>Viewer: viewer instance
    Viewer-->>Main: viewer

    Main->>API: getSlideInfo(slide.id)
    API->>Fetch: GET /api/slides/{id}/info
    Fetch->>Router: get_slide_info(slide_id)
    Router->>SlideLoader: get_slide_metadata(path)
    SlideLoader->>OSL: OpenSlide(path)
    OSL->>FS: Open .mrxs + companion/
    FS-->>OSL: file handles
    OSL-->>SlideLoader: slide instance
    SlideLoader->>OSL: slide.dimensions, levels, etc.
    OSL-->>SlideLoader: metadata
    SlideLoader->>OSL: slide.close()
    SlideLoader-->>Router: {dimensions, level_count, ...}
    Router-->>Fetch: JSON response
    Fetch-->>API: Response
    API-->>Main: metadata
    Main-->>User: Affiche dimensions

    Main->>Viewer: loadSlideWithTiles(viewer, slide.id)
    Viewer->>Fetch: GET /api/slides/{id}/dzi.json
    Fetch->>Router: get_dzi_metadata(slide_id)
    Router->>TileSvr: get_dzi_metadata(path)
    TileSvr->>OSL: OpenSlide(path)
    OSL->>FS: Open .mrxs + companion/
    FS-->>OSL: file handles
    TileSvr->>OSL: slide.dimensions, levels, downsamples
    OSL-->>TileSvr: metadata
    TileSvr-->>Router: {width, height, levels, ...}
    Router-->>Fetch: JSON response
    Fetch-->>Viewer: DZI metadata

    Viewer->>Viewer: Configure TileSource custom
    Viewer->>OSD: viewer.open(tileSource)
    OSD-->>Viewer: Event 'open'
    Viewer-->>User: Lame ouverte

    loop Pour chaque tuile visible
        OSD->>TileSource: getTileUrl(level, x, y)
        TileSource-->>OSD: URL /api/slides/{id}/tiles/{level}/{x}_{y}.jpg
        OSD->>Fetch: GET tile URL
        Fetch->>Router: get_tile(slide_id, level, col, row)
        Router->>TileSvr: get_tile(path, level, col, row)
        TileSvr->>OSL: read_region(location, level, size)
        OSL->>FS: Read tile data
        FS-->>OSL: pixel data
        OSL-->>TileSvr: PIL.Image RGBA
        TileSvr->>PIL: image.convert('RGB')
        PIL-->>TileSvr: PIL.Image RGB
        TileSvr->>PIL: image.save(buffer, 'JPEG', quality=85)
        PIL-->>TileSvr: JPEG bytes
        TileSvr-->>Router: JPEG bytes
        Router-->>Fetch: Response (image/jpeg)
        Fetch-->>OSD: Image
        OSD->>OSD: Render tile
    end

    OSD-->>User: Affichage complet avec navigation
```

---

### 6.2 Flux: Navigation Hiérarchique

```mermaid
sequenceDiagram
    actor User as 👤 Utilisateur
    participant FB as FolderBrowser.js
    participant API as api.js
    participant Router as slides.py
    participant Browser as folder_browser.py
    participant FD as FormatDetector
    participant OSL as OpenSlide
    participant FS as File System

    User->>FB: Page charge (racine "/")
    FB->>API: fetchBrowse("/")
    API->>Router: GET /api/slides/browse?path=/
    Router->>Browser: browse_directory("/")
    Browser->>Browser: is_safe_path("/") ✓
    Browser->>Browser: Construire chemin absolu
    Browser->>FS: Lire contenu /Slides
    FS-->>Browser: [folders, files]

    loop Pour chaque fichier
        Browser->>FD: detect_format(file)
        FD->>OSL: detect_format(file)
        OSL->>FS: Read file headers
        FS-->>OSL: headers
        OSL-->>FD: format_string

        alt Format supporté
            FD->>OSL: OpenSlide(file) test
            OSL-->>FD: Success
            FD-->>Browser: SlideFormat(is_supported=True)
        else Format non supporté
            FD-->>Browser: SlideFormat(is_supported=False)
        end
    end

    Browser->>Browser: Générer breadcrumb
    Browser->>Browser: Compter items par dossier
    Browser->>Browser: generate_slide_id() pour chaque lame
    Browser-->>Router: {current_path, breadcrumb, folders, slides, files}
    Router-->>API: JSON response
    API-->>FB: data

    FB->>FB: renderBreadcrumb(data.breadcrumb)
    FB->>FB: renderContent(folders, slides, files)
    FB->>SlideList: createSlideList(slides)
    SlideList-->>FB: HTMLElement
    FB-->>User: Affiche explorateur

    User->>FB: Clique sur dossier "3DHistech"
    FB->>API: fetchBrowse("/3DHistech")
    API->>Router: GET /api/slides/browse?path=/3DHistech
    Router->>Browser: browse_directory("/3DHistech")
    Note over Browser: Répète process ci-dessus
    Browser-->>Router: {current_path: "/3DHistech", ...}
    Router-->>API: JSON response
    API-->>FB: data
    FB->>FB: Affiche nouveau contenu
    FB-->>User: Contenu "/3DHistech"

    User->>FB: Clique "Retour" (breadcrumb)
    FB->>API: fetchBrowse("/")
    Note over API,Browser: Répète process
    FB-->>User: Retour à racine
```

---

## 7. Interactions entre Composants

### 7.1 Matrice d'Interactions

| De ↓ / Vers → | FormatDetector | TileServer | OpenSlide | PIL | FastAPI | OpenSeadragon | DOM API |
|---------------|----------------|------------|-----------|-----|---------|---------------|---------|
| **routes/slides.py** | ❌ | ✅ get_tile() | ❌ | ❌ | ❌ (est utilisé par) | ❌ | ❌ |
| **slide_scanner.py** | ✅ scan_directory() | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **slide_loader.py** | ❌ | ❌ | ✅ OpenSlide() | ✅ Image | ❌ | ❌ | ❌ |
| **folder_browser.py** | ✅ detect_format() | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **FormatDetector** | - | ❌ | ✅ detect_format(), OpenSlide() | ❌ | ❌ | ❌ | ❌ |
| **TileServer** | ❌ | - | ✅ read_region() | ✅ convert(), save() | ❌ | ❌ | ❌ |
| **main.js** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ querySelector() |
| **Viewer.js** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ OpenSeadragon() | ❌ |
| **FolderBrowser.js** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ createElement() |
| **api.js** | ❌ | ❌ | ❌ | ❌ | ✅ fetch() | ❌ | ❌ |

### 7.2 Graphe de Dépendances

```mermaid
graph LR
    subgraph "Backend Core"
        Routes[routes/slides.py]
    end

    subgraph "Backend Services"
        Scanner[slide_scanner.py]
        Loader[slide_loader.py]
        Browser[folder_browser.py]
        TileSvr[tile_server.py]
    end

    subgraph "Backend Classes"
        FormatDet[FormatDetector]
    end

    subgraph "External Python"
        OSL[OpenSlide]
        PIL[Pillow]
        Path[pathlib]
        Hash[hashlib]
    end

    subgraph "Frontend Core"
        MainJS[main.js]
    end

    subgraph "Frontend Components"
        ViewerJS[Viewer.js]
        BrowserJS[FolderBrowser.js]
        ListJS[SlideList.js]
        APIJS[api.js]
    end

    subgraph "External JS"
        OSD[OpenSeadragon]
        Fetch[Fetch API]
        DOM[DOM API]
    end

    %% Backend dependencies
    Routes --> Scanner
    Routes --> Loader
    Routes --> Browser
    Routes --> TileSvr

    Scanner --> FormatDet
    Browser --> FormatDet

    FormatDet --> OSL
    FormatDet --> Path

    Loader --> OSL
    Loader --> PIL

    TileSvr --> OSL
    TileSvr --> PIL

    Scanner --> Hash
    Browser --> Hash
    Browser --> Path

    %% Frontend dependencies
    MainJS --> BrowserJS
    MainJS --> ViewerJS
    MainJS --> APIJS
    MainJS --> DOM

    ViewerJS --> OSD
    ViewerJS --> APIJS
    ViewerJS --> Fetch

    BrowserJS --> ListJS
    BrowserJS --> APIJS
    BrowserJS --> DOM

    ListJS --> DOM

    APIJS --> Fetch

    %% HTTP boundary
    APIJS -.->|HTTP| Routes
```

---

## Résumé Quantitatif Final

### Éléments de l'Écosystème

| Catégorie | Count | Détails |
|-----------|-------|---------|
| **Classes Python personnalisées** | 3 | FormatDetector, TileServer, SlideFormat |
| **Fonctions Python personnalisées** | 24 | Routes (6) + Services (18) |
| **Modules Python internes** | 6 | main, config_openslide, routes/slides, services/* |
| **Fonctions JavaScript personnalisées** | 13 | Components (7) + API (4) + Utils (2) |
| **Modules JavaScript internes** | 5 | main, Viewer, FolderBrowser, SlideList, api |
| **Classes externes Python** | 8 | OpenSlide, FastAPI, APIRouter, HTTPException, Response, Image, Path, BytesIO |
| **Objets externes JavaScript** | 6 | OpenSeadragon, Viewer, TileSource, fetch, document, console |
| **Bibliothèques externes** | 6 | OpenSlide, FastAPI, Pillow, OpenSeadragon, pathlib, hashlib |
| **APIs Web natives** | 3 | Fetch API, DOM API, Console API |
| **Formats fichiers supportés** | 12+ | .mrxs, .bif, .tif, .vms, .vmu, .ndpi, .svs, .scn, .czi, .zvi, .dcm, .svslide |
| **Endpoints HTTP** | 6 | list, browse, info, overview, dzi.json, tiles |
| **Events OpenSeadragon** | 4+ | open, viewport-change, tile-loaded, animation-finish |

### Lignes de Code (approximatif)

| Fichier | LOC | Commentaires |
|---------|-----|--------------|
| **Backend** | ~2000 | |
| - format_detector.py | 783 | Détection 12 formats |
| - tile_server.py | 235 | Streaming tuiles |
| - folder_browser.py | 318 | Navigation hiérarchique |
| - slide_scanner.py | 125 | Scan récursif |
| - slide_loader.py | 127 | Chargement metadata |
| - routes/slides.py | 276 | 6 endpoints |
| - main.py | 120 | FastAPI setup |
| **Frontend** | ~900 | |
| - Viewer.js | 203 | OpenSeadragon integration |
| - FolderBrowser.js | 348 | Explorateur dossiers |
| - SlideList.js | 163 | Affichage lames |
| - main.js | 191 | Entry point |
| - api.js | 84 | HTTP client |
| **Total** | ~2900 | Code production |

---

**Prochaine étape:** Utiliser cette cartographie pour planifier l'architecture modulaire des Phases futures (annotations, filtres, IA, etc.)
