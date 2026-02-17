# Wave 4 Clustering Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add morphological clustering backend endpoint and frontend visualization overlay (#90, #92).

**Architecture:** Backend ClusteringService with mock/real modes + FastAPI endpoint. Frontend ClusteringPanel (accordion) + ClusteringOverlay (canvas on OSD). Same patterns as cell counting (Wave 4) and HeatmapOverlay.

**Tech Stack:** Python/FastAPI, scikit-learn (optional, graceful degradation), Vanilla JS, OpenSeadragon canvas overlay, Playwright E2E.

---

### Task 1: Backend ClusteringService

**Files:**
- Create: `backend/services/ml/clustering.py`
- Test: `backend/tests/test_clustering_endpoint.py`

**Step 1: Create `backend/services/ml/clustering.py`**

```python
"""
Morphological Clustering Service — cluster slide embeddings.

Two modes:
- Mock mode (default): Deterministic tile grid seeded from slide path hash.
- Real mode: KMeans on cached embeddings from DiskCache.

Reference: Issue #90 [W4-ML03]
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

CLUSTER_COLORS = [
    "#e74c3c", "#2ecc71", "#3498db", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]


@dataclass
class ClusterInfo:
    id: int
    color: str
    label: str
    tile_count: int
    centroid_embedding: List[float] = field(default_factory=list)


@dataclass
class TileAssignment:
    x: int
    y: int
    cluster_id: int


@dataclass
class ClusterResult:
    clusters: List[ClusterInfo]
    tile_assignments: List[TileAssignment]
    processing_time_ms: float
    metadata: Optional[Dict] = field(default_factory=dict)


class ClusteringService:
    """Morphological clustering service with mock and real modes."""

    def cluster(
        self,
        slide_path: str,
        n_clusters: int = 4,
        disk_cache=None,
        model_id: str = "unknown",
    ) -> ClusterResult:
        start = time.time()

        # Try real mode if embeddings are cached
        if disk_cache is not None:
            embeddings = disk_cache.load_embeddings(
                slide_path.replace("/", "_").replace("\\", "_"),
                model_id,
            )
            if embeddings is not None:
                try:
                    result = self._cluster_real(embeddings, n_clusters)
                    result.processing_time_ms = (time.time() - start) * 1000
                    return result
                except Exception as e:
                    logger.warning("Real clustering failed, falling back to mock: %s", e)

        # Mock mode
        result = self._cluster_mock(slide_path, n_clusters)
        result.processing_time_ms = (time.time() - start) * 1000
        return result

    def _cluster_mock(self, slide_path: str, n_clusters: int) -> ClusterResult:
        """Deterministic mock clustering on an 8x8 tile grid."""
        import random

        seed = int(hashlib.md5(slide_path.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        grid_size = 8
        n_clusters = min(n_clusters, len(CLUSTER_COLORS))

        # Assign each tile to a random cluster
        tile_assignments = []
        counts = [0] * n_clusters
        for y in range(grid_size):
            for x in range(grid_size):
                cid = rng.randint(0, n_clusters - 1)
                tile_assignments.append(TileAssignment(x=x, y=y, cluster_id=cid))
                counts[cid] += 1

        clusters = []
        for i in range(n_clusters):
            clusters.append(ClusterInfo(
                id=i,
                color=CLUSTER_COLORS[i],
                label=f"Cluster {chr(65 + i)}",
                tile_count=counts[i],
                centroid_embedding=[],
            ))

        return ClusterResult(
            clusters=clusters,
            tile_assignments=tile_assignments,
            processing_time_ms=0,
            metadata={"mode": "mock", "grid_size": grid_size},
        )

    def _cluster_real(self, embeddings, n_clusters: int) -> ClusterResult:
        """Real KMeans clustering on embeddings array."""
        import numpy as np

        try:
            from sklearn.cluster import KMeans
        except ImportError:
            raise RuntimeError("scikit-learn not installed — cannot run real clustering")

        n_clusters = min(n_clusters, len(CLUSTER_COLORS), embeddings.shape[0])

        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = km.fit_predict(embeddings)

        # Build grid assuming square-ish layout
        n_tiles = embeddings.shape[0]
        grid_w = int(np.ceil(np.sqrt(n_tiles)))

        tile_assignments = []
        counts = [0] * n_clusters
        for idx in range(n_tiles):
            cid = int(labels[idx])
            tile_assignments.append(TileAssignment(
                x=idx % grid_w,
                y=idx // grid_w,
                cluster_id=cid,
            ))
            counts[cid] += 1

        clusters = []
        for i in range(n_clusters):
            clusters.append(ClusterInfo(
                id=i,
                color=CLUSTER_COLORS[i],
                label=f"Cluster {chr(65 + i)}",
                tile_count=counts[i],
                centroid_embedding=km.cluster_centers_[i].tolist(),
            ))

        return ClusterResult(
            clusters=clusters,
            tile_assignments=tile_assignments,
            processing_time_ms=0,
            metadata={"mode": "real", "n_tiles": n_tiles},
        )
```

