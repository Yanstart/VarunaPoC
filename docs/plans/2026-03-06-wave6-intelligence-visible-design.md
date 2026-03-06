# Wave 6 — Intelligence Visible

**Date:** 2026-03-06
**Status:** Approved
**Context:** End of Phase 2, entering Phase 3. All 62 original issues closed. Wave 5 (Robustesse ML) partially resolved via adaptive magnification and viewport inference.

---

## Problem Statement

ML features (heatmap, detection, focus zones, cell counting) are technically functional but violate the project's Radical Simplicity principle: pathologists cannot see, navigate, or interact with ML results effectively.

Root causes identified through testing:
1. **Heatmap invisible** — canvas overlay (z-index 150) hidden behind annotation SVG (z-index 200)
2. **Detection zones not navigable** — drawn as preview polygons but not clickable/toggleable
3. **Focus zones disconnected** — `focus:zone-selected` event emitted but zero listeners; no visual overlay on slide
4. **Cell counts abstract** — numbers without spatial mapping on the slide
5. **Auth breaks tiles** — OSD ajaxHeaders snapshot expires; AUTH_TOKEN_REFRESHED event never emitted
6. **No unified legend** — each ML feature uses different colors with no global reference

## Design Principle: ML Results as First-Class Visual Elements

Instead of treating ML outputs as separate overlay systems, make them visually consistent with annotations: same legend panel, same toggle pattern, same interaction model. This serves all three differentiators:

- **Radical Simplicity**: one visual language — learn annotations, know ML results
- **Quality-First**: ML results become reviewable through familiar annotation patterns
- **Continuous Learning** (future): pathologist corrections on ML-generated elements become training data

## Issues

### Issue A: Auth Token Refresh for Tile Loading

**Problem:** OSD ajaxHeaders set at viewer creation with token snapshot. After Keycloak token refresh, tiles fail 401. `AUTH_TOKEN_REFRESHED` constant defined but never emitted or consumed.

**Fix:**
1. `AuthService._setTokens()` — emit `AUTH_TOKEN_REFRESHED` after silent refresh
2. `ViewerInstance` — listen for `AUTH_TOKEN_REFRESHED`, update `ajaxHeaders` on the OSD viewer

**Acceptance criteria:** Tiles continue loading after token refresh without page reload.

### Issue B1: Heatmap Overlay Visibility

**Problem:** HeatmapOverlay canvas at z-index 150 is hidden behind AnnotationLayer SVG at z-index 200.

**Fix:**
1. Reorder z-index: AnnotationLayer SVG = 100, HeatmapOverlay = 200
2. Set `pointer-events: none` on heatmap canvas so annotations remain clickable
3. Add opacity slider in MLPanel results view (0-100%, default 70%)

**Acceptance criteria:** Heatmap visible on top of slide, annotations still interactive through it.

### Issue B2: Detection Zone Navigation

**Problem:** Detected zones are drawn as dashed orange polygons on AnnotationLayer `<g class="previews">` but cannot be clicked, listed, or toggled.

**Fix:**
1. Add detection results list in DetectionPanel (zone name, confidence, area)
2. Click on list item → viewer pans/zooms to zone bbox
3. Toggle visibility of detection overlay per-zone or all-at-once
4. Use consistent color from the global legend

**Acceptance criteria:** Each detected zone is listed, clickable (navigates viewer), and toggleable.

### Issue B3: Focus Zone Navigation and Display

**Problem:** FocusAssistPanel emits `focus:zone-selected` with zone data (including bbox) but nothing listens. Zones are listed in panel text but not drawn on the slide.

**Fix:**
1. Draw focus zones on a dedicated SVG group (or reuse AnnotationLayer previews) with distinct color
2. Listen for `focus:zone-selected` in ViewerInstance → `fitBounds()` to zone bbox
3. Register the event constant in Constants.js (currently a string literal)

**Acceptance criteria:** Focus zones are visible on slide, clicking a zone in the panel navigates the viewer to it.

### Issue B4: Unified Color Legend

**Problem:** ML outputs (heatmap jet colormap, orange detection polygons, focus zones, cell count markers) each use ad-hoc colors. No global legend assists the pathologist.

**Fix:**
1. Create `ColorLegendPanel` component — collapsible panel showing all active visual layers
2. Entries: annotation labels (existing colors), heatmap gradient, detection zones, focus zones, cell markers
3. Each entry has a visibility toggle (eye icon) matching the layer control pattern
4. Legend updates dynamically as ML analyses complete

**Acceptance criteria:** Pathologist sees a single legend panel with all active overlays and can toggle each.

### Issue C: Cell Counting Visual Markers

**Problem:** Cell counts display total/positive/negative numbers but no spatial markers on the slide. Pathologist cannot see which cells were counted or verify individual classifications.

**Fix:**
1. After count results, draw circle markers on slide at cell locations (if backend returns coordinates)
2. Color-code: positive = configurable color (default red), negative = configurable (default blue)
3. Hover on marker shows cell ID/classification
4. If backend does not return per-cell coordinates (current state), add a note in the UI and file a backend follow-up issue

