# Annotation Phase C — Maturite Clinique

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address all pathologist-identified blockers (contour editing, annotation history, quiz scoring) and remaining technical review findings (migration merge, rejection reasons, Tab skip validated) to reach clinical-grade annotation quality.

**Architecture:** Contour editing extends DrawingTools with vertex-drag on selected annotations. Annotation history uses a new `annotation_versions` table (append-only). Quiz scoring tracks reveals in AnnotationLayer and displays results. Migration 008 is corrected with a proper merge approach.

**Tech Stack:** PostgreSQL + Alembic (backend), SVG vertex editing (frontend), existing EventBus pipeline

**Sources:**
- Technical review: 3 critical + 2 important findings
- Pathologist review (Dr. Patil): 3 blockers + 4 important demands

---

## Consolidated Issue Tracker

### From Technical Review
| # | Severity | Issue | Task |
|---|----------|-------|------|
| T3 | CRITICAL | Migration 008 ambiguous with two "006" | Task 1 |
| P6 | IMPORTANT | Tab should skip validated detections too | Task 2 |
| P5 | IMPORTANT | Rejection reason field (mandatory) | Task 3 |

### From Pathologist Review
| # | Severity | Issue | Task |
|---|----------|-------|------|
| P2 | BLOCKER | Edit AI detection contours (E key, vertex drag) | Task 4 |
| P3 | BLOCKER | Annotation version history (medicolegal) | Task 5 |
| P4 | IMPORTANT | Quiz mode scoring (22/30 = 73%) | Task 6 |
| P7 | IMPORTANT | Honest AI dashboard message | Task 7 |

*Note: Pathologist blocker #1 (multi-lame sync) already exists (CompareLayout, SyncController) — separate roadmap item.*

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/alembic/versions/007_merge_heads.py` | Create | Merge the two "006" branches |
| `backend/alembic/versions/008_annotation_notes_and_status.py` | Modify | down_revision = "007" |
| `backend/alembic/versions/009_annotation_versions.py` | Create | annotation_versions table |
| `backend/models/annotation_version.py` | Create | AnnotationVersion ORM model |
| `backend/models/annotation.py` | Modify | Add rejection_reason field |
| `backend/schemas/annotation.py` | Modify | Add rejection_reason to schemas |
| `backend/routes/annotations.py` | Modify | Auto-create version on update, rejection_reason on reject |
| `frontend/src/components/DrawingTools.js` | Modify | Tab skip validated, E=edit contour mode |
| `frontend/src/components/DetectionPanel.js` | Modify | Tab skip validated |
| `frontend/src/components/AnnotationLayer.js` | Modify | Vertex editing overlay, quiz scoring |
| `frontend/src/components/DashboardPanel.js` | Modify | Honest AI message |
| `frontend/src/core/Constants.js` | Modify | New events for contour editing |

---

### Task 1: Fix Migration Chain (merge two "006" branches)

**Files:**
- Create: `backend/alembic/versions/007_merge_heads.py`
- Modify: `backend/alembic/versions/008_annotation_notes_and_status.py`

- [ ] **Step 1: Create merge migration 007**

```python
"""Merge two 006 branches (tenant_id + worklist)

Revision ID: 007
Revises: 006 (both branches)
"""

from typing import Union

revision: str = "007"
down_revision: tuple[str, str] = ("006", "006")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

Note: Alembic actually cannot distinguish two revisions with the same ID "006". The practical fix is to rename one of the 006 files to have a unique revision ID. Rename `006_add_tenant_id.py` to use revision `"006a"` and update its references. Then:
- `007_merge_heads.py`: `down_revision = ("006", "006a")`
- `008`: `down_revision = "007"`

- [ ] **Step 2: Update 008 down_revision to "007"**

- [ ] **Step 3: Test with `alembic upgrade head`**

- [ ] **Step 4: Commit**

```bash
git commit -m "fix(db): resolve migration branch conflict with merge revision 007"
```

---

### Task 2: Tab Skips Validated Detections

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js`

- [ ] **Step 1: Update _goToNextDetection**

In the while loop, also skip `this.accepted.has(next)`:

```javascript
    if (!this.hiddenZones.has(next) && !this.rejected.has(next) && !this.accepted.has(next)) break;
```

- [ ] **Step 2: Commit**

```bash
git commit -m "fix(detection): Tab skips validated detections in addition to rejected/hidden"
```

---

### Task 3: Rejection Reason Field

**Files:**
- Modify: `backend/models/annotation.py`
- Modify: `backend/schemas/annotation.py`
- Modify: `backend/routes/annotations.py`
- Create: `backend/alembic/versions/009_add_rejection_reason.py`

- [ ] **Step 1: Add `rejection_reason` column to model**

```python
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

- [ ] **Step 2: Update schemas**

Add `rejection_reason` to AnnotationUpdate and AnnotationResponse.
In reject endpoint, require reason via Query param:
```python
    reason: str = Query(..., min_length=1, max_length=500, description="Rejection reason"),
```

- [ ] **Step 3: Create migration 009**

- [ ] **Step 4: Update frontend reject flow**