**Step 2: Create `backend/tests/test_clustering_endpoint.py`**

```python
"""
Tests for Clustering Service

Markers: @pytest.mark.clustering, @pytest.mark.unit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from services.ml.clustering import ClusteringService, ClusterResult


@pytest.mark.clustering
@pytest.mark.unit
class TestClusteringService:

    def setup_method(self):
        self.service = ClusteringService()

    def test_mock_returns_cluster_result(self):
        result = self.service.cluster("/slides/test.svs")
        assert isinstance(result, ClusterResult)

    def test_mock_default_4_clusters(self):
        result = self.service.cluster("/slides/test.svs")
        assert len(result.clusters) == 4

    def test_mock_custom_n_clusters(self):
        result = self.service.cluster("/slides/test.svs", n_clusters=6)
        assert len(result.clusters) == 6

    def test_mock_cluster_ids_sequential(self):
        result = self.service.cluster("/slides/test.svs")
        ids = [c.id for c in result.clusters]
        assert ids == list(range(len(result.clusters)))

    def test_mock_clusters_have_colors(self):
        result = self.service.cluster("/slides/test.svs")
        for c in result.clusters:
            assert c.color.startswith("#")
            assert len(c.color) == 7

    def test_mock_clusters_have_labels(self):
        result = self.service.cluster("/slides/test.svs")
        labels = [c.label for c in result.clusters]
        assert labels[0] == "Cluster A"
        assert labels[1] == "Cluster B"

    def test_mock_tile_counts_sum_to_total(self):
        result = self.service.cluster("/slides/test.svs")
        total_from_clusters = sum(c.tile_count for c in result.clusters)
        assert total_from_clusters == len(result.tile_assignments)

    def test_mock_tile_grid_8x8(self):
        result = self.service.cluster("/slides/test.svs")
        assert len(result.tile_assignments) == 64

    def test_mock_tile_assignments_have_valid_cluster_ids(self):
        result = self.service.cluster("/slides/test.svs", n_clusters=3)
        for t in result.tile_assignments:
            assert 0 <= t.cluster_id < 3

    def test_mock_is_deterministic(self):
        r1 = self.service.cluster("/slides/test.svs")
        r2 = self.service.cluster("/slides/test.svs")
        ids1 = [(t.x, t.y, t.cluster_id) for t in r1.tile_assignments]
        ids2 = [(t.x, t.y, t.cluster_id) for t in r2.tile_assignments]
        assert ids1 == ids2

    def test_mock_different_slides_differ(self):
        r1 = self.service.cluster("/slides/a.svs")
        r2 = self.service.cluster("/slides/b.svs")
        ids1 = [t.cluster_id for t in r1.tile_assignments]
        ids2 = [t.cluster_id for t in r2.tile_assignments]
        assert ids1 != ids2

    def test_mock_metadata_mode(self):
        result = self.service.cluster("/slides/test.svs")
        assert result.metadata.get("mode") == "mock"

    def test_processing_time_positive(self):
        result = self.service.cluster("/slides/test.svs")
        assert result.processing_time_ms >= 0

    def test_n_clusters_capped_at_8(self):
        result = self.service.cluster("/slides/test.svs", n_clusters=20)
        assert len(result.clusters) == 8
```

**Step 3: Register `clustering` marker in `backend/pyproject.toml`**

Add `"clustering: Clustering tests",` after the `counting` marker line.

**Step 4: Run tests**

```bash
cd /data/VarunaPoC/backend && python3 -m pytest tests/test_clustering_endpoint.py -v
```

Expected: 14 passed.

**Step 5: Lint**