**Acceptance criteria:** If coordinates available: markers visible, hoverable, color-coded. If not: clear message explaining current limitation + backend issue created.

### Issue D: Close Resolved Wave 5 Issues

Issues already resolved by adaptive magnification and viewport inference implementation:
- #141 ML: MPP override pour lames sans metadonnee de resolution
- #142 ML: Inference par region (viewport-only) pour eviter la surcharge serveur
- #143 ML: Background worker pour inference non-bloquante

**Action:** Close with implementation references.

### Issue E: Clustering Overlay Error Recovery (#155)

**Problem:** After a 429 rate limit error, the clustering overlay persists and toggle checkbox stops working.

**Fix:** Reset overlay state on error, ensure toggle works regardless of previous errors.

### Issue F: Detection Region Support (#156)

**Problem:** `/ml/detect` endpoint does not accept a region parameter. Detection always processes the entire slide.

**Fix:** Add region filtering to detect endpoint using same wsi.grid approach as predict.

### Issue G: ML Progress Feedback (#157)

**Problem:** ML analyses take 30-120s on CPU. Only a spinner is shown — no progress indication.

**Fix:** Expose tile count progress from backend (SSE or polling), display progress bar in panels.

### Issue H: ML Compare Mode (#158)

**Problem:** Viewer supports split comparison for two slides, but not before/after ML overlay toggle.

**Fix:** Keyboard shortcut (M) to toggle all ML overlays, split view option.

### Issue I: ML Retry with Backoff (#159)

**Problem:** 429/503 errors shown as definitive failures. No automatic retry.

**Fix:** Exponential backoff retry (3 attempts) in ApiService for ML endpoints.

### Issue J: Quality-ML Cross-Validation (#160)

**Problem:** Image quality score and ML results are shown independently. No warning when analyzing a low-quality slide.

**Fix:** Warning banner in ML panels when quality < 50%.

### Issue K: ML Results Export (#161)

**Problem:** ML results cannot be exported. Pathologists need documented analyses.

**Fix:** CSV/PDF export from ML panels with slide metadata and results.

## Dependency Map

```
D (close Wave 5) — done
A (#149 auth refresh) — no dependency, critical path
B1 (#150 heatmap z-index) — no dependency
B4 (#153 color legend) — no dependency, informs B2/B3
B2 (#151 detection navigation) — depends on B4 color choices
B3 (#152 focus zone navigation) — depends on B4 color choices
C (#154 cell counting markers) — depends on backend capability check
E (#155 clustering error recovery) — no dependency
F (#156 detection region) — no dependency
G (#157 ML progress) — no dependency
H (#158 compare mode) — depends on B1 (overlay visibility)
I (#159 retry backoff) — no dependency
J (#160 quality cross-validation) — no dependency
K (#161 ML export) — depends on B2, C (need data to export)
```

### Suggested implementation order (3 batches)

