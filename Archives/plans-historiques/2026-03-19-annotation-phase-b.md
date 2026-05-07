# Annotation Phase B — Intelligence Visible

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add arrow+text annotations, reporting sidebar, quiz mode for residents, and AI contribution dashboard — completing the pathologist's clinical annotation toolkit.

**Architecture:** Arrow tool stores geometry as GeoJSON LineString with text in `properties.text`. Reporting panel aggregates annotation data from existing `/stats` endpoint extended with validation breakdown. Quiz mode is a toggle on AnnotationLayer that hides annotation text/labels until clicked. Dashboard is a lightweight component showing correction counts from a new backend endpoint.

**Tech Stack:** SVG (arrow rendering), existing EventBus + AnnotationStore pipeline, FastAPI stats endpoint

**Pathologist reference:** `docs/research/2026-03-18-pathologist-interview-annotation-workflow.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/components/DrawingTools.js` | Modify | Add arrow tool (F key), text input on finish |
| `frontend/src/components/AnnotationLayer.js` | Modify | Render arrow geometry (SVG line + arrowhead + text) |
| `frontend/src/css/annotation-layer.css` | Modify | Arrow marker + text styles |
| `frontend/src/components/ReportingPanel.js` | Create | Sidebar: who annotated, when, validation stats, export |
| `frontend/src/css/reporting-panel.css` | Create | Reporting panel styles |
| `backend/routes/annotations.py` | Modify | Extended stats endpoint with validation breakdown + contributor list |
| `frontend/src/services/ApiService.js` | Modify | getAnnotationReport() method |
| `frontend/src/components/AnnotationLayer.js` | Modify | Quiz mode: hide/reveal labels on click |
| `frontend/src/components/DrawingTools.js` | Modify | Quiz toggle (Q key) |
| `frontend/src/components/DashboardPanel.js` | Create | AI contribution stats panel |
| `frontend/src/css/dashboard-panel.css` | Create | Dashboard styles |

---

### Task 1: Arrow + Text Annotation Tool

**Files:**
- Modify: `frontend/src/components/DrawingTools.js`
- Modify: `frontend/src/components/AnnotationLayer.js`
- Modify: `frontend/src/css/annotation-layer.css`

- [ ] **Step 1: Add arrow tool to DrawingTools**

In `_onMouseDown`, add a case for `'arrow'` tool (same pattern as ruler — click start, click end):
```javascript
            case 'arrow':
                if (!this.isDrawing) {
                    this.isDrawing = true;
                    this._drawStartSlide = slideCoords;
                    eventBus.emit(Events.DRAWING_START, { tool: 'arrow' });
                } else {
                    this._finishArrow(slideCoords);
                }
                break;
```

In `_onMouseMove`, add arrow preview (reuse ruler preview pattern but with arrowhead):
```javascript
            case 'arrow':
                if (this.isDrawing) this._updateArrowPreview(slideCoords);
                break;
```

- [ ] **Step 2: Add arrow preview and finish methods**

After `_finishRuler()`, add:

```javascript
    _updateArrowPreview(current) {
        this._clearPreview();
        const start = this._drawStartSlide;
        if (!start) return;
        const previewGroup = this.annotationLayer.getPreviewGroup();

        // Arrow line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', start.x);
        line.setAttribute('y1', start.y);
        line.setAttribute('x2', current.x);
        line.setAttribute('y2', current.y);
        line.setAttribute('stroke', this.selectedLabel?.color || '#FF0000');
        line.setAttribute('stroke-width', this.annotationLayer._getStrokeWidth());
        line.setAttribute('stroke-dasharray', '6 4');
        line.setAttribute('marker-end', 'url(#arrowhead-preview)');
        previewGroup.appendChild(line);
    }

    async _finishArrow(end) {
        this.isDrawing = false;
        this._clearPreview();
        const start = this._drawStartSlide;
        if (!start) return;

        // Prompt for text
        const text = await this._promptArrowText();

        await annotationStore.createAnnotation({
            geometry: {
                type: 'LineString',
                coordinates: [[start.x, start.y], [end.x, end.y]],
            },
            geometry_type: 'arrow',
            annotation_type: 'manual',
            label_id: this.selectedLabel?.id,
            properties: { text: text || '' },
        });

        eventBus.emit(Events.DRAWING_END, { tool: 'arrow' });
    }

    _promptArrowText() {
        return new Promise((resolve) => {
            // Create inline text input near toolbar
            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'drawing-tools__arrow-text';
            input.placeholder = 'Note...';
            input.maxLength = 200;
            this.element.appendChild(input);
            input.focus();

            const finish = () => {
                const val = input.value.trim();
                input.remove();
                resolve(val);
            };
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') finish();
                if (e.key === 'Escape') { input.remove(); resolve(''); }
            });
            input.addEventListener('blur', finish);
        });
    }
```

- [ ] **Step 3: Add keyboard shortcut F=arrow**

In `_handleKeyDown`, change the existing `case 'f': case 'F':` from freehand to arrow. Move freehand to a different key or keep D=freehand and add F=arrow (fleche):

```javascript
            case 'f': case 'F':
                if (e.ctrlKey || e.metaKey) break;
                this._setTool('arrow');
                break;
```

Update the tool buttons array to include 'arrow' with an arrow icon SVG.

- [ ] **Step 4: Render arrows in AnnotationLayer**

In `_createAnnotationElement()`, add a case for `geometry_type === 'arrow'` or `geometry.type === 'LineString'`:

```javascript
            case 'LineString':
                el = this._createArrow(geom.coordinates, color, opacity, anno.properties?.text);
                break;
```

Add the `_createArrow` method:

```javascript
    _createArrow(coordinates, color, opacity, text) {
        if (!coordinates || coordinates.length < 2) return null;
        const [start, end] = coordinates;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.classList.add('annotation-arrow');

        // Ensure arrowhead marker exists in defs
        this._ensureArrowMarker(color);

        // Line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', start[0]);
        line.setAttribute('y1', start[1]);
        line.setAttribute('x2', end[0]);
        line.setAttribute('y2', end[1]);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', this._getStrokeWidth());
        line.setAttribute('stroke-opacity', opacity);
        line.setAttribute('marker-end', `url(#arrowhead-${color.replace('#', '')})`);
        g.appendChild(line);

        // Text label near the endpoint
        if (text) {
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', end[0]);
            label.setAttribute('y', end[1] - this._getStrokeWidth() * 3);
            label.setAttribute('fill', color);
            label.setAttribute('font-size', this._getStrokeWidth() * 5);
            label.setAttribute('font-family', 'sans-serif');
            label.classList.add('annotation-arrow__text');
            label.textContent = text;
            g.appendChild(label);
        }

        return g;
    }

    _ensureArrowMarker(color) {
        const defs = this.svg.querySelector('defs');
        const markerId = `arrowhead-${color.replace('#', '')}`;
        if (defs.querySelector(`#${markerId}`)) return;

        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', markerId);
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '7');
        marker.setAttribute('refX', '10');
        marker.setAttribute('refY', '3.5');
        marker.setAttribute('orient', 'auto');
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3.5, 0 7');
        polygon.setAttribute('fill', color);
        marker.appendChild(polygon);
        defs.appendChild(marker);
    }
