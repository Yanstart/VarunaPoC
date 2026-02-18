# Wave 4 — Morphological Clustering (#90 Backend + #92 Frontend)

## Context

Identify morphological pattern types in a slide via embedding clustering.
Enables pathologists to visualize tumor heterogeneity (e.g. Gleason 3 vs 4 vs 5 coexisting).

## Backend (#90): `POST /ml/cluster/{slide_id}?n_clusters=4`

### Service: `ClusteringService`

Two modes:
- **Mock mode** (no embeddings cached): deterministic grid seeded from `hash(slide_path)`. Generates an 8x8 tile grid with random cluster assignments. Dev/test friendly.
- **Real mode** (embeddings in DiskCache): loads `(N, D)` embeddings → `sklearn.cluster.KMeans(n_clusters)` → cluster assignments per tile.

### Response shape (per issue spec)

```json
{
  "clusters": [
    {"id": 0, "color": "#e74c3c", "label": "Cluster A", "tile_count": 120, "centroid_embedding": []},
    {"id": 1, "color": "#2ecc71", "label": "Cluster B", "tile_count": 89, "centroid_embedding": []}
  ],
  "tile_assignments": [
    {"x": 0, "y": 0, "cluster_id": 0},
    {"x": 1, "y": 0, "cluster_id": 1}
  ]
}
```

Mock mode omits `centroid_embedding` (empty list). Real mode includes actual centroid vectors.

### Fixed color palette

```python
CLUSTER_COLORS = ["#e74c3c", "#2ecc71", "#3498db", "#f39c12", "#9b59b6", "#1abc9c", "#e67e22", "#34495e"]
```

## Frontend (#92): ClusteringPanel + ClusteringOverlay

### ClusteringPanel (collapsible accordion)

Same pattern as CellCountingPanel/DetectionPanel:
- **Idle**: `n_clusters` selector (2-8) + "Lancer le clustering" button
- **Loading**: spinner + "Clustering en cours..."
- **Results**: color legend with cluster label, tile count, per-cluster visibility toggle, opacity slider, "Relancer" button

### ClusteringOverlay (canvas on OpenSeadragon)

- Receives `tile_assignments` + `clusters` from panel via event bus
- Creates a canvas overlay sized to the OSD container
- On viewport change: for each tile assignment, compute viewport position, draw colored rectangle with cluster color at global opacity
- Per-cluster toggle: hide/show specific cluster colors
- Opacity slider: controls global overlay opacity (0-1)

### Events

```
CLUSTERING_START, CLUSTERING_COMPLETE, CLUSTERING_ERROR
CLUSTERING_OVERLAY_TOGGLE, CLUSTERING_OVERLAY_OPACITY
```

## Files

| # | File | Action |
|---|------|--------|
| 1 | `backend/services/ml/clustering.py` | CREATE |
| 2 | `backend/routes/ml.py` | MODIFY — models + endpoint |
| 3 | `backend/tests/test_clustering_endpoint.py` | CREATE |
| 4 | `frontend/src/core/Constants.js` | MODIFY — events |
| 5 | `frontend/src/services/ApiService.js` | MODIFY — `clusterSlide()` |
| 6 | `frontend/src/components/ClusteringPanel.js` | CREATE |
| 7 | `frontend/src/components/ClusteringOverlay.js` | CREATE |
| 8 | `frontend/src/css/clustering-panel.css` | CREATE |
| 9 | `frontend/src/css/viewer.css` | MODIFY — import |
| 10 | `frontend/src/main.js` | MODIFY — import + mount + cleanup |
| 11 | `frontend/e2e/helpers/api-mock.js` | MODIFY — mock |
| 12 | `frontend/e2e/tests/16-clustering.spec.js` | CREATE |

## Verification

```bash
cd /data/VarunaPoC/backend && python -m pytest tests/test_clustering_endpoint.py -v
cd /data/VarunaPoC/backend && python -m ruff check routes/ml.py services/ml/clustering.py
cd /data/VarunaPoC/frontend && npx vite build 2>&1 | tail -5
cd /data/VarunaPoC/frontend && npx playwright test e2e/tests/16-clustering.spec.js
cd /data/VarunaPoC/frontend && npx playwright test
```
