# Wave 1 — Le viewer qui parle pathologiste — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the viewer from a tech prototype into a tool that speaks the pathologist's language — French terminology, predefined labels, polished UX, and backend infrastructure for Wave 2.

**Architecture:** Vanilla JS frontend (EventBus pub/sub, OpenSeadragon) + FastAPI backend (SQLAlchemy AsyncIO, PostgreSQL/PostGIS, Alembic). No framework — direct DOM manipulation. All UI strings hardcoded in components (no i18n system).

**Tech Stack:** JavaScript (vanilla), OpenSeadragon, FastAPI, SQLAlchemy, Alembic, PostgreSQL, cachetools, numpy

---

## Parallelization Strategy

Tasks are organized into 4 independent groups that can run in parallel:

| Group | Tasks | Description |
|-------|-------|-------------|
| A | 1, 7, 8 | Quick wins (config change, badges, counting) |
| B | 2, 3 | FR Terminology + predefined labels |
| C | 4, 5, 6 | UX structural (accordion, magnification, toolbar) |
| D | 9, 10, 11 | Backend infrastructure (corrections table, caches) |

Within each group, tasks are sequential.

---

## Task 1: W1-UX04 — Sync pan/zoom active par defaut (#63)

**Files:**
- Modify: `frontend/src/core/Constants.js:199`
- Test: `frontend/e2e/tests/viewer.spec.js`

**Step 1: Change the default**

In `frontend/src/core/Constants.js`, line 199, change:
```js
ENABLED_BY_DEFAULT: false,
```
to:
```js
ENABLED_BY_DEFAULT: true,
```

**Step 2: Verify E2E tests still pass**

Run: `cd frontend && npx playwright test e2e/tests/viewer.spec.js --reporter=list`
Expected: All existing viewer tests PASS (sync behavior may change in compare mode)

**Step 3: Commit**

```bash
git add frontend/src/core/Constants.js
git commit -m "feat(ux): enable sync pan/zoom by default in compare mode (#63)"
```

---

## Task 2: W1-UX01 — Terminologie FR pathologiste (#60)

**Files:**
- Modify: `frontend/src/components/MLPanel.js`
- Modify: `frontend/src/components/DetectionPanel.js`
- Modify: `frontend/src/components/CountingPanel.js`
- Modify: `frontend/src/components/QualityPanel.js`
- Modify: `frontend/src/components/LayerManager.js`
- Modify: `frontend/src/components/DrawingTools.js`
- Modify: `frontend/src/components/ViewerPanel.js`
- Modify: `frontend/src/components/CompareLayout.js`
- Modify: `frontend/src/main.js`
- Test: `frontend/e2e/tests/viewer.spec.js` (update selectors if text-based)

**Step 1: Create translation map**

This is the reference translation map. Each file below will be updated using these translations.

| English | French |
|---------|--------|
| ML Analysis | Analyse IA |
| Analyze Slide | Analyser la lame |
| Show Heatmap | Afficher la carte de chaleur |
| Hide Heatmap | Masquer la carte de chaleur |
| Prediction | Prediction |
| Confidence | Confiance |
| Opacity | Opacite |
| Auto-Detection | Detection automatique |
| Detect Regions | Detecter les regions |
| Threshold | Seuil |
| Min Area | Surface min. |
| Accept | Accepter |
| Reject | Rejeter |
| Confirm All | Tout confirmer |
| Annotations | Annotations |
| By Label | Par etiquette |
| By Type | Par type |
| Unlabeled | Sans etiquette |
| No annotations yet | Aucune annotation |
| Quality Metrics | Metriques de qualite |
| Compute Metrics | Calculer les metriques |
| Layers | Couches |
| Export GeoJSON | Exporter GeoJSON |
| Select (V) | Selection (V) |
| Rectangle (R) | Rectangle (R) |
| Polygon (P) | Polygone (P) |
| Point (M) | Point (M) |
| Freehand (F) | Main levee (F) |
| Circle (C) | Cercle (C) |
| Delete Selected | Supprimer la selection |
| Slide Viewer | Visualiseur de lame |
| Select slide | Selectionner une lame |
| Reset view | Reinitialiser la vue |
| Compare Mode | Mode comparaison |
| Back | Retour |
| high | elevee |
| medium | moyenne |
| low | faible |
| manual | manuel |
| auto | auto |
| auto_confirmed | auto confirme |
| Viewer | Visualiseur |

**Step 2: Update DrawingTools.js**