```bash
python3 -m ruff check services/ml/clustering.py tests/test_clustering_endpoint.py
```

---

### Task 2: Backend Route — Pydantic Models + Endpoint

**Files:**
- Modify: `backend/routes/ml.py` — add models after `CountingResponse` (line ~242), add endpoint after `count_cells` (line ~953)

**Step 1: Add Pydantic models after `CountingResponse`**

```python
class ClusterInfoModel(BaseModel):
    id: int
    color: str
    label: str
    tile_count: int
    centroid_embedding: List[float] = []


class TileAssignmentModel(BaseModel):
    x: int
    y: int
    cluster_id: int


class ClusteringResponse(BaseModel):
    clusters: List[ClusterInfoModel]
    tile_assignments: List[TileAssignmentModel]
    processing_time_ms: float
```

**Step 2: Add endpoint after `count_cells` endpoint (before `submit_feedback`)**

```python
@router.post("/cluster/{slide_id}", response_model=ClusteringResponse)
async def cluster_slide(
    slide_id: str,
    n_clusters: int = Query(4, ge=2, le=8, description="Number of clusters"),
    provider=Depends(get_ml_provider),
    disk_cache: DiskCache = Depends(get_disk_cache),
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """
    Clustering morphologique — identifie les patterns dans une lame.

    Utilise KMeans sur les embeddings mis en cache, ou génère des clusters
    mock en mode développement.
    """
    from services.ml.clustering import ClusteringService

    try:
        slide_path = get_slide_path_by_id(slide_id)
        if not slide_path:
            raise HTTPException(status_code=404, detail=f"Slide {slide_id} not found")
        _check_slide_format(slide_path, slide_id)

        model_id = (
            provider.model_config.get("model_id", "unknown")
            if provider.model_loaded
            else "unknown"
        )

        service = ClusteringService()
        result = service.cluster(
            slide_path=slide_path,
            n_clusters=n_clusters,
            disk_cache=disk_cache,
            model_id=model_id,
        )

        return ClusteringResponse(
            clusters=[
                ClusterInfoModel(
                    id=c.id,
                    color=c.color,
                    label=c.label,
                    tile_count=c.tile_count,
                    centroid_embedding=c.centroid_embedding,
                )
                for c in result.clusters
            ],
            tile_assignments=[
                TileAssignmentModel(x=t.x, y=t.y, cluster_id=t.cluster_id)
                for t in result.tile_assignments
            ],
            processing_time_ms=result.processing_time_ms,
        )

    except HTTPException:
        raise
    except MLProviderError as e:
        logger.error(f"Clustering failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Clustering error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Clustering error: {e!s}")
```

**Step 3: Lint**

```bash
python3 -m ruff check routes/ml.py
```

---

### Task 3: Frontend Constants + ApiService

**Files:**
- Modify: `frontend/src/core/Constants.js:108` — add events after cell counting events
- Modify: `frontend/src/services/ApiService.js:699` — add `clusterSlide()` after `countCells()`

**Step 1: Add to Constants.js after line 108 (CELL_COUNTING_ERROR)**

```javascript
    // Clustering events (Wave 4)
    CLUSTERING_START: 'clustering:start',
    CLUSTERING_COMPLETE: 'clustering:complete',
    CLUSTERING_ERROR: 'clustering:error',
    CLUSTERING_OVERLAY_TOGGLE: 'clustering:overlayToggle',
    CLUSTERING_OVERLAY_OPACITY: 'clustering:overlayOpacity',
```

**Step 2: Add to ApiService.js after `countCells()` (line ~699)**

```javascript
    // ==========================================
    // CLUSTERING API (Wave 4)
    // ==========================================

    /**
     * Run morphological clustering on a slide
     * @param {string} slideId - Slide ID
     * @param {Object} [params={}] - Clustering parameters
     * @param {number} [params.n_clusters=4] - Number of clusters (2-8)
     * @returns {Promise<Object>} Clustering result
     */
    async clusterSlide(slideId, params = {}) {
        const queryParams = new URLSearchParams();
        if (params.n_clusters !== undefined) queryParams.set('n_clusters', params.n_clusters);
        const qs = queryParams.toString();
        return this.post(`/api/ml/cluster/${encodeURIComponent(slideId)}${qs ? '?' + qs : ''}`, {});
    }
```

---

### Task 4: Frontend ClusteringPanel

