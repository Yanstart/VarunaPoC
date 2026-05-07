# Annotation Phase A — Fondations Cliniques

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add notes, validation states, undo/redo, and keyboard-driven AI correction to the annotation system so pathologists can work at clinical speed.

**Architecture:** Extend the existing Annotation model with `notes`, `status` (pending/validated/rejected), `validated_by`, `validated_at` fields. Add an undo/redo history stack to AnnotationStore. Wire V/X/Tab keyboard shortcuts to the DetectionPanel's accept/reject logic via EventBus. Add a notes popover that appears when an annotation is selected.

**Tech Stack:** PostgreSQL + Alembic (backend), Vanilla JS + EventBus (frontend), existing AnnotationStore + DrawingTools pipeline

**Pathologist interview reference:** `docs/research/2026-03-18-pathologist-interview-annotation-workflow.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/models/annotation.py` | Modify | Add `notes`, `status`, `validated_by`, `validated_at` columns |
| `backend/schemas/annotation.py` | Modify | Add fields to Create/Update/Response schemas |
| `backend/alembic/versions/008_annotation_notes_and_status.py` | Create | Migration for new columns |
| `backend/routes/annotations.py` | Modify | Add `PATCH .../validate` and `PATCH .../reject` convenience endpoints |
| `frontend/src/core/Constants.js` | Modify | Add new events (ANNOTATION_VALIDATED, UNDO, REDO, etc.) |
| `frontend/src/services/ApiService.js` | Modify | Add validate/reject/updateNotes methods + PATCH support |
| `frontend/src/services/AnnotationStore.js` | Modify | Add undo/redo stack, validateAnnotation(), rejectAnnotation() |
| `frontend/src/components/DrawingTools.js` | Modify | Remap keyboard shortcuts (V=validate, D=draw, etc.) |
| `frontend/src/components/AnnotationNotes.js` | Create | Inline notes popover for selected annotations |
| `frontend/src/css/annotation-notes.css` | Create | Styles for notes popover |
| `frontend/src/components/DetectionPanel.js` | Modify | Wire Tab/V/X keys for sequential validation |

---

### Task 1: Backend — Extend Annotation Model + Migration

**Files:**
- Modify: `backend/models/annotation.py`
- Modify: `backend/schemas/annotation.py`
- Create: `backend/alembic/versions/008_annotation_notes_and_status.py`

- [ ] **Step 1: Add columns to ORM model**

In `backend/models/annotation.py`, add after the `properties` field (line 44):

```python
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default=text("'pending'")
    )  # pending, validated, rejected
    validated_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Update Pydantic schemas**

In `backend/schemas/annotation.py`:

Add to `AnnotationCreate` (after `created_by` line 61):
```python
    notes: str | None = Field(None, max_length=2000)
```

Add to `AnnotationUpdate` (after `properties` line 70):
```python
    notes: str | None = Field(None, max_length=2000)
    status: str | None = Field(None, pattern=r"^(pending|validated|rejected)$")
    validated_by: str | None = None
```

Add to `AnnotationResponse` (after `properties` line 82):
```python
    notes: str | None
    status: str
    validated_by: str | None
    validated_at: datetime | None