In `frontend/src/components/DrawingTools.js`, lines 32-39, replace the `TOOL_LABELS` object:

```js
const TOOL_LABELS = {
    select: 'S\u00e9lection (V)',
    rectangle: 'Rectangle (R)',
    polygon: 'Polygone (P)',
    point: 'Point (M)',
    freehand: 'Main lev\u00e9e (F)',
    circle: 'Cercle (C)',
};
```

Also find and replace the delete button tooltip text:
- `'Delete Selected'` to `'Supprimer la s\u00e9lection'`

**Step 3: Update MLPanel.js**

Search and replace all English UI strings in `frontend/src/components/MLPanel.js`:
- `'ML Analysis'` to `'Analyse IA'`
- `'Analyze Slide'` to `'Analyser la lame'`
- `'Show Heatmap'` to `'Afficher la carte de chaleur'`
- `'Hide Heatmap'` to `'Masquer la carte de chaleur'`
- `'Prediction'` to `'Pr\u00e9diction'`
- `'Confidence'` to `'Confiance'`
- `'Opacity'` to `'Opacit\u00e9'`
- Any other English strings found in the file

**Step 4: Update DetectionPanel.js**

Search and replace in `frontend/src/components/DetectionPanel.js`:
- `'Auto-Detection'` to `'D\u00e9tection automatique'`
- `'Detect Regions'` to `'D\u00e9tecter les r\u00e9gions'`
- `'Threshold'` to `'Seuil'`
- `'Min Area'` to `'Surface min.'`
- `'Accept'` to `'Accepter'`
- `'Reject'` to `'Rejeter'`
- `'Confirm All'` to `'Tout confirmer'`
- `'Confidence'` to `'Confiance'`

**Step 5: Update CountingPanel.js**

In `frontend/src/components/CountingPanel.js`:
- `'Annotations'` stays `'Annotations'` (same in FR)
- `'By Label'` to `'Par \u00e9tiquette'`
- `'By Type'` to `'Par type'`
- `'Unlabeled'` to `'Sans \u00e9tiquette'`
- `'No annotations yet'` to `'Aucune annotation'`
- `'Confidence'` to `'Confiance'`
- `'high'` to `'\u00e9lev\u00e9e'`
- `'medium'` to `'moyenne'`
- `'low'` to `'faible'`

**Step 6: Update QualityPanel.js**

In `frontend/src/components/QualityPanel.js`:
- `'Quality Metrics'` to `'M\u00e9triques de qualit\u00e9'`
- `'Compute Metrics'` to `'Calculer les m\u00e9triques'`
- Other English strings found

**Step 7: Update LayerManager.js**

In `frontend/src/components/LayerManager.js`:
- `'Layers'` to `'Couches'`
- `'Export GeoJSON'` to `'Exporter GeoJSON'`
- `'No annotations yet'` to `'Aucune annotation'`

**Step 8: Update ViewerPanel.js**

In `frontend/src/components/ViewerPanel.js`:
- `'Slide Viewer'` to `'Visualiseur de lame'`
- `'Select slide'` to `'S\u00e9lectionner une lame'`
- `'Reset view'` to `'R\u00e9initialiser la vue'`

**Step 9: Update CompareLayout.js**

In `frontend/src/components/CompareLayout.js`:
- `` `Viewer ${index + 1}` `` to `` `Visualiseur ${index + 1}` ``

**Step 10: Update main.js**

In `frontend/src/main.js`:
- `'Compare Mode'` to `'Mode comparaison'`
- `'Back'` to `'Retour'`
- Other English UI strings

**Step 11: Update E2E tests**

In `frontend/e2e/tests/viewer.spec.js`, update any text-based selectors that reference the old English strings. For example:
- `getByText('ML Analysis')` to `getByText('Analyse IA')`
- Check all `getByText`, `getByRole`, `getByLabel` selectors

**Step 12: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: All tests PASS with new French labels

**Step 13: Commit**

```bash
git add frontend/src/components/ frontend/src/main.js frontend/e2e/
git commit -m "feat(ux): translate all UI strings to French pathologist terminology (#60)"
```

---

## Task 3: W1-UX02 — Labels d'annotation predefinis metier (#61)

**Files:**
- Create: `backend/alembic/versions/004_seed_pathology_labels.py`
- Test: `backend/tests/test_annotations_api.py` (extend)

**Step 1: Write the migration**

Create `backend/alembic/versions/004_seed_pathology_labels.py`:

```python
"""Seed predefined pathology annotation labels

Revision ID: 004
Revises: 003
Create Date: 2026-02-16
"""

import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Predefined labels for anatomopathology workflow
PATHOLOGY_LABELS = [
    # Diagnostic labels
    {"name": "Tumeur", "color": "#e74c3c", "category": "diagnostic", "sort_order": 1},
    {"name": "Necrose", "color": "#8e44ad", "category": "diagnostic", "sort_order": 2},
    {"name": "Inflammation", "color": "#e67e22", "category": "diagnostic", "sort_order": 3},
    {"name": "Stroma", "color": "#3498db", "category": "diagnostic", "sort_order": 4},
    {"name": "Tissu sain", "color": "#2ecc71", "category": "diagnostic", "sort_order": 5},
    # Structural labels
    {"name": "Marge de resection", "color": "#f39c12", "category": "structure", "sort_order": 10},
    {"name": "Embole vasculaire", "color": "#c0392b", "category": "structure", "sort_order": 11},
    {"name": "Invasion peri-nerveuse", "color": "#d35400", "category": "structure", "sort_order": 12},
    # Quality labels
    {"name": "Artefact", "color": "#95a5a6", "category": "qualite", "sort_order": 20},
    {"name": "Zone floue", "color": "#7f8c8d", "category": "qualite", "sort_order": 21},
    {"name": "Pli de tissu", "color": "#bdc3c7", "category": "qualite", "sort_order": 22},
]


def upgrade() -> None:
    now = datetime.now(UTC).isoformat()
    for label in PATHOLOGY_LABELS:
        op.execute(
            sa.text(
                "INSERT INTO annotation_labels (id, name, color, category, sort_order, created_at) "
                "VALUES (:id, :name, :color, :category, :sort_order, :created_at) "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(
                id=str(uuid.uuid4()),
                name=label["name"],
                color=label["color"],
                category=label["category"],
                sort_order=label["sort_order"],
                created_at=now,
            )
        )


def downgrade() -> None:
    names = [l["name"] for l in PATHOLOGY_LABELS]
    placeholders = ", ".join(f"'{n}'" for n in names)
    op.execute(sa.text(f"DELETE FROM annotation_labels WHERE name IN ({placeholders})"))
```

**Step 2: Run the migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration 004 applied successfully

**Step 3: Verify labels exist**

Run: `curl http://localhost:8000/api/annotations/labels | python -m json.tool`

**Step 4: Commit**

```bash
git add backend/alembic/versions/004_seed_pathology_labels.py
git commit -m "feat(db): seed 11 predefined pathology annotation labels (#61)"
```

---

## Task 4: W1-UX03 — Panneaux ML et Quality masques par defaut (#62)

**Files:**
- Modify: `frontend/src/components/MLPanel.js`
- Modify: `frontend/src/components/DetectionPanel.js`
- Modify: `frontend/src/components/QualityPanel.js`
- Modify: `frontend/src/css/ml-panel.css`
- Modify: `frontend/src/css/detection-panel.css`

**Step 1: Add accordion to MLPanel**

In `frontend/src/components/MLPanel.js`, find the `_build()` method. Wrap the panel body in a collapsible section.

Add a property in the constructor:
```js
this.isCollapsed = true; // collapsed by default
```

In `_build()`, make the header clickable and add a chevron indicator:
```js
// In the header element creation:
const header = document.createElement('div');
header.className = 'ml-panel__header ml-panel__header--collapsible';
header.addEventListener('click', () => this._toggleCollapse());

const title = document.createElement('span');
title.className = 'ml-panel__title';
title.textContent = 'Analyse IA';

const chevron = document.createElement('span');
chevron.className = 'ml-panel__chevron';
chevron.textContent = '\u25B6'; // right-pointing triangle

header.appendChild(title);
header.appendChild(chevron);
```

Add the toggle method:
```js
_toggleCollapse() {
    this.isCollapsed = !this.isCollapsed;
    const body = this.element.querySelector('.ml-panel__body');
    const chevron = this.element.querySelector('.ml-panel__chevron');
    if (body) {
        body.style.display = this.isCollapsed ? 'none' : 'block';
    }
    if (chevron) {
        chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
    }
}
```

Set initial collapsed state after build:
```js
// At end of _build():
const body = this.element.querySelector('.ml-panel__body');
if (body) body.style.display = 'none';
```