**Files:**
- Create: `frontend/src/components/ClusteringPanel.js`

Follows CellCountingPanel pattern exactly. States: idle → loading → results → error.

- **Idle:** `n_clusters` number input (2-8) + "Lancer le clustering" button
- **Loading:** spinner + "Clustering en cours..."
- **Results:** color legend (colored dot + label + tile count per cluster), per-cluster toggle checkboxes, opacity slider (0-1), "Relancer" button
- **Error:** message + "Réessayer" button

On results received, emits `CLUSTERING_COMPLETE` with the full result so ClusteringOverlay can render.

Toggle checkbox emits `CLUSTERING_OVERLAY_TOGGLE` with `{clusterId, visible}`.
Opacity slider emits `CLUSTERING_OVERLAY_OPACITY` with `{opacity}`.

Has `setSlide(slideId)` and `destroy()` methods matching DetectionPanel/CellCountingPanel.

---

### Task 5: Frontend ClusteringOverlay

**Files:**
- Create: `frontend/src/components/ClusteringOverlay.js`

Follows HeatmapOverlay pattern:
- Creates absolute-positioned canvas overlay inside OSD viewer container
- Listens for `CLUSTERING_COMPLETE` → stores tile_assignments + clusters
- Listens for `CLUSTERING_OVERLAY_TOGGLE` → updates per-cluster visibility Set
- Listens for `CLUSTERING_OVERLAY_OPACITY` → updates canvas opacity
- On OSD `viewport-change` / `animation-finish` / `resize` → re-render visible tiles

Render logic:
1. Get OSD tiledImage bounds
2. Compute tile size = imageBounds.width / grid_width (max x+1 from tile_assignments)
3. For each tile_assignment: if cluster visible, viewport-transform (x * tileW, y * tileH) to viewer element coords, fillRect with cluster color + alpha

Has `destroy()` to remove canvas + event listeners.

Constructor takes `viewerInstance` (same as HeatmapOverlay).

---

### Task 6: Frontend CSS

**Files:**
- Create: `frontend/src/css/clustering-panel.css`
- Modify: `frontend/src/css/viewer.css:10` — add `@import './clustering-panel.css';`

Same styling pattern as `cell-counting-panel.css`:
- `.clustering-panel` — same background/border/radius/width
- `.clustering-panel__header` — same as cell-counting-panel__header
- `.clustering-panel__legend` — vertical list of cluster items
- `.clustering-panel__legend-item` — flex row: color dot + label + count + checkbox
- `.clustering-panel__color-dot` — 12x12 circle with cluster color
- `.clustering-panel__opacity` — range slider
- `.clustering-panel__spinner` — same keyframe pattern

---

### Task 7: Frontend main.js Integration

**Files:**
- Modify: `frontend/src/main.js`

**Imports (after line 49):**
```javascript
import { ClusteringPanel } from './components/ClusteringPanel.js';
import { ClusteringOverlay } from './components/ClusteringOverlay.js';
```

**appState (after line 98 `cellCountingPanel`):**
```javascript
    clusteringPanel: null,
    clusteringOverlay: null,
```

**Mount in `showViewerPage()` — after cellCountingPanel creation (line ~423):**
```javascript
            // Wave 4: Clustering Panel
            const clusteringContainer = document.createElement('div');
            clusteringContainer.id = 'clustering-panel-container';
            clusteringContainer.style.marginTop = '8px';
            mlContainer2.appendChild(clusteringContainer);
            appState.clusteringPanel = new ClusteringPanel(clusteringContainer, { slideId: slide.id });
```

**Mount ClusteringOverlay after HeatmapOverlay (find where heatmapOverlay is created):**
```javascript
    // Wave 4: Clustering Overlay
    if (appState.viewer) {
        appState.clusteringOverlay = new ClusteringOverlay(appState.viewer);
    }
```

**handleSlideSwitch (after line 755 cellCountingPanel.setSlide):**
```javascript
    // 9. Reset clustering panel for new slide
    if (appState.clusteringPanel && appState.clusteringPanel.setSlide) {
        appState.clusteringPanel.setSlide(newSlide.id);
    }
    // 10. Reset clustering overlay for new slide
    if (appState.clusteringOverlay && appState.clusteringOverlay.clear) {
        appState.clusteringOverlay.clear();
    }
```