```

- [ ] **Step 3: Create migration 008**

Create `backend/alembic/versions/008_annotation_notes_and_status.py`:

```python
"""Add notes, status, validated_by, validated_at to annotations

Revision ID: 008
Revises: 006
Create Date: 2026-03-18
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("annotations", sa.Column("notes", sa.String(2000), nullable=True))
    op.add_column(
        "annotations",
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )
    op.add_column("annotations", sa.Column("validated_by", sa.String(200), nullable=True))
    op.add_column(
        "annotations",
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_annotations_status", "annotations", ["status"])


def downgrade() -> None:
    op.drop_index("idx_annotations_status", table_name="annotations")
    op.drop_column("annotations", "validated_at")
    op.drop_column("annotations", "validated_by")
    op.drop_column("annotations", "status")
    op.drop_column("annotations", "notes")
```

- [ ] **Step 4: Run migration and tests**

```bash
cd backend && alembic upgrade head
cd backend && pytest tests/test_annotations_api.py -v --timeout=30
```

- [ ] **Step 5: Commit**

```bash
git add backend/models/annotation.py backend/schemas/annotation.py backend/alembic/versions/008_annotation_notes_and_status.py
git commit -m "feat(annotations): add notes, status, and validation audit fields

Extends the annotation model with:
- notes: free-text pathologist comments (max 2000 chars)
- status: pending/validated/rejected for AI correction workflow
- validated_by/validated_at: audit trail for validation actions"
```

---

### Task 2: Backend — Validate/Reject Convenience Endpoints

**Files:**
- Modify: `backend/routes/annotations.py`

- [ ] **Step 1: Add validate and reject PATCH endpoints**

Add after the existing PUT endpoint:

```python
@router.patch("/{slide_id}/{annotation_id}/validate")
async def validate_annotation(
    slide_id: str,
    annotation_id: UUID,
    notes: str | None = Query(None, max_length=2000),
    current_user: CurrentUser = Depends(require_role("MEDECIN")),
    db: AsyncSession = Depends(get_db),
):
    """Mark an annotation as validated by the current pathologist."""
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id,
            Annotation.slide_id == slide_id,
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(404, "Annotation not found")

    annotation.status = "validated"
    annotation.validated_by = current_user.username
    annotation.validated_at = datetime.now(UTC)
    if notes is not None:
        annotation.notes = notes

    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.patch("/{slide_id}/{annotation_id}/reject")
async def reject_annotation(
    slide_id: str,
    annotation_id: UUID,
    notes: str | None = Query(None, max_length=2000),
    current_user: CurrentUser = Depends(require_role("MEDECIN")),
    db: AsyncSession = Depends(get_db),
):
    """Mark an annotation as rejected (false positive)."""
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id,
            Annotation.slide_id == slide_id,
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(404, "Annotation not found")

    annotation.status = "rejected"
    annotation.validated_by = current_user.username
    annotation.validated_at = datetime.now(UTC)
    if notes is not None:
        annotation.notes = notes

    await db.commit()
    await db.refresh(annotation)
    return annotation
```

Ensure imports exist: `from datetime import UTC, datetime` and `from sqlalchemy import select`.

- [ ] **Step 2: Lint + commit**

```bash
cd backend && ruff check routes/annotations.py && ruff format routes/annotations.py
git add backend/routes/annotations.py
git commit -m "feat(annotations): add validate/reject PATCH endpoints

PATCH /annotations/{slide_id}/{id}/validate - marks as validated
PATCH /annotations/{slide_id}/{id}/reject - marks as rejected
Both record the pathologist name and timestamp for audit."
```

---

### Task 3: Frontend — Add Events + ApiService Methods

**Files:**
- Modify: `frontend/src/core/Constants.js`
- Modify: `frontend/src/services/ApiService.js`

- [ ] **Step 1: Add events to Constants.js**

After existing annotation events, add:
```javascript
    ANNOTATION_VALIDATED: 'annotation:validated',
    ANNOTATION_REJECTED: 'annotation:rejected',
    ANNOTATION_NOTES_CHANGED: 'annotation:notesChanged',
    UNDO: 'history:undo',
    REDO: 'history:redo',
    DETECTION_VALIDATE_CURRENT: 'detection:validateCurrent',
    DETECTION_REJECT_CURRENT: 'detection:rejectCurrent',
    DETECTION_NEXT: 'detection:next',
    VIEWER_ZOOM_PRESET: 'viewer:zoomPreset',
```

- [ ] **Step 2: Add PATCH method + annotation API methods to ApiService.js**

Add generic PATCH if missing:
```javascript
    async patch(url, data = {}) {
        return this._request(url, { method: 'PATCH', body: JSON.stringify(data) });
    }
```

Add annotation methods:
```javascript
    async validateAnnotation(slideId, annotationId, notes = null) {
        const params = notes ? `?notes=${encodeURIComponent(notes)}` : '';
        return this.patch(`/api/v1/annotations/${slideId}/${annotationId}/validate${params}`);
    }

    async rejectAnnotation(slideId, annotationId, notes = null) {
        const params = notes ? `?notes=${encodeURIComponent(notes)}` : '';
        return this.patch(`/api/v1/annotations/${slideId}/${annotationId}/reject${params}`);
    }

    async updateAnnotationNotes(slideId, annotationId, notes) {
        return this.put(`/api/v1/annotations/${slideId}/${annotationId}`, { notes });
    }
```

- [ ] **Step 3: Lint + commit**

```bash
cd frontend && npx eslint src/core/Constants.js src/services/ApiService.js
git add frontend/src/core/Constants.js frontend/src/services/ApiService.js
git commit -m "feat(annotations): add validation events and API methods

New events: ANNOTATION_VALIDATED/REJECTED, UNDO/REDO, DETECTION_VALIDATE/REJECT/NEXT
New API: validateAnnotation, rejectAnnotation, updateAnnotationNotes, patch()"
```

---

### Task 4: Frontend — Undo/Redo Stack + Validation in AnnotationStore

**Files:**
- Modify: `frontend/src/services/AnnotationStore.js`

- [ ] **Step 1: Add history stack to constructor (after line 52)**

```javascript
        /** @type {Array<Object>} Undo history stack */
        this._undoStack = [];
        /** @type {Array<Object>} Redo history stack */
        this._redoStack = [];
        /** @type {number} Max history size */
        this._maxHistory = 50;
```

- [ ] **Step 2: Add undo/redo methods after clear()**

Add `_pushHistory(type, annotation, previousState)`, `undo()`, `redo()`, `canUndo`, `canRedo`.

The `undo()` method reverses the last action: undo create = API delete, undo delete = API re-create, undo update = API restore previous state. `redo()` replays the undone action.

- [ ] **Step 3: Wire _pushHistory into existing CRUD**

In `createAnnotation()` after setting in map: `this._pushHistory('create', annotation);`
In `deleteAnnotation()` before deleting: snapshot, then `this._pushHistory('delete', snapshot);`
In `updateAnnotation()` before setting: save prev, then `this._pushHistory('update', annotation, prev);`

- [ ] **Step 4: Add validate/reject/updateNotes methods**

```javascript
    async validateAnnotation(annotationId, notes = null) {
        if (!this.slideId) return null;
        try {
            const annotation = await apiService.validateAnnotation(this.slideId, annotationId, notes);
            this.annotations.set(annotation.id, annotation);
            eventBus.emit(Events.ANNOTATION_VALIDATED, { annotation });
            eventBus.emit(Events.ANNOTATION_UPDATED, { annotation });
            return annotation;
        } catch (err) {
            console.error('[AnnotationStore] Validation failed:', err);
            return null;
        }
    }

    async rejectAnnotation(annotationId, notes = null) {
        if (!this.slideId) return null;
        try {
            const annotation = await apiService.rejectAnnotation(this.slideId, annotationId, notes);
            this.annotations.set(annotation.id, annotation);
            eventBus.emit(Events.ANNOTATION_REJECTED, { annotation });
            eventBus.emit(Events.ANNOTATION_UPDATED, { annotation });
            return annotation;
        } catch (err) {
            console.error('[AnnotationStore] Rejection failed:', err);
            return null;
        }
    }

    async updateNotes(annotationId, notes) {
        if (!this.slideId) return null;
        try {
            const annotation = await apiService.updateAnnotationNotes(this.slideId, annotationId, notes);
            this.annotations.set(annotation.id, annotation);
            eventBus.emit(Events.ANNOTATION_NOTES_CHANGED, { annotation });
            return annotation;
        } catch (err) {
            console.error('[AnnotationStore] Notes update failed:', err);
            return null;
        }
    }
```

- [ ] **Step 5: Clear history on slide change**

In `clear()` and `setSlide()`: `this._undoStack = []; this._redoStack = [];`

- [ ] **Step 6: Lint + commit**

```bash
cd frontend && npx eslint src/services/AnnotationStore.js
git add frontend/src/services/AnnotationStore.js
git commit -m "feat(annotations): add undo/redo stack and validation methods

Undo/redo with 50-action history, persisted to backend.
Ctrl+Z undoes create/delete/update. Ctrl+Y redoes.
New methods: validateAnnotation, rejectAnnotation, updateNotes."
```

---

### Task 5: Frontend — Remap Keyboard Shortcuts for Clinical Workflow

**Files:**
- Modify: `frontend/src/components/DrawingTools.js:387-402`

- [ ] **Step 1: Replace _handleKeyDown switch block**

New mapping:
- S=Select, D=Draw(freehand), R=Rect, P=Polygon, M=Point, C=Circle, L=ruLer
- V=Validate AI, X=Reject AI, Tab=Next detection
- Ctrl+Z=Undo, Ctrl+Y=Redo
- H=Hide/show overlays, 1-5=Zoom presets
- Escape=Cancel+select, Delete/Backspace=delete selected
- Input guard: skip shortcuts when typing in input/textarea

Add import: `import { annotationStore } from '../services/AnnotationStore.js';`
Add state: `this._overlaysVisible = true;` in constructor

- [ ] **Step 2: Lint + commit**

```bash
cd frontend && npx eslint src/components/DrawingTools.js
git add frontend/src/components/DrawingTools.js frontend/src/core/Constants.js
git commit -m "feat(annotations): remap keyboard shortcuts for clinical workflow

D=Draw(freehand), S=Select, V=Validate AI, X=Reject AI, Tab=Next detection
Ctrl+Z/Y=Undo/Redo, H=toggle overlays, 1-5=zoom presets, Escape=cancel+select
Input guard: shortcuts disabled when typing in input/textarea fields."
```

---

### Task 6: Frontend — Wire V/X/Tab into DetectionPanel

**Files:**
- Modify: `frontend/src/components/DetectionPanel.js`

- [ ] **Step 1: Add event listeners for DETECTION_VALIDATE_CURRENT, DETECTION_REJECT_CURRENT, DETECTION_NEXT**

In `_setupEventListeners()`, listen for the three new events. On validate: call `_toggleAccept(highlightedIndex)` then advance. On reject: call `_toggleReject(highlightedIndex)` then advance. On next: advance.

- [ ] **Step 2: Add `_goToNextDetection()` method**

Navigate to next visible detection (skip hidden and rejected zones). Wraps around.

- [ ] **Step 3: Lint + commit**

```bash
cd frontend && npx eslint src/components/DetectionPanel.js
git add frontend/src/components/DetectionPanel.js
git commit -m "feat(detection): wire V/X/Tab keyboard shortcuts for fast AI correction

V=validate current detection, X=reject, Tab=next visible zone.
Sequential workflow: validate/reject auto-advances to next zone."
```

---

### Task 7: Frontend — Annotation Notes Popover Component

**Files:**
- Create: `frontend/src/components/AnnotationNotes.js`
- Create: `frontend/src/css/annotation-notes.css`
- Modify: `frontend/src/main.js` (import CSS + instantiate)

- [ ] **Step 1: Create AnnotationNotes.js**

Component that:
- Listens to ANNOTATION_SELECTED events
- Shows a popover with: type badge (AI/manual), confidence %, status badge, label, author+date info
- Textarea for notes (auto-saves on blur or Ctrl+Enter)
- Validate/Reject buttons (visible only for pending status)
- All DOM creation uses safe methods (createElement, textContent) — NO innerHTML with user content

- [ ] **Step 2: Create annotation-notes.css**

Dark theme matching existing design. Positioned bottom-left of viewer area.
Status badges: pending=gray, validated=green, rejected=red.

- [ ] **Step 3: Import and instantiate**

In main.js, import CSS and create AnnotationNotes instance in the viewer area.

- [ ] **Step 4: Lint + commit**

```bash
cd frontend && npx eslint src/components/AnnotationNotes.js
git add frontend/src/components/AnnotationNotes.js frontend/src/css/annotation-notes.css frontend/src/main.js
git commit -m "feat(annotations): add inline notes popover with validation actions

Shows notes, status, confidence, author, and timestamp when an annotation
is selected. Validate/Reject buttons for AI correction. Notes auto-save
on blur or Ctrl+Enter."
```

---

### Task 8: Final Verification

- [ ] **Step 1: Backend lint + tests**

```bash
cd backend && ruff check . && pytest --timeout=30
```

- [ ] **Step 2: Frontend lint**

```bash
cd frontend && npm run lint
```

- [ ] **Step 3: Manual regression test**

1. Load slide, create freehand annotation (D key)
2. Ctrl+Z undoes the annotation, Ctrl+Y redoes
3. Run ML detection, Tab through zones
4. V validates, X rejects (auto-advances)
5. Click annotation — notes popover appears with metadata
6. Type note, blur — note saved
7. H toggles all overlays
8. 1-5 keys change zoom

- [ ] **Step 4: Push**

```bash
git push -u origin fix/detection-navigation-151
```