**Step 2: Add accordion to DetectionPanel**

Same pattern in `frontend/src/components/DetectionPanel.js`:
- Add `this.isCollapsed = true;` in constructor
- Make header clickable with chevron
- Panel body hidden by default

**Step 3: Verify QualityPanel**

`QualityPanel` already has `this.isCollapsed = true;` at line 36. Verify it starts collapsed — no changes needed if it does.

**Step 4: Add CSS for collapsible headers**

In `frontend/src/css/ml-panel.css`, add:
```css
.ml-panel__header--collapsible {
    cursor: pointer;
    user-select: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.ml-panel__chevron {
    font-size: 0.75rem;
    transition: transform 0.2s ease;
    color: var(--text-secondary);
}
```

Similar styles for DetectionPanel in `frontend/src/css/detection-panel.css`.

**Step 5: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: All tests PASS (panels start collapsed, tests may need to click to expand)

**Step 6: Commit**

```bash
git add frontend/src/components/MLPanel.js frontend/src/components/DetectionPanel.js
git add frontend/src/css/ml-panel.css frontend/src/css/detection-panel.css
git commit -m "feat(ux): collapse ML and Detection panels by default with accordion (#62)"
```

---

## Task 5: W1-UX05 — Barre de status en grossissement optique (#64)

**Files:**
- Modify: `frontend/src/viewers/ViewerInstance.js`
- Modify: `frontend/src/components/ViewerPanel.js`
- Create: `frontend/src/css/magnification-bar.css`

**Step 1: Add magnification calculator to ViewerInstance**

In `frontend/src/viewers/ViewerInstance.js`, add a method:

```js
/**
 * Get current optical-equivalent magnification.
 * Assumes 0.25 um/px at max resolution (40x objective equivalent).
 * @returns {number} Magnification value (e.g. 1, 2, 5, 10, 20, 40)
 */
getOpticalMagnification() {
    if (!this.viewer || !this.viewer.viewport) return 1;
    const zoom = this.viewer.viewport.getZoom(true);
    const maxZoom = this.viewer.viewport.getMaxZoom();
    const ratio = zoom / maxZoom;
    // 40x at max zoom, scale linearly
    const rawMag = ratio * 40;
    // Snap to nearest standard objective
    const objectives = [1, 2, 4, 5, 10, 20, 40];
    let closest = objectives[0];
    for (const obj of objectives) {
        if (Math.abs(obj - rawMag) < Math.abs(closest - rawMag)) {
            closest = obj;
        }
    }
    return closest;
}
```

**Step 2: Add magnification bar to ViewerPanel**

In `frontend/src/components/ViewerPanel.js`, in the `_build()` method, add a magnification indicator in the viewer container:

```js
// Create magnification bar element
this.magBar = document.createElement('div');
this.magBar.className = 'magnification-bar';
this.magBar.textContent = '\u00d71'; // multiplication sign + 1
// Append to the viewer container
```

Subscribe to viewport changes to update it:
```js
this._unsubscribers.push(
    eventBus.on(Events.VIEWPORT_CHANGE, (data) => {
        if (data.viewerId === this.viewerInstance?.id) {
            this._updateMagnification();
        }
    })
);
```

Add the update method:
```js
_updateMagnification() {
    if (!this.viewerInstance || !this.magBar) return;
    const mag = this.viewerInstance.getOpticalMagnification();
    this.magBar.textContent = '\u00d7' + mag;
    // Color code: green for diagnostic zoom (10x, 20x, 40x)
    this.magBar.classList.toggle('magnification-bar--diagnostic', mag >= 10);
}
```

**Step 3: Create CSS**

Create `frontend/src/css/magnification-bar.css`:
```css
.magnification-bar {
    position: absolute;
    bottom: 8px;
    left: 8px;
    background: var(--bg-primary, rgba(0, 0, 0, 0.7));
    color: var(--text-primary, #fff);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    z-index: 10;
    pointer-events: none;
    transition: background 0.2s ease;
}

.magnification-bar--diagnostic {
    background: var(--accent-primary, #00b894);
}
```

**Step 4: Import CSS in main entry**

Add the CSS import in the appropriate entry file (check if there is an index.html or main CSS import).