**cleanup (after cellCountingPanel destroy, line ~859):**
```javascript
    if (appState.clusteringPanel) {
        appState.clusteringPanel.destroy();
        appState.clusteringPanel = null;
    }
    if (appState.clusteringOverlay) {
        appState.clusteringOverlay.destroy();
        appState.clusteringOverlay = null;
    }
```

---

### Task 8: E2E Tests

**Files:**
- Modify: `frontend/e2e/helpers/api-mock.js` — add `mockClustering()` + add to `setupFullMocks()`
- Create: `frontend/e2e/tests/16-clustering.spec.js`

**api-mock.js — add before `setupFullMocks()`:**

```javascript
export async function mockClustering(page) {
    await page.route('**/api/ml/cluster/*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                clusters: [
                    { id: 0, color: '#e74c3c', label: 'Cluster A', tile_count: 20, centroid_embedding: [] },
                    { id: 1, color: '#2ecc71', label: 'Cluster B', tile_count: 22, centroid_embedding: [] },
                    { id: 2, color: '#3498db', label: 'Cluster C', tile_count: 12, centroid_embedding: [] },
                    { id: 3, color: '#f39c12', label: 'Cluster D', tile_count: 10, centroid_embedding: [] },
                ],
                tile_assignments: Array.from({ length: 64 }, (_, i) => ({
                    x: i % 8, y: Math.floor(i / 8), cluster_id: i % 4,
                })),
                processing_time_ms: 1500,
            }),
        }),
    );
}
```

Add `await mockClustering(page);` to `setupFullMocks()`.

**16-clustering.spec.js:**

```javascript
import { test, expect } from '../fixtures/base.js';
import { setupFullMocks } from '../helpers/api-mock.js';

test.describe('Clustering Panel', () => {
    test.beforeEach(async ({ page, mockSlideData }) => {
        await setupFullMocks(page, mockSlideData);
        await page.goto('/');
        await page.waitForSelector('.folder-browser');
    });

    test('no errors on page load with clustering mocked', async ({ page }) => {
        const errors = [];
        page.on('pageerror', (err) => errors.push(err.message));
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }
        const clusterErrors = errors.filter(
            (e) => e.includes('Clustering') || e.includes('clustering') || e.includes('cluster'),
        );
        expect(clusterErrors).toHaveLength(0);
    });

    test('panel is present in ML container', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }
        const panel = page.locator('.clustering-panel');
        await expect(panel).toBeAttached();
    });

    test('panel header shows Clustering morphologique', async ({ page }) => {
        const firstSlide = page.locator('.slide-item').first();
        if (await firstSlide.isVisible()) {
            await firstSlide.click();
            await page.waitForTimeout(1500);
        }
        const header = page.locator('.clustering-panel__title');
        await expect(header).toHaveText('Clustering morphologique');
    });
});
```

---

### Task 9: Verification

```bash
# Backend tests
cd /data/VarunaPoC/backend && python3 -m pytest tests/test_clustering_endpoint.py -v

# Backend lint
python3 -m ruff check routes/ml.py services/ml/clustering.py
python3 -m black --check routes/ml.py services/ml/clustering.py
python3 -m isort --check-only routes/ml.py services/ml/clustering.py

# Frontend build
cd /data/VarunaPoC/frontend && npx vite build 2>&1 | tail -5

# E2E clustering tests
npx playwright test e2e/tests/16-clustering.spec.js --config=e2e/playwright.config.js --project=chromium

# Full E2E regression
npx playwright test --config=e2e/playwright.config.js --project=chromium

# Pytest collection (no import errors)
cd /data/VarunaPoC/backend && python3 -m pytest --co -q
```

---

### Task 10: Commit

```bash
git add backend/services/ml/clustering.py backend/routes/ml.py \
  backend/tests/test_clustering_endpoint.py backend/pyproject.toml \
  frontend/src/core/Constants.js frontend/src/services/ApiService.js \
  frontend/src/components/ClusteringPanel.js frontend/src/components/ClusteringOverlay.js \
  frontend/src/css/clustering-panel.css frontend/src/css/viewer.css \
  frontend/src/main.js frontend/e2e/helpers/api-mock.js \
  frontend/e2e/tests/16-clustering.spec.js

git commit -m "feat(wave4): add morphological clustering backend + frontend (#90, #92)"
```