```

- [ ] **Step 5: Add CSS for arrows and text input**

In `annotation-layer.css`:
```css
.annotation-arrow__text {
    pointer-events: none;
    font-weight: 600;
    paint-order: stroke;
    stroke: rgba(0, 0, 0, 0.7);
    stroke-width: 3px;
}
```

In `drawing-tools.css`:
```css
.drawing-tools__arrow-text {
    position: absolute;
    left: 48px;
    top: 50%;
    transform: translateY(-50%);
    width: 180px;
    padding: 4px 8px;
    background: var(--color-bg-elevated, #1a1f2e);
    color: var(--color-text-primary, #e2e8f0);
    border: 1px solid var(--color-accent, #3b82f6);
    border-radius: 4px;
    font-size: 12px;
    z-index: 400;
}
```

- [ ] **Step 6: Lint + commit**

```bash
cd frontend && npx eslint src/components/DrawingTools.js src/components/AnnotationLayer.js
git add frontend/src/components/DrawingTools.js frontend/src/components/AnnotationLayer.js frontend/src/css/annotation-layer.css frontend/src/css/drawing-tools.css
git commit -m "feat(annotations): add arrow+text annotation tool

F key activates arrow tool. Click start -> click end -> type text.
Renders as SVG line with arrowhead marker and text label near tip.
Text stored in annotation properties.text field."
```

---

### Task 2: Backend — Extended Stats with Validation Breakdown

**Files:**
- Modify: `backend/routes/annotations.py`
- Modify: `backend/services/annotation_service.py`

- [ ] **Step 1: Add report endpoint**

After the existing `/stats` endpoint in `annotations.py`, add:

```python
@router.get("/{slide_id}/report")
async def get_annotation_report(
    slide_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Detailed annotation report: validation stats, contributor list, timeline.
    For the reporting panel and AI contribution dashboard.
    """
    result = await db.execute(
        select(Annotation).where(
            Annotation.slide_id == slide_id,
            Annotation.tenant_id == tenant_id,
        )
    )
    annotations = result.scalars().all()

    # Contributor breakdown
    contributors = {}
    validation_stats = {"pending": 0, "validated": 0, "rejected": 0}
    ai_corrections = {"total_ai": 0, "validated": 0, "rejected": 0, "corrected": 0}
    timeline = []

    for a in annotations:
        # Contributor stats
        author = a.created_by or "anonymous"
        if author not in contributors:
            contributors[author] = {"annotations": 0, "validations": 0, "rejections": 0}
        contributors[author]["annotations"] += 1

        # Validation stats
        status = getattr(a, "status", "pending")
        if status in validation_stats:
            validation_stats[status] += 1

        # Validator stats
        validator = a.validated_by
        if validator:
            if validator not in contributors:
                contributors[validator] = {"annotations": 0, "validations": 0, "rejections": 0}
            if status == "validated":
                contributors[validator]["validations"] += 1
            elif status == "rejected":
                contributors[validator]["rejections"] += 1

        # AI correction tracking
        if a.annotation_type in ("auto", "auto_confirmed"):
            ai_corrections["total_ai"] += 1
            if status == "validated":
                ai_corrections["validated"] += 1
            elif status == "rejected":
                ai_corrections["rejected"] += 1

        # Timeline (last 50)
        timeline.append({
            "id": str(a.id),
            "type": a.annotation_type,
            "status": status,
            "created_by": a.created_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "validated_by": a.validated_by,
            "validated_at": a.validated_at.isoformat() if a.validated_at else None,
            "label": a.label.name if a.label else None,
            "notes": a.notes,
        })

    timeline.sort(key=lambda x: x["created_at"] or "", reverse=True)

    return {
        "slide_id": slide_id,
        "total": len(annotations),
        "validation": validation_stats,
        "ai_corrections": ai_corrections,
        "contributors": contributors,
        "timeline": timeline[:50],
    }
```

- [ ] **Step 2: Add API method in frontend**

In `ApiService.js`:
```javascript
    async getAnnotationReport(slideId) {
        return this.get(`/api/v1/annotations/${slideId}/report`);
    }
```

- [ ] **Step 3: Lint + commit**

```bash
cd backend && ruff check routes/annotations.py && ruff format routes/annotations.py
cd frontend && npx eslint src/services/ApiService.js
git add backend/routes/annotations.py frontend/src/services/ApiService.js
git commit -m "feat(annotations): add report endpoint with validation breakdown

GET /annotations/{slide_id}/report returns validation stats,
contributor list, AI correction tracking, and activity timeline."
```

---

### Task 3: Reporting Panel (Sidebar)

**Files:**
- Create: `frontend/src/components/ReportingPanel.js`
- Create: `frontend/src/css/reporting-panel.css`
- Modify: `frontend/src/core/Router.js` (instantiate)
- Modify: `frontend/src/style.css` (import)

- [ ] **Step 1: Create ReportingPanel component**

A collapsible sidebar panel showing:
- Total annotations count
- Validation breakdown (pending/validated/rejected) with progress bar
- AI correction stats (AI total, validated %, rejected %)
- Contributor table (who, annotations count, validations, rejections)
- Activity timeline (last 20 entries with type, author, time, notes)
- Export button (existing exportGeoJSON)

Follows the exact same pattern as DetectionPanel/QualityPanel:
- Constructor with container + options
- `_create()` builds DOM with createElement/textContent only (NO innerHTML)
- `_setupEventListeners()` subscribes to ANNOTATIONS_LOADED, ANNOTATION_VALIDATED, ANNOTATION_REJECTED
- `_loadReport()` calls `apiService.getAnnotationReport(slideId)`
- Collapsible accordion header
- `_unsubscribers[]` pattern, `destroy()` method

- [ ] **Step 2: Create CSS**

Dark theme, matches existing panel styles. Positioned in the right sidebar alongside other panels.

Key elements:
- `.reporting-panel` — accordion container
- `.reporting-panel__stats` — grid of stat cards
- `.reporting-panel__progress` — validation progress bar (green/red/gray)
- `.reporting-panel__contributors` — compact table
- `.reporting-panel__timeline` — scrollable activity list (max-height: 200px)

- [ ] **Step 3: Wire into Router and style imports**

Add CSS import to `style.css`. Instantiate in Router alongside other panels.
Add `'reportingPanel'` to destroyKeys.

- [ ] **Step 4: Lint + commit**

```bash
cd frontend && npx eslint src/components/ReportingPanel.js
git add frontend/src/components/ReportingPanel.js frontend/src/css/reporting-panel.css frontend/src/core/Router.js frontend/src/style.css
git commit -m "feat(annotations): add reporting panel with contributor and timeline views

Shows validation breakdown, AI correction stats, contributor table,
and activity timeline. Updates on annotation events."
```

---

### Task 4: Quiz Mode for Resident Training

**Files:**
- Modify: `frontend/src/components/AnnotationLayer.js`
- Modify: `frontend/src/components/DrawingTools.js`
- Modify: `frontend/src/core/Constants.js`

- [ ] **Step 1: Add quiz mode state and event**

In `Constants.js`, add:
```javascript
    QUIZ_MODE_TOGGLE: 'quiz:toggle',
```

In `AnnotationLayer` constructor, add:
```javascript
        this._quizMode = false;
        this._revealedAnnotations = new Set();
```

- [ ] **Step 2: Implement quiz rendering in AnnotationLayer**

In `_setupEventListeners()`, add:
```javascript
        this._unsubscribers.push(
            eventBus.on(Events.QUIZ_MODE_TOGGLE, ({ enabled }) => {
                this._quizMode = enabled;
                this._revealedAnnotations.clear();
                this.render();
            }),
        );
```

Modify `_createAnnotationElement()` — when quiz mode is on, hide the label color and replace with neutral gray. The annotation shape is still visible but with no identifying color:
```javascript
        // Quiz mode: mask label colors until revealed
        if (this._quizMode && !this._revealedAnnotations.has(anno.id)) {
            color = '#6b7280'; // neutral gray
            // Don't render text labels for arrows
        }
```

In the `canvas-click` handler, when quiz mode is on and an annotation is clicked, reveal it:
```javascript
            // Quiz mode: reveal annotation on click
            if (this._quizMode && !this._revealedAnnotations.has(annotationId)) {
                this._revealedAnnotations.add(annotationId);
                this.render(); // Re-render with real colors
                return;
            }
```

- [ ] **Step 3: Add Q key shortcut**

In `DrawingTools._handleKeyDown()`:
```javascript
            case 'q': case 'Q':
                if (e.ctrlKey || e.metaKey) break;
                this._quizMode = !this._quizMode;
                eventBus.emit(Events.QUIZ_MODE_TOGGLE, { enabled: this._quizMode });
                eventBus.emit(Events.TOAST_SHOW, {
                    type: 'info',
                    message: this._quizMode ? 'Quiz mode ON' : 'Quiz mode OFF',
                    duration: 2000,
                });
                break;
```

Add `this._quizMode = false;` in constructor.

- [ ] **Step 4: Lint + commit**

```bash
cd frontend && npx eslint src/components/AnnotationLayer.js src/components/DrawingTools.js
git add frontend/src/components/AnnotationLayer.js frontend/src/components/DrawingTools.js frontend/src/core/Constants.js
git commit -m "feat(annotations): add quiz mode for resident training

Q key toggles quiz mode. Annotations show as neutral gray shapes.
Clicking reveals the real color and label. Useful for self-assessment
during pathology training."
```

---

### Task 5: AI Contribution Dashboard

**Files:**
- Create: `frontend/src/components/DashboardPanel.js`
- Create: `frontend/src/css/dashboard-panel.css`
- Modify: `frontend/src/core/Router.js`
- Modify: `frontend/src/style.css`

- [ ] **Step 1: Create DashboardPanel component**

Lightweight panel showing the pathologist's AI correction impact:
- Total AI detections on current slide
- Validated / Rejected / Pending counts with visual bars
- Accuracy indicator: "Your corrections improved model precision"
- Personal contribution count: "You validated X, rejected Y this session"

Data comes from the existing `/report` endpoint (same as ReportingPanel).

Key: this is motivational — it shows the pathologist their corrections matter.

Pattern: same as other panels. Collapsible, dark theme, `_unsubscribers[]`, `destroy()`.

Track session-level corrections locally (not persisted):
```javascript
this._sessionStats = { validated: 0, rejected: 0, corrected: 0 };
```

Listen to `ANNOTATION_VALIDATED` and `ANNOTATION_REJECTED` to increment counters.

- [ ] **Step 2: Create CSS**

Key visual: large numbers for validated/rejected counts, green/red color coding, progress ring or simple bar for AI accuracy.

- [ ] **Step 3: Wire into Router**

Same pattern as ReportingPanel.

- [ ] **Step 4: Lint + commit**

```bash
cd frontend && npx eslint src/components/DashboardPanel.js
git add frontend/src/components/DashboardPanel.js frontend/src/css/dashboard-panel.css frontend/src/core/Router.js frontend/src/style.css
git commit -m "feat(annotations): add AI contribution dashboard

Shows validation stats for current slide and session-level correction
counts. Motivates pathologists to correct AI detections by showing
their impact on model accuracy."
```

---

### Task 6: Final Verification

- [ ] **Step 1: Backend lint + tests**
```bash
cd backend && ruff check . && pytest --timeout=30
```

- [ ] **Step 2: Frontend lint**
```bash
cd frontend && npm run lint
```

- [ ] **Step 3: Manual test**

1. F key -> arrow tool, click start -> click end -> type text -> arrow annotation appears
2. Arrow visible on slide with text label at tip
3. Reporting panel shows validation breakdown + contributor table
4. Q key toggles quiz mode -> annotations turn gray
5. Click gray annotation -> reveals real color/label
6. Dashboard shows AI correction counts
7. V/X on detections -> dashboard counters update
8. All Phase A features still work (undo, notes, shortcuts)

- [ ] **Step 4: Push**
```bash
git push origin fix/detection-navigation-151
```