In DrawingTools X key handler, show a quick reason selector (predefined: "Faux positif", "Artefact", "Zone deja annotee", "Contour incorrect", "Autre") before rejecting.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(annotations): add mandatory rejection reason for AI correction audit"
```

---

### Task 4: Edit AI Detection Contours (E Key)

**Files:**
- Modify: `frontend/src/components/DrawingTools.js`
- Modify: `frontend/src/components/AnnotationLayer.js`
- Modify: `frontend/src/core/Constants.js`

This is the pathologist's #2 blocker. When E is pressed on a selected annotation/detection, enter vertex editing mode.

- [ ] **Step 1: Add E key and CONTOUR_EDIT_START/END events**

In Constants.js:
```javascript
    CONTOUR_EDIT_START: 'contour:editStart',
    CONTOUR_EDIT_END: 'contour:editEnd',
```

In DrawingTools._handleKeyDown:
```javascript
    case 'e': case 'E':
        if (e.ctrlKey || e.metaKey) break;
        this._startContourEdit();
        break;
```

- [ ] **Step 2: Implement _startContourEdit() in DrawingTools**

Get selected annotation from annotationStore. If it has a Polygon geometry, enter edit mode:
- Render vertex handles (small circles) at each coordinate
- Enable drag on vertex handles (mousedown → mousemove → mouseup)
- On mouseup, update annotation geometry via annotationStore.updateAnnotation()
- Save as `annotation_type = 'auto_refined'` to track that it was AI + manually corrected

- [ ] **Step 3: Implement vertex rendering in AnnotationLayer**

Add `_renderVertexHandles(annotation)` method:
- Create SVG circles at each polygon vertex
- Each circle: draggable, `pointer-events: all` (exception to the pointer-events:none rule)
- On drag: update SVG polygon points in real-time
- On drop: emit CONTOUR_EDIT_END with new coordinates

- [ ] **Step 4: Add vertex handle CSS**

```css
.annotation-vertex {
    fill: white;
    stroke: #3b82f6;
    stroke-width: 2;
    cursor: grab;
    pointer-events: all;
}
.annotation-vertex:hover {
    fill: #3b82f6;
}
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(annotations): add contour editing mode (E key) for AI detection refinement

E key enters vertex editing on selected annotation. Drag vertices to
refine AI detection contours. Saves as auto_refined type for audit."
```

---

### Task 5: Annotation Version History (Medicolegal)

**Files:**
- Create: `backend/models/annotation_version.py`
- Create: `backend/alembic/versions/010_annotation_versions.py`
- Modify: `backend/routes/annotations.py`

- [ ] **Step 1: Create AnnotationVersion model**

```python
class AnnotationVersion(Base):
    __tablename__ = "annotation_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("annotations.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry: Mapped[str] = mapped_column(Geometry(geometry_type="GEOMETRY", srid=0), nullable=False)
    geometry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
```

- [ ] **Step 2: Auto-create version on annotation update**

In the PUT endpoint and PATCH validate/reject, before committing changes, snapshot current state to annotation_versions.

- [ ] **Step 3: Add GET /annotations/{slide_id}/{annotation_id}/history**

Returns all versions of an annotation, ordered by version number.

- [ ] **Step 4: Create migration 010**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(annotations): add versioned annotation history for medicolegal audit

Every annotation update creates a version snapshot. Immutable history
accessible via GET /annotations/{slide_id}/{id}/history."
```

---

### Task 6: Quiz Mode Scoring

**Files:**
- Modify: `frontend/src/components/AnnotationLayer.js`
- Modify: `frontend/src/components/DrawingTools.js`

- [ ] **Step 1: Track quiz stats in AnnotationLayer**

Add to constructor:
```javascript
        this._quizStats = { total: 0, revealed: 0 };
```

In render(), when quiz mode is on, count total annotations:
```javascript
        if (this._quizMode) this._quizStats.total = annotations.length;
```

In the canvas-click reveal handler, increment:
```javascript
        this._quizStats.revealed++;
        eventBus.emit(Events.QUIZ_SCORE_UPDATE, {
            revealed: this._quizStats.revealed,
            total: this._quizStats.total,
        });
```

- [ ] **Step 2: Add score overlay**

Create a small overlay showing "12/30 revealed" that updates on each reveal.

- [ ] **Step 3: Show summary on quiz mode OFF**

When Q is pressed to disable quiz mode, show a toast with the final score:
```
"Quiz terminé : 22/30 annotations révélées (73%)"
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(annotations): add quiz mode scoring counter and summary"
```

---

### Task 7: Honest AI Dashboard Message

**Files:**
- Modify: `frontend/src/components/DashboardPanel.js`

- [ ] **Step 1: Replace motivational text**

Replace "Each correction trains the AI for better diagnoses" with:
```
"Vos corrections sont enregistrees pour le prochain cycle d'amelioration du modele."
```

Add last-trained date if available from ML health endpoint:
```
"Dernier entrainement : [date]. Corrections depuis : [count]."
```

- [ ] **Step 2: Commit**

```bash
git commit -m "fix(dashboard): replace misleading AI training message with transparent status"
```

---

### Task 8: Final Verification + Push

- [ ] **Step 1: Backend lint + migration test**
- [ ] **Step 2: Frontend lint (0 errors)**
- [ ] **Step 3: Manual regression test**
- [ ] **Step 4: Push + update PR**