**Step 5: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/src/viewers/ViewerInstance.js frontend/src/components/ViewerPanel.js
git add frontend/src/css/magnification-bar.css
git commit -m "feat(ux): add optical magnification bar (x10, x40) to viewer (#64)"
```

---

## Task 6: W1-UX06 — Toolbar contextuelle (#65)

**Files:**
- Modify: `frontend/src/components/DrawingTools.js`
- Modify: `frontend/src/css/drawing-tools.css`

**Step 1: Modify DrawingTools to show 2 primary + overflow**

In `frontend/src/components/DrawingTools.js`, the current `_build()` creates buttons for all 6 tools. Change to show only 2 primary tools (Select + last-used drawing tool) with an overflow menu.

Add to constructor:
```js
this.primaryTools = ['select', 'rectangle']; // default primary set
this.overflowOpen = false;
```

Modify `_build()` to create:
1. Two primary tool buttons (always visible)
2. A "more" button
3. An overflow container (hidden by default) with remaining tools

```js
// Primary tools
this.primaryTools.forEach(tool => {
    this._createToolButton(tool, toolbar);
});

// Overflow toggle button
const moreBtn = document.createElement('button');
moreBtn.className = 'drawing-tools__btn drawing-tools__btn--more';
moreBtn.textContent = '\u22EF'; // horizontal ellipsis character
moreBtn.title = "Plus d'outils";
moreBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    this._toggleOverflow();
});
toolbar.appendChild(moreBtn);

// Overflow menu
this.overflowMenu = document.createElement('div');
this.overflowMenu.className = 'drawing-tools__overflow';
this.overflowMenu.style.display = 'none';

TOOLS.filter(t => !this.primaryTools.includes(t)).forEach(tool => {
    this._createToolButton(tool, this.overflowMenu);
});
toolbar.appendChild(this.overflowMenu);
```

When user selects a tool from overflow, it replaces the second primary slot:
```js
_onToolSelect(tool) {
    this.activeTool = tool;
    if (tool !== 'select' && !this.primaryTools.includes(tool)) {
        this.primaryTools[1] = tool;
        this._rebuild(); // rebuild toolbar with new primary
    }
    this.overflowOpen = false;
    if (this.overflowMenu) this.overflowMenu.style.display = 'none';
    this._updateActiveStates();
}
```

**Step 2: Add CSS for overflow**

In `frontend/src/css/drawing-tools.css`, add:
```css
.drawing-tools__btn--more {
    font-size: 1.2rem;
    letter-spacing: 2px;
    color: var(--text-secondary);
}

