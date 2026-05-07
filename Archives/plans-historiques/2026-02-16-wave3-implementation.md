# Wave 3 — Le cas, pas le fichier — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform navigation from file-centric to case-centric, add similarity search, and build feedback aggregation.

**Architecture:** Frontend-heavy wave. Case concept = folder grouping (existing `/api/slides/browse` already returns slides per folder). New FAISS index service for vector similarity. FeedbackCollector aggregates corrections with sliding window stats.

**Tech Stack:** Vanilla JS (DOM), FAISS (via faiss-cpu), FastAPI BackgroundTasks, existing cachetools/DiskCache

---

## Parallel Groups

| Group | Issues | Domain | Agent |
|-------|--------|--------|-------|
| A | #69, #76, #72, #75 | UX (case navigation) | Frontend |
| B | #78, #80, #82 | ML (similarity search) | Full-stack |
| C | #84 | Infra (feedback collector) | Backend |

Dependencies: A1→A2, A1→A3→A4 (within A). B1→B2→B3 (within B). C1 independent.

---

## Group A: Case-Centric Navigation

### Task A1: Case concept in Home — group slides by parent folder (#69)

**Files:**
- Create: `frontend/src/components/CaseBrowser.js`
- Create: `frontend/src/css/case-browser.css`
- Modify: `frontend/src/main.js` (import + use CaseBrowser)
- Modify: `frontend/src/style.css` (import case-browser.css)
- Modify: `frontend/src/core/Constants.js` (add CASE events)

**What to build:**

`CaseBrowser.js` — new component replacing FolderBrowser as default Home view. Calls `apiService.browse('/')` and groups slides by parent folder into "case cards".

```javascript
// CaseBrowser exports:
export function createCaseBrowser(onSlideSelect, onCaseSelect)

// Internal state:
// - cases: Array<{ name, path, slides: [], stains: [], lastModified }>
// - Built from browse API: folders become cases, slides within each folder are grouped

// DOM structure:
// .case-browser
//   .browser-header (reuse exact same header as FolderBrowser: title + search + file picker)
//   .case-browser__grid
//     .case-card (for each case/folder)
//       .case-card__name  → folder name (e.g. "2024-0847")
//       .case-card__meta  → "3 lames — H&E, CK5/6, P63"
//       .case-card__date  → last modified date
//       .case-card__slides-preview  → mini slide list (collapsed)
```

**Case grouping logic:**
1. Call `apiService.browse('/')` to get root folders
2. For each folder with `item_count > 0`, call `apiService.browse(folder.path)` to get its slides
3. Group: `{ name: folder.name, path: folder.path, slides: [...], stains: slides.map(s => extractStain(s.name)) }`
4. `extractStain(name)` — parse stain from filename: look for "HE", "H&E", "CK5", "P63", "Ki67" etc. in the stem

**Stain extraction helper** (inline in CaseBrowser):
```javascript
function extractStain(slideName) {
    const stem = slideName.replace(/\.[^.]+$/, '').toUpperCase();
    const stains = ['H&E', 'HE', 'CK5', 'CK5/6', 'CK7', 'CK20', 'P63', 'P53', 'KI67', 'KI-67',
                    'HER2', 'ER', 'PR', 'PD-L1', 'CD3', 'CD20', 'CD45', 'PAS', 'MASSON'];
    return stains.find(s => stem.includes(s.replace(/[/-]/g, ''))) || null;
}
```

**Search:** Filter cases by name (reuse search input pattern from FolderBrowser).

**Click behavior:** Click case card → call `onCaseSelect(caseData)` which will be handled by Task A3.