**Batch 1 — Critical fixes:**
A (#149), B1 (#150), B4 (#153), E (#155), I (#159)

**Batch 2 — Navigation and interaction:**
B2 (#151), B3 (#152), F (#156), J (#160)

**Batch 3 — Advanced UX:**
C (#154), G (#157), H (#158), K (#161)

## Extended Issues — Pathologist Workflow UX

### Issue L: Measurement Tool with Physical Units (#162)
**Problem:** No interactive ruler tool. No area/perimeter display. No scalebar. Pathologists measure daily.
**Fix:** Ruler tool in DrawingTools + scalebar overlay + area display for polygons, all using MPP.
**Differentiator:** Radical Simplicity — digital equivalent of the ocular micrometer.

### Issue M: Detection Correction Workflow (#163)
**Problem:** "Corriger" button submits 'refined' feedback but captures NO corrected geometry.
**Fix:** Activate drawing tool on "Corriger", pre-select label, capture new geometry with feedback.
**Differentiator:** Quality-First + Continuous Learning — expert corrections are high-value training data.

### Issue N: Annotation Save Error Feedback (#164)
**Problem:** `createAnnotation()` returns null silently. Pathologist loses their drawing with no explanation.
**Fix:** Visible toast on failure, retain unsaved annotation locally, retry button.

### Issue O: Global Toast Notification System (#165)
**Problem:** ML errors only visible inside individual panels. No global notification.
**Fix:** `ToastNotification` component listening to all EventBus error/success events.

### Issue P: Sequential Zone Navigation (#166)
**Problem:** No Next/Previous for detections/zones. Must click each item manually.
**Fix:** Next/Previous buttons + keyboard shortcuts (N/B) in DetectionPanel and FocusAssistPanel.

### Issue Q: Slide Metadata Panel (#167)
**Problem:** No MetadataPanel despite i18n key existing. Scanner, MPP, date inaccessible.
**Fix:** MetadataPanel in sidebar showing OpenSlide properties with physical unit conversion.

### Issue R: Multi-Stain Comparison from CaseSidebar (#168)
**Problem:** CaseSidebar replaces current slide instead of offering compare. SimilarityPanel opens new window.
**Fix:** "Comparer" button per slide → CompareLayout with both slides.
**Differentiator:** Radical Simplicity — one click for the daily H&E vs Ki-67 comparison.

### Issue S: Case Summary in Sidebar (#169)
**Problem:** No annotation count, quality badge, or completion status per slide in CaseSidebar.
**Fix:** Parallel fetch of counts/quality per slide, progress indicator, "Mark as done" button.

### Issue T: Quality Auto-Assessment on Load (#170)
**Problem:** QualityBadge requires click to evaluate. Should be automatic for a diagnostic tool.
**Fix:** Auto-trigger assessment on slide load, toast if quality < 50%.

### Issue U: Mount SimilarityPanel in Viewer (#171)
**Problem:** SimilarityPanel component is complete but never instantiated in main.js.
**Fix:** Mount in ML sidebar, wire results to CompareLayout instead of window.open().

### Issue V: Sync Mode Selector (#172)
**Problem:** SyncController supports 3 modes but UI only exposes on/off toggle.
**Fix:** Dropdown with full/pan-only/zoom-only modes.

### Issue W: Detection Preview Click Handler (#173)
**Problem:** SVG detection previews have cursor:pointer but no click handler. Bidirectional link missing.
**Fix:** Click preview → highlight in panel. Click panel item → highlight preview on slide.

### Issue X: ML Panel Reorganization — Tabs vs Accordions (#174)
**Problem:** 5 collapsed accordions stacked vertically. Hard to find, violates Radical Simplicity.
**Fix:** Tab-based or grouped layout. Badge notifications on tabs with results.

### Issue Y: Accessibility — ARIA, Focus, Contrast (#175)
**Problem:** No role attributes, no aria-pressed, no focus management, marginal contrast.
**Fix:** role="button" + aria-expanded on accordions, aria-pressed on tools, focus trapping, contrast fix.

### Issue Z: Connect I18nService (#176)
**Problem:** Complete i18n infrastructure (5 languages) built but zero calls from components.
**Fix:** Init service, connect visible strings, add language selector.
**Differentiator:** Radical Simplicity — 3-minute onboarding impossible in French-only for international staff.

### Issue AA: Light Theme Toggle (#177)
**Problem:** CSS light theme variables fully defined but no switch to activate them.
**Fix:** Theme toggle in user menu, localStorage persistence, respect prefers-color-scheme.

## Out of Scope (Deferred to Cercle 1-2)

- ML results becoming editable annotations (Cercle 1: Quality-First complete)
- Feedback loops from corrections to retraining (Cercle 2: Continuous Learning)
- Multi-model ensemble predictions (Cercle 2: MLOps)

## GitHub Issues Summary

### ML Pipeline & Integration (13 issues)

| # | Title | Priority | Batch |
|---|-------|----------|-------|
| #149 | Auth token refresh pour tuiles OSD | High | 1 |
| #150 | Pipeline heatmap — 9 bugs (affichage, cache, formats, erreurs) | High | 1 |
| #151 | Navigation et toggle zones detection | Medium | 2 |
| #152 | Affichage et navigation zones FocusAssist | Medium | 2 |
| #153 | Legende de couleurs unifiee | Medium | 1 |
| #154 | Marqueurs visuels comptage cellulaire | Medium | 3 |
| #155 | Overlay clustering apres erreur 429 | Low | 1 |
| #156 | Detection endpoint region viewport | Medium | 2 |
| #157 | Feedback progression analyses ML | Medium | 3 |
| #158 | Mode comparaison avant/apres ML | Low | 3 |
| #159 | Retry automatique 429/503 | Medium | 1 |
| #160 | Qualite-ML validation croisee | Low | 2 |
| #161 | Export resultats ML PDF/CSV | Low | 3 |

### Pathologist Workflow UX (16 issues)

| # | Title | Priority | Batch |
|---|-------|----------|-------|
| #162 | Outil de mesure (regle) + scalebar | High | 2 |
| #163 | Workflow correction detection (dessin) | High | 2 |
| #164 | Erreur sauvegarde annotation visible | High | 1 |
| #165 | Systeme notification global (toast) | High | 1 |
| #166 | Navigation sequentielle zones (N/B) | Medium | 2 |
| #167 | Panneau metadonnees lame | Medium | 3 |
| #168 | Comparaison multi-coloration CaseSidebar | Medium | 3 |
| #169 | Resume de cas (annotations, qualite, etat) | Medium | 3 |
| #170 | Qualite auto-evaluee au chargement | Medium | 2 |
| #171 | Monter SimilarityPanel dans viewer | Low | 3 |
| #172 | Selecteur mode synchronisation | Low | 4 |
| #173 | Detection preview SVG cliquable | Medium | 2 |
| #174 | Reorganiser panels ML (onglets) | Medium | 3 |
| #175 | Accessibilite ARIA, focus, contraste | Medium | 4 |
| #176 | Connecter I18nService | Low | 4 |
| #177 | Theme clair toggle | Low | 4 |