.drawing-tools__overflow {
    position: absolute;
    top: 100%;
    left: 0;
    background: var(--bg-secondary, #1e1e1e);
    border: 1px solid var(--border-color, #333);
    border-radius: 6px;
    padding: 4px;
    display: flex;
    gap: 2px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 100;
}
```

**Step 3: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: PASS (drawing tests should still work via clicking tools)

**Step 4: Commit**

```bash
git add frontend/src/components/DrawingTools.js frontend/src/css/drawing-tools.css
git commit -m "feat(ux): contextual toolbar with 2 primary tools and overflow menu (#65)"
```

---

## Task 7: W1-UX07 — Badge incertitude ML (#66)

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js`
- Modify: `frontend/src/css/detection-panel.css`

**Step 1: Add confidence badges to detection results**

In `frontend/src/components/DetectionPanel.js`, find where individual detections are rendered. For each detection, add a colored confidence badge:

```js
_getConfidenceBadge(confidence) {
    const badge = document.createElement('span');
    if (confidence === null || confidence === undefined) {
        badge.className = 'detection-badge detection-badge--unknown';
        badge.textContent = '?';
        badge.title = 'Confiance inconnue';
    } else if (confidence >= 0.8) {
        badge.className = 'detection-badge detection-badge--high';
        badge.textContent = Math.round(confidence * 100) + '%';
        badge.title = 'Confiance \u00e9lev\u00e9e';
    } else if (confidence >= 0.5) {
        badge.className = 'detection-badge detection-badge--medium';
        badge.textContent = Math.round(confidence * 100) + '%';
        badge.title = 'Confiance moyenne';
    } else {
        badge.className = 'detection-badge detection-badge--low';
        badge.textContent = Math.round(confidence * 100) + '%';
        badge.title = 'Confiance faible';
    }
    return badge;
}
```

Insert this badge next to each detection item in the result list.

**Step 2: Add CSS for badges**

In `frontend/src/css/detection-panel.css`, add:
```css
.detection-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    vertical-align: middle;
    margin-left: 6px;
}

.detection-badge--high {
    background: rgba(46, 204, 113, 0.2);
    color: #2ecc71;
    border: 1px solid rgba(46, 204, 113, 0.3);
}

.detection-badge--medium {
    background: rgba(243, 156, 18, 0.2);
    color: #f39c12;
    border: 1px solid rgba(243, 156, 18, 0.3);
}

.detection-badge--low {
    background: rgba(231, 76, 60, 0.2);
    color: #e74c3c;
    border: 1px solid rgba(231, 76, 60, 0.3);
}

.detection-badge--unknown {
    background: rgba(149, 165, 166, 0.2);
    color: #95a5a6;
    border: 1px solid rgba(149, 165, 166, 0.3);
}
```

**Step 3: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/components/DetectionPanel.js frontend/src/css/detection-panel.css
git commit -m "feat(ux): add colored confidence badges to ML detections (#66)"
```

---

## Task 8: W1-UX08 — Comptage annotations integre dans sidebar (#67)

**Files:**
- Modify: `frontend/src/components/CountingPanel.js`

**Step 1: Add grouped counting summary**

The CountingPanel already exists and shows counts. Enhance `_render()` to show a more structured summary with label-grouped counts that are visible in the sidebar at a glance.

Update the section titles to French (if not done in Task 2):
- `'By Label'` to `'Par etiquette'`
- `'By Type'` to `'Par type'`
- `'Unlabeled'` to `'Sans etiquette'`

Add a compact summary line at the top showing total count prominently:
```js
// In _render(), create a summary header:
const summaryDiv = document.createElement('div');
summaryDiv.className = 'counting-panel__summary';

const totalSpan = document.createElement('span');
totalSpan.className = 'counting-panel__total-big';
totalSpan.textContent = String(data.total);

const labelSpan = document.createElement('span');
labelSpan.className = 'counting-panel__total-label';
labelSpan.textContent = data.total === 1 ? 'annotation' : 'annotations';

summaryDiv.appendChild(totalSpan);
summaryDiv.appendChild(labelSpan);
```

**Step 2: Run E2E tests**

Run: `cd frontend && npx playwright test --reporter=list`
Expected: PASS

**Step 3: Commit**

```bash
git add frontend/src/components/CountingPanel.js
git commit -m "feat(ux): enhanced counting summary in sidebar with label grouping (#67)"
```

---

## Task 9: W1-INF01 — Table corrections SQL + migration Alembic (#68)

**Files:**
- Create: `backend/models/correction.py`
- Create: `backend/alembic/versions/005_corrections.py`
- Test: `backend/tests/test_annotations_api.py` (extend)

**Step 1: Create the Correction ORM model**

Create `backend/models/correction.py`:

```python
"""
Correction ORM Model

Tracks pathologist corrections to ML predictions.
Links to annotations table for provenance tracking.
Supports: confirmed, rejected, refined (geometry edit), relabeled.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    correction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # confirmed, rejected, refined, relabeled
    original_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    corrected_label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotation_labels.id", ondelete="SET NULL"),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    annotation = relationship("Annotation", lazy="selectin")
    corrected_label = relationship("AnnotationLabel", lazy="selectin")

    def __repr__(self):
        return (
            f"<Correction(id='{self.id}', type='{self.correction_type}', "
            f"annotation='{self.annotation_id}')>"
        )
```

**Step 2: Create the Alembic migration**

Create `backend/alembic/versions/005_corrections.py`:

```python
"""Corrections table for ML feedback loop

Revision ID: 005
Revises: 004
Create Date: 2026-02-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "annotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("annotations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slide_id", sa.String(500), nullable=False),
        sa.Column("correction_type", sa.String(20), nullable=False),
        sa.Column("original_confidence", sa.Float, nullable=True),
        sa.Column(
            "corrected_label_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("annotation_labels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("model_name", sa.String(200), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("metadata_extra", postgresql.JSONB, nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_corrections_annotation_id", "corrections", ["annotation_id"])
    op.create_index("idx_corrections_slide_id", "corrections", ["slide_id"])
    op.create_index("idx_corrections_type", "corrections", ["correction_type"])


def downgrade() -> None:
    op.drop_index("idx_corrections_type")
    op.drop_index("idx_corrections_slide_id")
    op.drop_index("idx_corrections_annotation_id")
    op.drop_table("corrections")
```

**Step 3: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration 005 applied, `corrections` table created

**Step 4: Verify table**

Run: `cd backend && python -c "from models.correction import Correction; print(Correction.__tablename__)"`
Expected: `corrections`

**Step 5: Commit**

```bash
git add backend/models/correction.py backend/alembic/versions/005_corrections.py
git commit -m "feat(db): add corrections table for ML feedback loop (#68)"
```

---

## Task 10: W1-INF02 — Cache disque embeddings niveau 2 (#71)

**Files:**
- Create: `backend/services/__init__.py` (if not exists)
- Create: `backend/services/cache/__init__.py`
- Create: `backend/services/cache/disk_cache.py`
- Test: `backend/tests/test_disk_cache.py`

**Step 1: Write the failing test**

Create `backend/tests/test_disk_cache.py`:

```python
"""Tests for disk cache service (embeddings .npy storage)"""

import numpy as np
import pytest


@pytest.mark.unit
class TestDiskCache:
    def test_save_and_load_embeddings(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        slide_id = "test_slide_001"
        model = "phikon_v1"
        embeddings = np.random.rand(100, 1024).astype(np.float32)

        cache.save_embeddings(slide_id, model, embeddings)
        loaded = cache.load_embeddings(slide_id, model)

        assert loaded is not None
        assert loaded.shape == (100, 1024)
        np.testing.assert_array_almost_equal(loaded, embeddings)

    def test_load_missing_returns_none(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        result = cache.load_embeddings("nonexistent", "model")
        assert result is None

    def test_invalidate(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        embeddings = np.random.rand(10, 1024).astype(np.float32)
        cache.save_embeddings("slide1", "model1", embeddings)

        cache.invalidate("slide1", "model1")
        assert cache.load_embeddings("slide1", "model1") is None

    def test_exists(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        embeddings = np.random.rand(5, 1024).astype(np.float32)

        assert not cache.exists("slide1", "model1")
        cache.save_embeddings("slide1", "model1", embeddings)
        assert cache.exists("slide1", "model1")

    def test_save_and_load_heatmap(self, tmp_path):
        from services.cache.disk_cache import DiskCache

        cache = DiskCache(base_dir=str(tmp_path))
        heatmap = np.random.rand(256, 256).astype(np.float32)

        cache.save_heatmap("slide1", "model1", heatmap)
        loaded = cache.load_heatmap("slide1", "model1")

        assert loaded is not None
        np.testing.assert_array_almost_equal(loaded, heatmap)
```

**Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_disk_cache.py -v`
Expected: FAIL (ModuleNotFoundError -- services.cache.disk_cache does not exist)

**Step 3: Implement DiskCache**

Create directory structure:
```bash
mkdir -p backend/services/cache
touch backend/services/__init__.py
touch backend/services/cache/__init__.py
```

Create `backend/services/cache/disk_cache.py`:

```python
"""
Disk Cache Service -- Level 2 Cache

Stores computed numpy arrays (embeddings, heatmaps, detections) on disk
using .npy format. Organized by slide_id and model name.

Directory structure:
    {base_dir}/{slide_id}/{model}/{type}.npy

Thread-safe: uses atomic write (write to tmp, then rename).
"""

import logging
import os
import tempfile
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class DiskCache:
    """Numpy-based disk cache for ML computed results."""

    def __init__(self, base_dir: str = "/tmp/varuna_cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slide_id: str, model: str, data_type: str = "embeddings") -> Path:
        """Build cache file path."""
        # Sanitize slide_id (may contain path separators)
        safe_id = slide_id.replace("/", "_").replace("\\", "_")
        return self.base_dir / safe_id / model / f"{data_type}.npy"

    def save_embeddings(self, slide_id: str, model: str, data: np.ndarray) -> None:
        """Save embeddings array to disk."""
        self._save(slide_id, model, "embeddings", data)

    def load_embeddings(self, slide_id: str, model: str) -> np.ndarray | None:
        """Load embeddings from disk. Returns None if not cached."""
        return self._load(slide_id, model, "embeddings")

    def save_heatmap(self, slide_id: str, model: str, data: np.ndarray) -> None:
        """Save heatmap array to disk."""
        self._save(slide_id, model, "heatmap", data)

    def load_heatmap(self, slide_id: str, model: str) -> np.ndarray | None:
        """Load heatmap from disk. Returns None if not cached."""
        return self._load(slide_id, model, "heatmap")

    def exists(self, slide_id: str, model: str, data_type: str = "embeddings") -> bool:
        """Check if cache entry exists."""
        return self._path(slide_id, model, data_type).exists()

    def invalidate(self, slide_id: str, model: str, data_type: str = "embeddings") -> None:
        """Remove a specific cache entry."""
        path = self._path(slide_id, model, data_type)
        if path.exists():
            path.unlink()
            logger.info("Cache invalidated: %s/%s/%s", slide_id, model, data_type)

    def _save(self, slide_id: str, model: str, data_type: str, data: np.ndarray) -> None:
        """Atomic save: write to temp file, then rename."""
        path = self._path(slide_id, model, data_type)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write
        fd, tmp_path = tempfile.mkstemp(suffix=".npy", dir=str(path.parent))
        try:
            np.save(tmp_path, data)
            os.replace(tmp_path, str(path))
            logger.debug("Cached %s: %s (%s)", data_type, path, data.shape)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def _load(self, slide_id: str, model: str, data_type: str) -> np.ndarray | None:
        """Load numpy array from disk."""
        path = self._path(slide_id, model, data_type)
        if not path.exists():
            return None
        try:
            return np.load(str(path))
        except Exception as e:
            logger.warning("Failed to load cache %s: %s", path, e)
            return None
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_disk_cache.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add backend/services/ backend/tests/test_disk_cache.py
git commit -m "feat(infra): add disk cache service for embeddings and heatmaps (#71)"
```

---

## Task 11: W1-INF03 — Cache memoire metadata niveau 1 (#73)

**Files:**
- Create: `backend/services/cache/memory_cache.py`
- Modify: `backend/requirements.txt` (add cachetools)
- Test: `backend/tests/test_memory_cache.py`

**Step 1: Add cachetools dependency**

In `backend/requirements.txt`, add under a new section:
```
# Phase 5: Caching
cachetools>=5.3.0
```

**Step 2: Write the failing test**

Create `backend/tests/test_memory_cache.py`:

```python
"""Tests for memory cache service (TTL-based metadata cache)"""

import time

import pytest


@pytest.mark.unit
class TestMemoryCache:
    def test_get_set(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("slide:info:abc", {"width": 1024, "height": 768})
        result = cache.get("slide:info:abc")
        assert result == {"width": 1024, "height": 768}

    def test_get_missing_returns_none(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=1)  # 1 second TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_invalidate(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_maxsize_eviction(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=3, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # should evict oldest
        # At least one of the first entries should be evicted
        assert cache.get("d") == 4

    def test_stats(self):
        from services.cache.memory_cache import MemoryCache

        cache = MemoryCache(maxsize=100, ttl=60)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("missing")  # miss

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["maxsize"] == 100
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
```

**Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_memory_cache.py -v`
Expected: FAIL (ModuleNotFoundError)

**Step 4: Implement MemoryCache**

Create `backend/services/cache/memory_cache.py`:

```python
"""
Memory Cache Service -- Level 1 Cache

Fast in-memory TTL cache for metadata, slide info, and ML tags.
Built on cachetools TTLCache with hit/miss statistics.

Thread-safe via built-in cachetools locking.
"""

import logging

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class MemoryCache:
    """TTL-based in-memory cache with statistics."""

    def __init__(self, maxsize: int = 512, ttl: int = 300):
        """
        Args:
            maxsize: Maximum number of entries
            ttl: Time-to-live in seconds (default 5 minutes)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def get(self, key: str):
        """Get value by key. Returns None if missing or expired."""
        try:
            value = self._cache[key]
            self._hits += 1
            return value
        except KeyError:
            self._misses += 1
            return None

    def set(self, key: str, value) -> None:
        """Set a key-value pair."""
        self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a specific key."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": (
                self._hits / (self._hits + self._misses)
                if (self._hits + self._misses) > 0
                else 0.0
            ),
        }
```

**Step 5: Install dependency and run tests**

Run: `cd backend && pip install cachetools>=5.3.0 && python -m pytest tests/test_memory_cache.py -v`
Expected: All 7 tests PASS

**Step 6: Commit**

```bash
git add backend/services/cache/memory_cache.py backend/tests/test_memory_cache.py backend/requirements.txt
git commit -m "feat(infra): add TTL-based memory cache for metadata and tags (#73)"
```

---

## Final Verification

After all 11 tasks are complete:

```bash
# Run all unit tests
cd backend && python -m pytest tests/ -m "unit" -v

# Run all E2E tests
cd frontend && npx playwright test --reporter=list

# Verify all migrations
cd backend && alembic current
# Expected: 005 (head)
```

Then create a PR for the wave1 branch.