**`case-browser.css`** — Dark theme matching existing `.folder-browser` and `.folder-card` styles:
- `.case-browser` — full screen, black background (#000)
- `.case-browser__grid` — CSS grid auto-fill minmax(280px, 1fr), gap 16px
- `.case-card` — dark card (#1a1a1a), rounded, border #333, hover glow
- `.case-card__name` — 16px bold, #e0e0e0
- `.case-card__meta` — 12px, #888, stain pills (small colored badges)
- `.case-card__date` — 11px, #666

**Constants.js additions:**
```javascript
CASE_SELECTED: 'ui:caseSelected',
CASE_SLIDE_SWITCH: 'case:slideSwitch',
```

**main.js changes:**
- Import `createCaseBrowser`
- In `showHomePage()`: check `localStorage.getItem('varuna_home_view')`:
  - If `'explorer'` → use existing `createFolderBrowser`
  - Else (default `'cases'`) → use `createCaseBrowser`
- Pass both `onSlideSelect` and `onCaseSelect` callbacks

---

### Task A2: Home redesign — case view default + toggle (#76)

**Files:**
- Modify: `frontend/src/components/CaseBrowser.js` (add toggle button)
- Modify: `frontend/src/components/FolderBrowser.js` (add toggle button)
- Modify: `frontend/src/main.js` (toggle logic)
- Modify: `frontend/src/css/case-browser.css` (toggle button styles)

**What to build:**

Add a toggle button in both CaseBrowser and FolderBrowser headers to switch between views.

**In CaseBrowser header** (after search box):
```javascript
const toggleBtn = document.createElement('button');
toggleBtn.className = 'view-toggle-btn';
toggleBtn.textContent = 'Explorateur';
toggleBtn.title = 'Basculer vers la vue explorateur de fichiers';
toggleBtn.addEventListener('click', () => {
    localStorage.setItem('varuna_home_view', 'explorer');
    // Emit event to trigger view switch
    if (onViewToggle) onViewToggle('explorer');
});
```

**In FolderBrowser header** (after search box):
```javascript
const toggleBtn = document.createElement('button');
toggleBtn.className = 'view-toggle-btn';
toggleBtn.textContent = 'Mes cas';
toggleBtn.title = 'Basculer vers la vue par cas';
toggleBtn.addEventListener('click', () => {
    localStorage.setItem('varuna_home_view', 'cases');
    if (onViewToggle) onViewToggle('cases');
});
```

**main.js `showHomePage()` updated:**
```javascript
function showHomePage() {
    const app = document.getElementById('app');
    app.textContent = '';

    const viewPref = localStorage.getItem('varuna_home_view') || 'cases';

    function handleViewToggle(newView) {
        showHomePage(); // Re-render with new preference
    }

    if (viewPref === 'explorer') {
        appState.folderBrowser = createFolderBrowser(handleSlideSelect, handleViewToggle);
        app.appendChild(appState.folderBrowser);
    } else {
        const caseBrowser = createCaseBrowser(handleSlideSelect, handleCaseSelect, handleViewToggle);
        app.appendChild(caseBrowser);
    }
}
```

**CSS for toggle button:**
```css
.view-toggle-btn {
    padding: 6px 14px;
    font-size: 12px;
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 6px;
    color: #e0e0e0;
    cursor: pointer;
    transition: all 0.15s ease;
}
.view-toggle-btn:hover {
    border-color: #4a9eff;
    color: #4a9eff;
}
```

---

### Task A3: Case sidebar in viewer — list slides from same case (#72)

**Files:**
- Create: `frontend/src/components/CaseSidebar.js`
- Create: `frontend/src/css/case-sidebar.css`
- Modify: `frontend/src/main.js` (wire sidebar into viewer page)
- Modify: `frontend/src/style.css` (import case-sidebar.css)

**What to build:**

`CaseSidebar.js` — right sidebar in viewer showing sibling slides from the same case.

```javascript
// Exports:
export class CaseSidebar {
    constructor(container, options = {})
    // options: { onSlideSwitch: (slide) => void }

    setCase(casePath, slides, activeSlideId)
    // casePath: parent folder path
    // slides: array of sibling slides
    // activeSlideId: currently viewed slide

    setActiveSlide(slideId)
    // Update active indicator without refetching

    destroy()
}
```

**DOM structure:**
```
.case-sidebar
  .case-sidebar__header
    .case-sidebar__title  → "Cas: {folderName}" (bold, 14px)
    .case-sidebar__count  → "{n} lames" (12px, #888)
  .case-sidebar__list
    .case-sidebar__item (for each slide)
      .case-sidebar__dot  → filled circle (active) or empty circle
      .case-sidebar__name → slide filename (truncated)
      .case-sidebar__stain → stain badge (if detected)
    .case-sidebar__item.is-active
      → blue left border, filled dot, bold name
```

**Click behavior:**
- Click slide item → call `options.onSlideSwitch(slide)` (handled by Task A4)
- Active slide has `.is-active` class

**How to get sibling slides:**
The case info (path + slides) is passed when navigating from CaseBrowser. If user navigates from FolderBrowser or deep link, extract parent path from slide info and call `apiService.browse(parentPath)`.

**main.js viewer page layout change:**
```
viewer-page
  ├── viewer-header (existing)
  ├── viewer-body (NEW flex container)
  │   ├── viewer-main (existing viewer area, flex: 1)
  │   └── case-sidebar (width: 220px, collapsible)
```

**`case-sidebar.css`:**
- `.case-sidebar` — width: 220px, background: #111, border-left: 1px solid #333, overflow-y: auto
- `.case-sidebar__item` — padding: 10px 12px, cursor: pointer, hover: #1a1a1a
- `.case-sidebar__item.is-active` — border-left: 3px solid #4a9eff, background: rgba(74,158,255,0.08)
- `.case-sidebar__dot` — 8px circle, border: 2px solid #555 (empty) or background: #4a9eff (active)
- `.case-sidebar__stain` — small pill badge, 10px font

---

### Task A4: Rapid intra-case switch (#75)

**Files:**
- Modify: `frontend/src/main.js` (slide switching logic)
- Modify: `frontend/src/components/CaseSidebar.js` (update active state)

**What to build:**

When user clicks a slide in the CaseSidebar, switch the viewer to that slide without navigating back to Home.

**In main.js `showViewerPage()`:**
```javascript
function handleSlideSwitch(newSlide) {
    // 1. Update app state
    appState.selectedSlide = newSlide;

    // 2. Update viewer header title
    const titleEl = document.querySelector('.viewer-title');
    if (titleEl) titleEl.textContent = newSlide.name;

    // 3. Reload viewer with new slide
    if (appState.viewer) {
        // Destroy old OSD tile source
        appState.viewer.close();
    }
    loadSlide(newSlide); // existing function that loads DZI + tiles

    // 4. Update sidebar active indicator
    if (appState.caseSidebar) {
        appState.caseSidebar.setActiveSlide(newSlide.id);
    }

    // 5. Reload annotations for new slide
    annotationStore.loadAnnotations(newSlide.id);
}
```

**Key requirements:**
- Previous TileSource properly destroyed (OSD `.close()` or `.open()` with new source)
- Viewport resets to overview zoom
- Annotations reload for new slide
- ML panels reset (call `setSlide(newSlide.id)` on all sub-panels)
- No page navigation (no `showHomePage()` → `showViewerPage()` cycle)

**E2E test** (`frontend/e2e/tests/14-case-navigation.spec.js`):
- Mock browse API to return a folder with 3 slides
- Navigate to slide → verify sidebar shows 3 items
- Verify active slide indicator
- Click second slide → verify title changes

---

## Group B: Similarity Search

### Task B1: FAISS vector index service (#78)

**Files:**
- Create: `backend/services/ml/similarity_index.py`
- Create: `backend/tests/test_similarity_index.py`
- Modify: `backend/requirements.txt` (add faiss-cpu)

**What to build:**

`SimilarityIndex` class managing a FAISS index for slide-level embeddings.

```python
# backend/services/ml/similarity_index.py

import numpy as np
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Optional FAISS import (graceful degradation)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not installed — similarity search disabled")


class SimilarityIndex:
    """FAISS-based vector index for slide similarity search.

    Stores mean-pooled slide embeddings (one vector per slide).
    Uses cosine similarity via inner product on L2-normalized vectors.

    Index files:
        {index_dir}/faiss_slide_index.bin  — FAISS IndexFlatIP
        {index_dir}/faiss_slide_ids.json   — ordered list of slide IDs
    """

    def __init__(self, index_dir: str = "/tmp/varuna_cache/ml/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index = None        # faiss.IndexFlatIP
        self.slide_ids = []      # list[str], same order as index
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index from disk, or create empty one."""
        index_path = self.index_dir / "faiss_slide_index.bin"
        ids_path = self.index_dir / "faiss_slide_ids.json"

        if index_path.exists() and ids_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(ids_path) as f:
                self.slide_ids = json.load(f)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} slides")
        else:
            # Will be initialized on first add (need to know embedding dim)
            self.index = None
            self.slide_ids = []

    def add_slide(self, slide_id: str, embeddings: np.ndarray):
        """Add a slide to the index.

        Args:
            slide_id: Unique slide identifier
            embeddings: Shape (N, D) patch-level embeddings.
                       Mean-pooled to single (1, D) vector.
        """
        if slide_id in self.slide_ids:
            return  # Already indexed

        # Mean-pool patch embeddings to slide-level vector
        slide_vector = embeddings.mean(axis=0, keepdims=True).astype(np.float32)
        # L2-normalize for cosine similarity via inner product
        faiss.normalize_L2(slide_vector)

        if self.index is None:
            dim = slide_vector.shape[1]
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(slide_vector)
        self.slide_ids.append(slide_id)

    def search(self, query_embeddings: np.ndarray, top_k: int = 5,
               exclude_id: str = None) -> list[dict]:
        """Search for similar slides.

        Args:
            query_embeddings: Shape (N, D) patch-level, or (1, D) slide-level.
            top_k: Number of results to return.
            exclude_id: Slide ID to exclude (the query slide itself).

        Returns:
            List of {slide_id: str, score: float} sorted by descending score.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        # Mean-pool if multi-patch
        if query_embeddings.ndim == 2 and query_embeddings.shape[0] > 1:
            query = query_embeddings.mean(axis=0, keepdims=True).astype(np.float32)
        else:
            query = query_embeddings.reshape(1, -1).astype(np.float32)

        faiss.normalize_L2(query)

        # Search more than needed in case we exclude one
        k = min(top_k + 1, self.index.ntotal)
        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.slide_ids):
                continue
            sid = self.slide_ids[idx]
            if sid == exclude_id:
                continue
            results.append({"slide_id": sid, "score": float(score)})
            if len(results) >= top_k:
                break

        return results

    def save(self):
        """Persist index to disk."""
        if self.index is None:
            return
        faiss.write_index(self.index, str(self.index_dir / "faiss_slide_index.bin"))
        with open(self.index_dir / "faiss_slide_ids.json", "w") as f:
            json.dump(self.slide_ids, f)

    def size(self) -> int:
        """Number of indexed slides."""
        return self.index.ntotal if self.index else 0

    @property
    def is_available(self) -> bool:
        return FAISS_AVAILABLE
```

**Tests** (`test_similarity_index.py`):
```python
# 4 tests:
# test_add_and_search — add 5 slides, search for most similar, verify order
# test_exclude_self — search with exclude_id, verify query slide not in results
# test_save_and_reload — save index, create new instance, verify persistence
# test_empty_index — search on empty index returns []
```

**requirements.txt addition:**
```
faiss-cpu>=1.7.4
```

---

### Task B2: Similarity endpoint — POST /ml/similar/{slide_id} (#80)

**Files:**
- Modify: `backend/routes/ml.py` (add endpoint + Pydantic models)
- Modify: `frontend/src/services/ApiService.js` (add getSimilarSlides method)
- Create: `backend/tests/test_similarity_endpoint.py`

**What to build:**

**Pydantic models** (in ml.py, near other models):
```python
class SimilarityRequest(BaseModel):
    region: Optional[RegionRequest] = None  # Optional sub-region

class SimilarSlideResult(BaseModel):
    slide_id: str
    score: float = Field(..., ge=0, le=1)
    name: Optional[str] = None
    overview_url: Optional[str] = None

class SimilarityResponse(BaseModel):
    query_slide_id: str
    results: List[SimilarSlideResult]
    index_size: int
```

**Endpoint** (after feedback endpoint):
```python
# Singleton for similarity index
_similarity_index = None

def get_similarity_index():
    global _similarity_index
    if _similarity_index is None:
        from services.ml.similarity_index import SimilarityIndex, FAISS_AVAILABLE
        if not FAISS_AVAILABLE:
            raise HTTPException(503, "Similarity search unavailable (faiss-cpu not installed)")
        _similarity_index = SimilarityIndex()
    return _similarity_index

@router.post("/similar/{slide_id}", response_model=SimilarityResponse)
async def search_similar(
    slide_id: str,
    request: SimilarityRequest = SimilarityRequest(),
    top_k: int = Query(5, ge=1, le=20),
):
    """Find the K most similar slides to the given slide."""
    index = get_similarity_index()

    # Get query embeddings from disk cache
    disk_cache = DiskCache()
    model = os.getenv("ML_EXTRACTOR", "ctranspath")
    embeddings = disk_cache.load_embeddings(slide_id, model)

    if embeddings is None:
        raise HTTPException(404, f"No embeddings cached for slide {slide_id}")

    results = index.search(embeddings, top_k=top_k, exclude_id=slide_id)

    # Enrich with slide names and overview URLs
    for r in results:
        r["name"] = r["slide_id"].split("/")[-1] if "/" in r["slide_id"] else r["slide_id"]
        r["overview_url"] = f"/api/slides/{r['slide_id']}/overview"

    return SimilarityResponse(
        query_slide_id=slide_id,
        results=[SimilarSlideResult(**r) for r in results],
        index_size=index.size(),
    )
```

**ApiService.js addition:**
```javascript
async getSimilarSlides(slideId, options = {}) {
    const params = new URLSearchParams();
    if (options.topK) params.set('top_k', options.topK);
    const query = params.toString() ? `?${params}` : '';
    return this.post(`/api/ml/similar/${encodeURIComponent(slideId)}${query}`, options.region || {});
}
```

**Tests:** 3 tests with mocked DiskCache and SimilarityIndex.

---

### Task B3: SimilarityPanel frontend (#82)

**Files:**
- Create: `frontend/src/components/SimilarityPanel.js`
- Create: `frontend/src/css/similarity-panel.css`
- Modify: `frontend/src/components/ViewerPanel.js` (wire SimilarityPanel)
- Modify: `frontend/src/style.css` (import similarity-panel.css)
- Modify: `frontend/e2e/helpers/api-mock.js` (add similarity mock)

**What to build:**

`SimilarityPanel.js` — accordion panel showing thumbnail gallery of similar slides.

```javascript
class SimilarityPanel {
    constructor(container, options = {})
    // State: slideId, isCollapsed=true, isLoading, results=[]

    setSlide(slideId)
    _loadSimilar()       // POST /ml/similar/{slideId}
    _renderResults()     // Thumbnail grid with scores
    _renderError(msg)
    _toggleCollapse()
    destroy()
}
```

**DOM structure:**
```
.similarity-panel
  .similarity-panel__header.similarity-panel__header--collapsible
    span.similarity-panel__title  "Lames similaires"
    span.similarity-panel__chevron  ">"
  .similarity-panel__body
    button "Rechercher"  (triggers _loadSimilar)
    .similarity-panel__grid  (results)
      .similarity-panel__card (for each result)
        img (overview thumbnail, 80x60)
        .similarity-panel__card-name  (slide name, truncated)
        .similarity-panel__card-score  (similarity %, colored badge)
```

**Click behavior:** Click thumbnail → `window.open('/slide/' + slideId, '_blank')` (open in new tab via PACS deep link).

**CSS:** Grid layout 2 columns, dark theme matching other panels. Thumbnail cards with rounded corners, hover glow.

**ViewerPanel wiring:** Same pattern as FocusAssistPanel — lazy init in `_toggleMLPanel()`, `setSlide()` on load, `destroy()` on cleanup.

**E2E mock:**
```javascript
export async function mockMLSimilarity(page) {
    await page.route('**/api/ml/similar/*', route =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                query_slide_id: 'test-slide-001',
                results: [
                    { slide_id: 'slide-002', score: 0.94, name: 'Case_B_HE.svs', overview_url: '/api/slides/slide-002/overview' },
                    { slide_id: 'slide-003', score: 0.87, name: 'Case_C_HE.svs', overview_url: '/api/slides/slide-003/overview' },
                ],
                index_size: 50,
            }),
        }),
    );
}
```

---

## Group C: FeedbackCollector Service

### Task C1: FeedbackCollector — aggregation + thresholds (#84)

**Files:**
- Create: `backend/services/feedback_collector.py`
- Create: `backend/tests/test_feedback_collector.py`
- Modify: `backend/routes/ml.py` (add GET /ml/feedback/stats endpoint)

**What to build:**

`FeedbackCollector` class that aggregates pathologist corrections with sliding window stats.

```python
# backend/services/feedback_collector.py

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Configurable thresholds
FEEDBACK_RETRAIN_THRESHOLD = 100   # corrections before suggesting retrain
FEEDBACK_REJECTION_ALERT = 0.3     # 30% rejection rate triggers alert
FEEDBACK_WINDOW_DAYS = 7           # sliding window size


@dataclass
class FeedbackStats:
    """Aggregated feedback statistics for a model."""
    model_name: str
    window_days: int
    total_corrections: int
    confirmed: int
    rejected: int
    refined: int
    relabeled: int
    rejection_rate: float         # rejected / total
    needs_retrain: bool           # total >= threshold
    high_rejection: bool          # rejection_rate >= alert threshold
    computed_at: str              # ISO timestamp


class FeedbackCollector:
    """Aggregates pathologist corrections and computes threshold alerts.

    Reads from the corrections table with a sliding window
    (last N days) grouped by model_name.
    """

    def __init__(
        self,
        retrain_threshold: int = FEEDBACK_RETRAIN_THRESHOLD,
        rejection_alert: float = FEEDBACK_REJECTION_ALERT,
        window_days: int = FEEDBACK_WINDOW_DAYS,
    ):
        self.retrain_threshold = retrain_threshold
        self.rejection_alert = rejection_alert
        self.window_days = window_days

    async def get_stats(self, db_session, model_name: str = None) -> list[FeedbackStats]:
        """Compute sliding-window stats per model.

        Args:
            db_session: AsyncSession
            model_name: Optional filter for specific model

        Returns:
            List of FeedbackStats, one per model_name
        """
        from models.correction import Correction
        from sqlalchemy import select, func, case

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.window_days)

        query = (
            select(
                Correction.model_name,
                func.count(Correction.id).label("total"),
                func.sum(case((Correction.correction_type == "confirmed", 1), else_=0)).label("confirmed"),
                func.sum(case((Correction.correction_type == "rejected", 1), else_=0)).label("rejected"),
                func.sum(case((Correction.correction_type == "refined", 1), else_=0)).label("refined"),
                func.sum(case((Correction.correction_type == "relabeled", 1), else_=0)).label("relabeled"),
            )
            .where(Correction.created_at >= cutoff)
            .group_by(Correction.model_name)
        )

        if model_name:
            query = query.where(Correction.model_name == model_name)

        result = await db_session.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            total = row.total or 0
            rejected = row.rejected or 0
            rejection_rate = rejected / total if total > 0 else 0.0

            stats.append(FeedbackStats(
                model_name=row.model_name or "unknown",
                window_days=self.window_days,
                total_corrections=total,
                confirmed=row.confirmed or 0,
                rejected=rejected,
                refined=row.refined or 0,
                relabeled=row.relabeled or 0,
                rejection_rate=round(rejection_rate, 4),
                needs_retrain=total >= self.retrain_threshold,
                high_rejection=rejection_rate >= self.rejection_alert,
                computed_at=datetime.now(timezone.utc).isoformat(),
            ))

        return stats
```

**New endpoint** (in ml.py):
```python
@router.get("/feedback/stats")
async def get_feedback_stats(
    model_name: str = Query(None),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Get aggregated feedback statistics per model."""
    from services.feedback_collector import FeedbackCollector
    from core.database import get_db_context

    collector = FeedbackCollector()
    async with get_db_context() as session:
        stats = await collector.get_stats(session, model_name=model_name)

    return {
        "stats": [
            {
                "model_name": s.model_name,
                "window_days": s.window_days,
                "total_corrections": s.total_corrections,
                "confirmed": s.confirmed,
                "rejected": s.rejected,
                "refined": s.refined,
                "relabeled": s.relabeled,
                "rejection_rate": s.rejection_rate,
                "needs_retrain": s.needs_retrain,
                "high_rejection": s.high_rejection,
            }
            for s in stats
        ]
    }
```

**Tests** (`test_feedback_collector.py`):
```python
# 4 tests using mocked DB session:
# test_empty_stats — no corrections → empty list
# test_aggregation — insert 10 corrections (5 confirmed, 3 rejected, 2 refined) → verify counts
# test_retrain_threshold — 100+ corrections → needs_retrain=True
# test_rejection_alert — >30% rejected → high_rejection=True
```

---

## Post-Implementation Tasks

### Task E1: E2E tests and mocks update

**Files:**
- Create: `frontend/e2e/tests/14-case-navigation.spec.js`
- Modify: `frontend/e2e/helpers/api-mock.js` (add similarity mock to setupFullMocks)

### Verification

```bash
# Backend tests
cd backend && python3 -m pytest tests/test_similarity_index.py tests/test_similarity_endpoint.py tests/test_feedback_collector.py -v

# Frontend lint
cd frontend && npx eslint src/components/CaseBrowser.js src/components/CaseSidebar.js src/components/SimilarityPanel.js

# E2E (if browsers installed)
cd frontend && npx playwright test e2e/tests/14-case-navigation.spec.js
```
