/**
 * DrawingTools - Annotation drawing toolbar and handlers
 *
 * Provides drawing tools for creating annotations directly on the slide:
 * - Select: Click to select, drag to move
 * - Rectangle: Click-drag to draw
 * - Polygon: Click vertices, double-click to close
 * - Point: Single click marker
 * - Freehand: Draw freely + Douglas-Peucker simplification
 * - Circle: Click center + drag radius
 * - Ruler: Click two points to measure distance (physical units via MPP)
 *
 * Coordinates: screen px → OSD viewport → slide pixels
 *
 * @module components/DrawingTools
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { i18nService } from '../services/I18nService.js';

const TOOLS = ['select', 'rectangle', 'polygon', 'point', 'freehand', 'circle', 'ruler', 'arrow'];

/** localStorage key for last-used overflow tool */
const LAST_TOOL_KEY = 'varuna_last_tool';

const TOOL_ICONS = {
    select: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>',
    rectangle: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>',
    polygon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l8 6-3 10H7L4 8z"/></svg>',
    point: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="2 2"/></svg>',
    freehand: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17c3-3 6-10 9-10s3 4 6 4 3-2 3-2"/></svg>',
    circle: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/></svg>',
    ruler: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12h20"/><path d="M6 8v8"/><path d="M10 10v4"/><path d="M14 10v4"/><path d="M18 8v8"/></svg>',
    arrow: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="19" x2="19" y2="5"/><polyline points="9 5 19 5 19 15"/></svg>',
};

/** i18n keys for tool labels */
const TOOL_LABEL_KEYS = {
    select: 'tools.select',
    rectangle: 'tools.rectangle',
    polygon: 'tools.polygon',
    point: 'tools.point',
    freehand: 'tools.freehand',
    circle: 'tools.circle',
    ruler: 'tools.ruler',
    arrow: 'tools.arrow',
};

/**
 * Get translated tool labels
 * @returns {Object<string, string>}
 */
function getToolLabels() {
    const labels = {};
    for (const [tool, key] of Object.entries(TOOL_LABEL_KEYS)) {
        labels[tool] = i18nService.t(key);
    }
    return labels;
}

/**
 * Predefined pathology annotation labels with colors
 */
const PREDEFINED_LABELS = [
    { id: 'tumeur', name: 'Tumeur', color: '#e74c3c' },
    { id: 'benin', name: 'B\u00e9nin', color: '#2ecc71' },
    { id: 'necrose', name: 'N\u00e9crose', color: '#95a5a6' },
    { id: 'inflammation', name: 'Inflammation', color: '#f39c12' },
    { id: 'a_confirmer', name: '\u00c0 confirmer', color: '#3498db' },
    { id: 'stroma', name: 'Stroma', color: '#9b59b6' },
];

class DrawingTools {
    /**
     * @param {Object} viewerInstance - ViewerInstance wrapper
     * @param {AnnotationLayer} annotationLayer - The annotation SVG layer
     */
    constructor(viewerInstance, annotationLayer) {
        this.viewerInstance = viewerInstance;
        this.viewer = viewerInstance.viewer;
        this.annotationLayer = annotationLayer;

        this.activeTool = 'select';
        this.isDrawing = false;

        // Restore last-used overflow tool from localStorage
        const lastTool = this._getLastTool();
        this.primaryTools = ['select', lastTool || 'rectangle'];
        this.overflowOpen = false;

        // Label state
        this.selectedLabel = null;
        this.customLabelMode = false;

        // MPP (microns per pixel) for measurement tools
        this._mpp = null;

        // Drawing state
        this._drawPoints = [];
        this._drawStartSlide = null;
        this._currentPreview = null;

        // Quiz mode state
        this._quizMode = false;

        // Ruler state
        this._rulerStart = null;

        // Overlay visibility toggle state (H key)
        this._overlaysVisible = true;

        // Detection state (for Tab key guard)
        this._hasActiveDetections = false;

        // Arrow state
        this._arrowStart = null;
        this._arrowTextInput = null;

        // DOM
        this.element = null;
        this.overflowMenu = null;
        this.labelSelector = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this._createToolbar();
        this._setupEventListeners();
        this._setupKeyboardShortcuts();
    }

    // ==========================================
    // TOOLBAR UI
    // ==========================================

    _createToolbar() {
        this.element = document.createElement('div');
        this.element.className = 'drawing-tools';
        this.element.setAttribute('role', 'toolbar');
        this.element.setAttribute('aria-label', 'Outils de dessin');
        this._renderToolbar();
    }

    /**
     * Render toolbar content (primary tools + more button + overflow).
     * Uses static TOOL_ICONS constant (no user input) for SVG rendering.
     * @private
     */
    _renderToolbar() {
        // Clear existing content
        while (this.element.firstChild) {
            this.element.removeChild(this.element.firstChild);
        }

        // Primary tool buttons
        for (const tool of this.primaryTools) {
            const btn = document.createElement('button');
            btn.className = `drawing-tools__btn ${tool === this.activeTool ? 'is-active' : ''}`;
            btn.dataset.tool = tool;
            btn.title = getToolLabels()[tool];
            btn.setAttribute('aria-label', getToolLabels()[tool]);
            btn.setAttribute('aria-pressed', String(tool === this.activeTool));
            // TOOL_ICONS is a static constant defined in this module, not user input — safe static SVG
            btn.innerHTML = TOOL_ICONS[tool];
            btn.addEventListener('click', () => this._setTool(tool));
            this.element.appendChild(btn);
        }

        // "More" button (+ overflow)
        const moreBtn = document.createElement('button');
        moreBtn.className = 'drawing-tools__btn drawing-tools__btn--more';
        moreBtn.title = i18nService.t('btn.moreTools');
        moreBtn.setAttribute('aria-label', i18nService.t('btn.moreTools'));
        moreBtn.setAttribute('aria-expanded', String(this.overflowOpen));
        moreBtn.textContent = '+';
        moreBtn.addEventListener('click', () => this._toggleOverflow());
        this.element.appendChild(moreBtn);

        // Overflow container with remaining tools
        const overflowTools = TOOLS.filter(t => !this.primaryTools.includes(t));
        this.overflowMenu = document.createElement('div');
        this.overflowMenu.className = 'drawing-tools__overflow';
        this.overflowMenu.style.display = 'none';

        for (const tool of overflowTools) {
            const btn = document.createElement('button');
            btn.className = `drawing-tools__btn ${tool === this.activeTool ? 'is-active' : ''}`;
            btn.dataset.tool = tool;
            btn.title = getToolLabels()[tool];
            btn.setAttribute('aria-label', getToolLabels()[tool]);
            btn.setAttribute('aria-pressed', String(tool === this.activeTool));
            // TOOL_ICONS is a static constant defined in this module, not user input — safe static SVG
            btn.innerHTML = TOOL_ICONS[tool];
            btn.addEventListener('click', () => this._setTool(tool));
            this.overflowMenu.appendChild(btn);
        }

        this.element.appendChild(this.overflowMenu);

        // Delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'drawing-tools__btn drawing-tools__btn--danger';
        deleteBtn.title = i18nService.t('tools.deleteSelection');
        deleteBtn.setAttribute('aria-label', i18nService.t('tools.deleteSelection'));
        // Static SVG icon, not user input — safe constant, no user data
        deleteBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M5 6v14a2 2 0 002 2h10a2 2 0 002-2V6"/></svg>';
        deleteBtn.addEventListener('click', () => this._deleteSelected());
        this.element.appendChild(deleteBtn);

        // Label selector (visible when a drawing tool is active)
        this.labelSelector = this._buildLabelSelector();
        this.element.appendChild(this.labelSelector);
        this._updateLabelSelectorVisibility();
    }

    /**
     * Build the label selector dropdown with predefined pathology labels
     * @returns {HTMLElement}
     * @private
     */
    _buildLabelSelector() {
        const container = document.createElement('div');
        container.className = 'drawing-tools__label-selector';

        // Predefined label buttons
        const btnGroup = document.createElement('div');
        btnGroup.className = 'drawing-tools__label-group';

        // "No label" button
        const noneBtn = document.createElement('button');
        noneBtn.className = 'drawing-tools__label-btn is-active';
        noneBtn.dataset.labelId = '';
        noneBtn.title = i18nService.t('tools.noLabel');
        noneBtn.textContent = '\u2013';
        noneBtn.style.borderColor = '#666';
        noneBtn.addEventListener('click', () => this._selectLabel(null));
        btnGroup.appendChild(noneBtn);

        for (const label of PREDEFINED_LABELS) {
            const btn = document.createElement('button');
            btn.className = 'drawing-tools__label-btn';
            btn.dataset.labelId = label.id;
            btn.title = label.name;
            btn.textContent = label.name.charAt(0);
            btn.style.borderColor = label.color;
            btn.style.color = label.color;
            btn.addEventListener('click', () => this._selectLabel(label));
            btnGroup.appendChild(btn);
        }

        container.appendChild(btnGroup);

        // Custom label text input
        const customRow = document.createElement('div');
        customRow.className = 'drawing-tools__custom-label';

        const customInput = document.createElement('input');
        customInput.className = 'drawing-tools__custom-input';
        customInput.type = 'text';
        customInput.placeholder = i18nService.t('tools.customLabel');
        customInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && customInput.value.trim()) {
                const customLabel = {
                    id: 'custom_' + customInput.value.trim().toLowerCase().replace(/\s+/g, '_'),
                    name: customInput.value.trim(),
                    color: '#4a9eff',
                };
                this._selectLabel(customLabel);
                // Highlight none of the predefined buttons
                container.querySelectorAll('.drawing-tools__label-btn').forEach(b =>
                    b.classList.remove('is-active'),
                );
            }
        });
        customRow.appendChild(customInput);
        container.appendChild(customRow);

        return container;
    }

    /**
     * Select a label for new annotations
     * @param {Object|null} label - Label object {id, name, color} or null
     * @private
     */
    _selectLabel(label) {
        this.selectedLabel = label;
        annotationStore.activeLabel = label ? label.id : null;

        // Update button states
        if (this.labelSelector) {
            this.labelSelector.querySelectorAll('.drawing-tools__label-btn').forEach(btn => {
                const btnLabelId = btn.dataset.labelId;
                const isActive = label ? (btnLabelId === label.id) : (btnLabelId === '');
                btn.classList.toggle('is-active', isActive);
            });
            // Clear custom input when selecting predefined
            const customInput = this.labelSelector.querySelector('.drawing-tools__custom-input');
            if (customInput && label && !label.id.startsWith('custom_')) {
                customInput.value = '';
            }
        }
    }

    /**
     * Show/hide label selector based on active tool
     * @private
     */
    _updateLabelSelectorVisibility() {
        if (!this.labelSelector) {return;}
        const isDrawTool = this.activeTool !== 'select' && this.activeTool !== 'ruler' && this.activeTool !== 'arrow';
        this.labelSelector.style.display = isDrawTool ? 'flex' : 'none';
    }

    _setTool(toolName) {
        this.activeTool = toolName;
        annotationStore.setTool(toolName);

        // If a tool from overflow is selected, promote it to primary slot
        if (toolName !== 'select' && !this.primaryTools.includes(toolName)) {
            this.primaryTools[1] = toolName;
            this._saveLastTool(toolName);
            this._rebuild();
        } else {
            // Update toolbar UI
            this.element.querySelectorAll('.drawing-tools__btn').forEach(btn => {
                const isActive = btn.dataset.tool === toolName;
                btn.classList.toggle('is-active', isActive);
                if (btn.dataset.tool) {
                    btn.setAttribute('aria-pressed', String(isActive));
                }
            });
        }

        // Close overflow menu after selection
        this.overflowOpen = false;
        if (this.overflowMenu) {
            this.overflowMenu.style.display = 'none';
        }

        // Toggle OSD mouse navigation
        const isDrawTool = toolName !== 'select';
        this.viewer.setMouseNavEnabled(!isDrawTool);

        // Show/hide label selector
        this._updateLabelSelectorVisibility();

        // Cancel current drawing
        this._cancelDrawing();
    }

    /**
     * Toggle overflow menu visibility
     * @private
     */
    _toggleOverflow() {
        this.overflowOpen = !this.overflowOpen;
        if (this.overflowMenu) {
            this.overflowMenu.style.display = this.overflowOpen ? 'flex' : 'none';
        }
        const moreBtn = this.element.querySelector('.drawing-tools__btn--more');
        if (moreBtn) {
            moreBtn.setAttribute('aria-expanded', String(this.overflowOpen));
        }
    }

    /**
     * Rebuild the toolbar (after primary tool change)
     * @private
     */
    _rebuild() {
        this._renderToolbar();
    }

    // ==========================================
    // EVENT HANDLERS
    // ==========================================

    _setupEventListeners() {
        const canvas = this.viewer.canvas;

        canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
        canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
        canvas.addEventListener('mouseup', (e) => this._onMouseUp(e));
        canvas.addEventListener('dblclick', (e) => this._onDblClick(e));

        // External tool change - Store unsubscribe function
        this._unsubscribers.push(
            eventBus.on(Events.TOOL_CHANGED, ({ tool }) => {
                if (tool !== this.activeTool) {this._setTool(tool);}
            }),
        );

        // Track active detections for Tab key guard
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_COMPLETE, () => { this._hasActiveDetections = true; }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_PREVIEW, ({ features }) => {
                this._hasActiveDetections = features && features.length > 0;
            }),
        );
    }

    _setupKeyboardShortcuts() {
        this._boundKeyHandler = (e) => this._handleKeyDown(e);
        document.addEventListener('keydown', this._boundKeyHandler);
    }

    _handleKeyDown(e) {
        if (!this.element || !this.element.parentNode) return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        switch (e.key) {
            case 's': case 'S': this._setTool('select'); break;
            case 'd': case 'D': this._setTool('freehand'); break;
            case 'r': case 'R': this._setTool('rectangle'); break;
            case 'p': case 'P': this._setTool('polygon'); break;
            case 'm': case 'M': this._setTool('point'); break;
            case 'f': case 'F':
                if (e.ctrlKey || e.metaKey) break;
                this._setTool('arrow');
                break;
            case 'c': case 'C':
                if (e.ctrlKey || e.metaKey) break;
                this._setTool('circle');
                break;
            case 'l': case 'L': this._setTool('ruler'); break;
            case 'Delete': case 'Backspace': this._deleteSelected(); break;
            case 'Escape':
                this._cancelDrawing();
                this._setTool('select');
                break;
            case 'z': case 'Z':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    annotationStore.undo();
                }
                break;
            case 'y': case 'Y':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    annotationStore.redo();
                }
                break;
            case 'v': case 'V':
                if (e.ctrlKey || e.metaKey) break;
                eventBus.emit(Events.DETECTION_VALIDATE_CURRENT);
                break;
            case 'x': case 'X':
                if (e.ctrlKey || e.metaKey) break;
                eventBus.emit(Events.DETECTION_REJECT_CURRENT);
                break;
            case 'Tab':
                if (this._hasActiveDetections) {
                    e.preventDefault();
                    eventBus.emit(Events.DETECTION_NEXT);
                }
                break;
            case 'q': case 'Q':
                if (e.ctrlKey || e.metaKey) break;
                this._quizMode = !this._quizMode;
                eventBus.emit(Events.QUIZ_MODE_TOGGLE, { enabled: this._quizMode });
                if (!this._quizMode && this.annotationLayer?.getQuizSummary) {
                    const s = this.annotationLayer.getQuizSummary();
                    const missedStr = s.missed.length > 0
                        ? `\nNon r\u00e9v\u00e9l\u00e9es : ${s.missed.slice(0, 5).join(', ')}${s.missed.length > 5 ? '...' : ''}`
                        : '';
                    eventBus.emit(Events.TOAST_SHOW, {
                        type: s.pct >= 80 ? 'success' : 'info',
                        message: `Quiz termin\u00e9 : ${s.revealed}/${s.total} (${s.pct}%)${missedStr}`,
                        duration: 5000,
                    });
                } else {
                    eventBus.emit(Events.TOAST_SHOW, {
                        type: 'info',
                        message: 'Quiz mode ON',
                        duration: 2000,
                    });
                }
                break;
            case 'h': case 'H':
                this._overlaysVisible = !this._overlaysVisible;
                eventBus.emit(Events.ML_OVERLAYS_TOGGLE, { visible: this._overlaysVisible });
                break;
            case '1': eventBus.emit(Events.VIEWER_ZOOM_PRESET, { level: 1 }); break;
            case '2': eventBus.emit(Events.VIEWER_ZOOM_PRESET, { level: 2 }); break;
            case '3': eventBus.emit(Events.VIEWER_ZOOM_PRESET, { level: 3 }); break;
            case '4': eventBus.emit(Events.VIEWER_ZOOM_PRESET, { level: 4 }); break;
            case '5': eventBus.emit(Events.VIEWER_ZOOM_PRESET, { level: 5 }); break;
        }
    }

    _getSlideCoords(e) {
        const rect = this.viewer.canvas.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        return this.annotationLayer.screenToSlide(screenX, screenY);
    }

    // ==========================================
    // DRAWING HANDLERS
    // ==========================================

    _onMouseDown(e) {
        if (this.activeTool === 'select' || e.button !== 0) {return;}

        const slideCoords = this._getSlideCoords(e);

        switch (this.activeTool) {
            case 'rectangle':
            case 'circle':
                this.isDrawing = true;
                this._drawStartSlide = slideCoords;
                eventBus.emit(Events.DRAWING_START, { tool: this.activeTool });
                break;
            case 'point':
                this._createPointAnnotation(slideCoords);
                break;
            case 'freehand':
                this.isDrawing = true;
                this._drawPoints = [slideCoords];
                eventBus.emit(Events.DRAWING_START, { tool: 'freehand' });
                break;
            case 'polygon':
                if (!this.isDrawing) {
                    this.isDrawing = true;
                    this._drawPoints = [slideCoords];
                    eventBus.emit(Events.DRAWING_START, { tool: 'polygon' });
                } else {
                    this._drawPoints.push(slideCoords);
                }
                this._updatePolygonPreview();
                break;
            case 'ruler':
                if (!this.isDrawing) {
                    this.isDrawing = true;
                    this._rulerStart = slideCoords;
                    eventBus.emit(Events.DRAWING_START, { tool: 'ruler' });
                } else {
                    this._finishRuler(slideCoords);
                }
                break;
            case 'arrow':
                if (!this.isDrawing) {
                    this.isDrawing = true;
                    this._arrowStart = slideCoords;
                    eventBus.emit(Events.DRAWING_START, { tool: 'arrow' });
                } else {
                    this._finishArrow(slideCoords);
                }
                break;
        }
    }

    _onMouseMove(e) {
        if (!this.isDrawing) {return;}

        const slideCoords = this._getSlideCoords(e);

        switch (this.activeTool) {
            case 'rectangle':
                this._updateRectanglePreview(slideCoords);
                break;
            case 'circle':
                this._updateCirclePreview(slideCoords);
                break;
            case 'freehand':
                this._drawPoints.push(slideCoords);
                this._updateFreehandPreview();
                break;
            case 'ruler':
                this._updateRulerPreview(slideCoords);
                break;
            case 'arrow':
                this._updateArrowPreview(slideCoords);
                break;
        }
    }

    _onMouseUp(e) {
        if (!this.isDrawing) {return;}

        const slideCoords = this._getSlideCoords(e);

        switch (this.activeTool) {
            case 'rectangle':
                this._finishRectangle(slideCoords);
                break;
            case 'circle':
                this._finishCircle(slideCoords);
                break;
            case 'freehand':
                this._finishFreehand();
                break;
            // polygon finishes on dblclick
        }
    }

    _onDblClick(e) {
        if (this.activeTool === 'polygon' && this.isDrawing) {
            e.preventDefault();
            e.stopPropagation();
            this._finishPolygon();
        }
    }

    // ==========================================
    // DRAWING: RECTANGLE
    // ==========================================

    _updateRectanglePreview(current) {
        this._clearPreview();
        const start = this._drawStartSlide;
        if (!start) {return;}

        const x = Math.min(start.x, current.x);
        const y = Math.min(start.y, current.y);
        const w = Math.abs(current.x - start.x);
        const h = Math.abs(current.y - start.y);

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', w);
        rect.setAttribute('height', h);
        rect.setAttribute('fill', 'rgba(74, 158, 255, 0.2)');
        rect.setAttribute('stroke', '#4a9eff');
        rect.setAttribute('stroke-width', this.annotationLayer._getStrokeWidth());
        rect.setAttribute('stroke-dasharray', '5 3');

        this._currentPreview = rect;
        this.annotationLayer.getPreviewGroup().appendChild(rect);
    }

    async _finishRectangle(end) {
        this.isDrawing = false;
        this._clearPreview();

        const start = this._drawStartSlide;
        if (!start) {return;}

        const x1 = Math.min(start.x, end.x);
        const y1 = Math.min(start.y, end.y);
        const x2 = Math.max(start.x, end.x);
        const y2 = Math.max(start.y, end.y);

        // Ignore tiny rectangles
        if (Math.abs(x2 - x1) < 5 || Math.abs(y2 - y1) < 5) {return;}

        const coordinates = [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]];

        await annotationStore.createAnnotation({
            geometry: { type: 'Polygon', coordinates },
            geometry_type: 'rectangle',
            annotation_type: 'manual',
            label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
        });

        eventBus.emit(Events.DRAWING_END, { tool: 'rectangle' });
    }

    // ==========================================
    // DRAWING: POLYGON
    // ==========================================

    _updatePolygonPreview() {
        this._clearPreview();
        if (this._drawPoints.length < 1) {return;}

        const points = this._drawPoints.map(p => `${p.x},${p.y}`).join(' ');
        const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline.setAttribute('points', points);
        polyline.setAttribute('fill', 'rgba(74, 158, 255, 0.1)');
        polyline.setAttribute('stroke', '#4a9eff');
        polyline.setAttribute('stroke-width', this.annotationLayer._getStrokeWidth());
        polyline.setAttribute('stroke-dasharray', '5 3');

        this._currentPreview = polyline;
        this.annotationLayer.getPreviewGroup().appendChild(polyline);

        // Draw vertices
        for (const p of this._drawPoints) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', p.x);
            circle.setAttribute('cy', p.y);
            circle.setAttribute('r', this.annotationLayer._getPointRadius() * 0.5);
            circle.setAttribute('fill', '#4a9eff');
            this.annotationLayer.getPreviewGroup().appendChild(circle);
        }
    }

    async _finishPolygon() {
        this.isDrawing = false;
        this._clearPreview();

        if (this._drawPoints.length < 3) {
            this._drawPoints = [];
            return;
        }

        // Close the polygon
        const coords = this._drawPoints.map(p => [p.x, p.y]);
        coords.push(coords[0]); // close ring

        await annotationStore.createAnnotation({
            geometry: { type: 'Polygon', coordinates: [coords] },
            geometry_type: 'polygon',
            annotation_type: 'manual',
            label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
        });

        this._drawPoints = [];
        eventBus.emit(Events.DRAWING_END, { tool: 'polygon' });
    }

    // ==========================================
    // DRAWING: POINT
    // ==========================================

    async _createPointAnnotation(coords) {
        await annotationStore.createAnnotation({
            geometry: { type: 'Point', coordinates: [coords.x, coords.y] },
            geometry_type: 'point',
            annotation_type: 'manual',
            label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
        });
        eventBus.emit(Events.DRAWING_END, { tool: 'point' });
    }

    // ==========================================
    // DRAWING: FREEHAND
    // ==========================================

    _updateFreehandPreview() {
        this._clearPreview();
        if (this._drawPoints.length < 2) {return;}

        const points = this._drawPoints.map(p => `${p.x},${p.y}`).join(' ');
        const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline.setAttribute('points', points);
        polyline.setAttribute('fill', 'none');
        polyline.setAttribute('stroke', '#4a9eff');
        polyline.setAttribute('stroke-width', this.annotationLayer._getStrokeWidth());

        this._currentPreview = polyline;
        this.annotationLayer.getPreviewGroup().appendChild(polyline);
    }

    async _finishFreehand() {
        this.isDrawing = false;
        this._clearPreview();

        if (this._drawPoints.length < 5) {
            this._drawPoints = [];
            return;
        }

        // Simplify with Douglas-Peucker
        const simplified = this._simplifyPath(this._drawPoints, 3);

        const coords = simplified.map(p => [p.x, p.y]);
        coords.push(coords[0]); // close

        await annotationStore.createAnnotation({
            geometry: { type: 'Polygon', coordinates: [coords] },
            geometry_type: 'freehand',
            annotation_type: 'manual',
            label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
        });

        this._drawPoints = [];
        eventBus.emit(Events.DRAWING_END, { tool: 'freehand' });
    }

    // ==========================================
    // DRAWING: CIRCLE
    // ==========================================

    _updateCirclePreview(current) {
        this._clearPreview();
        const start = this._drawStartSlide;
        if (!start) {return;}

        const dx = current.x - start.x;
        const dy = current.y - start.y;
        const radius = Math.sqrt(dx * dx + dy * dy);

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', start.x);
        circle.setAttribute('cy', start.y);
        circle.setAttribute('r', radius);
        circle.setAttribute('fill', 'rgba(74, 158, 255, 0.2)');
        circle.setAttribute('stroke', '#4a9eff');
        circle.setAttribute('stroke-width', this.annotationLayer._getStrokeWidth());
        circle.setAttribute('stroke-dasharray', '5 3');

        this._currentPreview = circle;
        this.annotationLayer.getPreviewGroup().appendChild(circle);
    }

    async _finishCircle(end) {
        this.isDrawing = false;
        this._clearPreview();

        const start = this._drawStartSlide;
        if (!start) {return;}

        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const radius = Math.sqrt(dx * dx + dy * dy);

        if (radius < 5) {return;}

        // Approximate circle as polygon (32 segments)
        const segments = 32;
        const coords = [];
        for (let i = 0; i <= segments; i++) {
            const angle = (2 * Math.PI * i) / segments;
            coords.push([
                start.x + radius * Math.cos(angle),
                start.y + radius * Math.sin(angle),
            ]);
        }

        await annotationStore.createAnnotation({
            geometry: { type: 'Polygon', coordinates: [coords] },
            geometry_type: 'circle',
            annotation_type: 'manual',
            label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
            properties: { center: [start.x, start.y], radius },
        });

        eventBus.emit(Events.DRAWING_END, { tool: 'circle' });
    }

    // ==========================================
    // DRAWING: RULER (measurement tool)
    // ==========================================

    _updateRulerPreview(current) {
        this._clearPreview();
        const start = this._rulerStart;
        if (!start) {return;}

        const group = this.annotationLayer.getPreviewGroup();
        const strokeWidth = this.annotationLayer._getStrokeWidth();

        // Line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', start.x);
        line.setAttribute('y1', start.y);
        line.setAttribute('x2', current.x);
        line.setAttribute('y2', current.y);
        line.setAttribute('stroke', '#ffcc00');
        line.setAttribute('stroke-width', strokeWidth);
        line.setAttribute('stroke-dasharray', `${strokeWidth * 3} ${strokeWidth * 2}`);
        group.appendChild(line);

        // Endpoint circles
        const endR = this.annotationLayer._getPointRadius() * 0.4;
        for (const pt of [start, current]) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', pt.x);
            circle.setAttribute('cy', pt.y);
            circle.setAttribute('r', endR);
            circle.setAttribute('fill', '#ffcc00');
            group.appendChild(circle);
        }

        // Distance label at midpoint
        const midX = (start.x + current.x) / 2;
        const midY = (start.y + current.y) / 2;
        const distLabel = this._formatDistance(start, current);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', midY - strokeWidth * 3);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#ffcc00');
        text.setAttribute('font-size', strokeWidth * 8);
        text.setAttribute('font-family', 'JetBrains Mono, monospace');
        text.setAttribute('font-weight', '600');
        text.setAttribute('stroke', '#000');
        text.setAttribute('stroke-width', strokeWidth * 0.8);
        text.setAttribute('paint-order', 'stroke');
        text.textContent = distLabel;
        group.appendChild(text);

        this._currentPreview = group;
    }

    _finishRuler(end) {
        // Rulers are ephemeral measurements drawn on the SVG preview group.
        // They persist visually until the next drawing action clears the preview,
        // but are NOT saved as annotations. This is intentional — rulers are a
        // quick-measure tool, not persistent geometry.
        this.isDrawing = false;
        this._clearPreview();

        const start = this._rulerStart;
        if (!start) {return;}

        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const distPx = Math.sqrt(dx * dx + dy * dy);

        // Ignore tiny measurements
        if (distPx < 5) {
            this._rulerStart = null;
            return;
        }

        // Draw the permanent ruler on the preview group
        const group = this.annotationLayer.getPreviewGroup();
        const strokeWidth = this.annotationLayer._getStrokeWidth();

        // Permanent line
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', start.x);
        line.setAttribute('y1', start.y);
        line.setAttribute('x2', end.x);
        line.setAttribute('y2', end.y);
        line.setAttribute('stroke', '#ffcc00');
        line.setAttribute('stroke-width', strokeWidth);
        line.classList.add('ruler-line');
        group.appendChild(line);

        // Endpoint circles
        const endR = this.annotationLayer._getPointRadius() * 0.4;
        for (const pt of [start, end]) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', pt.x);
            circle.setAttribute('cy', pt.y);
            circle.setAttribute('r', endR);
            circle.setAttribute('fill', '#ffcc00');
            circle.classList.add('ruler-line');
            group.appendChild(circle);
        }

        // Distance label
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;
        const distLabel = this._formatDistance(start, end);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', midX);
        text.setAttribute('y', midY - strokeWidth * 3);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#ffcc00');
        text.setAttribute('font-size', strokeWidth * 8);
        text.setAttribute('font-family', 'JetBrains Mono, monospace');
        text.setAttribute('font-weight', '600');
        text.setAttribute('stroke', '#000');
        text.setAttribute('stroke-width', strokeWidth * 0.8);
        text.setAttribute('paint-order', 'stroke');
        text.classList.add('ruler-line');
        text.textContent = distLabel;
        group.appendChild(text);

        this._rulerStart = null;
        eventBus.emit(Events.DRAWING_END, { tool: 'ruler' });
    }

    // ==========================================
    // DRAWING: ARROW (annotation with text label)
    // ==========================================

    _updateArrowPreview(current) {
        this._clearPreview();
        const start = this._arrowStart;
        if (!start) {return;}

        const color = (this.selectedLabel && this.selectedLabel.color) ? this.selectedLabel.color : '#ff4444';
        const strokeWidth = this.annotationLayer._getStrokeWidth();
        const group = this.annotationLayer.getPreviewGroup();

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', start.x);
        line.setAttribute('y1', start.y);
        line.setAttribute('x2', current.x);
        line.setAttribute('y2', current.y);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', strokeWidth);
        line.setAttribute('stroke-dasharray', `${strokeWidth * 3} ${strokeWidth * 2}`);
        group.appendChild(line);

        this._currentPreview = line;
    }

    _finishArrow(end) {
        this.isDrawing = false;
        this._clearPreview();

        const start = this._arrowStart;
        if (!start) {return;}

        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const distPx = Math.sqrt(dx * dx + dy * dy);

        // Ignore tiny arrows
        if (distPx < 5) {
            this._arrowStart = null;
            return;
        }

        // Show inline text input appended to the toolbar element
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'drawing-tools__arrow-text';
        input.placeholder = 'Label...';
        this._arrowTextInput = input;
        this.element.appendChild(input);
        input.focus();

        const commit = async () => {
            const text = input.value.trim();
            input.remove();
            this._arrowTextInput = null;

            await annotationStore.createAnnotation({
                geometry: {
                    type: 'LineString',
                    coordinates: [[start.x, start.y], [end.x, end.y]],
                },
                geometry_type: 'arrow',
                annotation_type: 'manual',
                label_id: this.selectedLabel ? this.selectedLabel.id : undefined,
                properties: { text },
            });

            this._arrowStart = null;
            eventBus.emit(Events.DRAWING_END, { tool: 'arrow' });
        };

        const cancel = () => {
            input.remove();
            this._arrowTextInput = null;
            this._arrowStart = null;
        };

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                commit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancel();
            }
            // Prevent keyboard shortcuts from firing while typing
            e.stopPropagation();
        });

        // Commit on blur (user clicks away)
        input.addEventListener('blur', () => {
            // Only commit if still attached (not already handled by keydown)
            if (this._arrowTextInput === input) {
                commit();
            }
        });
    }

    /**
     * Format the distance between two points in physical units
     * @param {{ x: number, y: number }} a - Start point (slide pixels)
     * @param {{ x: number, y: number }} b - End point (slide pixels)
     * @returns {string} Formatted distance string
     * @private
     */
    _formatDistance(a, b) {
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distPx = Math.sqrt(dx * dx + dy * dy);

        if (this._mpp && this._mpp > 0) {
            const distUm = distPx * this._mpp;
            if (distUm >= 1000) {
                return (distUm / 1000).toFixed(2) + ' mm';
            }
            return distUm.toFixed(1) + ' \u00b5m';
        }

        return Math.round(distPx) + ' px';
    }

    /**
     * Set microns-per-pixel value for measurement calculations
     * @param {number|null} mpp
     */
    setMpp(mpp) {
        this._mpp = mpp;
    }

    // ==========================================
    // UTILITIES
    // ==========================================

    /**
     * Get the last-used tool from localStorage
     * @returns {string|null}
     * @private
     */
    _getLastTool() {
        try {
            const tool = localStorage.getItem(LAST_TOOL_KEY);
            if (tool && TOOLS.includes(tool) && tool !== 'select') {
                return tool;
            }
        } catch (_e) {
            // localStorage may be unavailable
        }
        return null;
    }

    /**
     * Save the last-used tool to localStorage
     * @param {string} toolName
     * @private
     */
    _saveLastTool(toolName) {
        try {
            localStorage.setItem(LAST_TOOL_KEY, toolName);
        } catch (_e) {
            // localStorage may be unavailable
        }
    }

    _clearPreview() {
        const group = this.annotationLayer.getPreviewGroup();
        while (group.firstChild) {
            group.removeChild(group.firstChild);
        }
        this._currentPreview = null;
    }

    _cancelDrawing() {
        this.isDrawing = false;
        this._drawPoints = [];
        this._drawStartSlide = null;
        this._rulerStart = null;
        this._arrowStart = null;
        if (this._arrowTextInput) {
            this._arrowTextInput.remove();
            this._arrowTextInput = null;
        }
        this._clearPreview();
    }

    async _deleteSelected() {
        const selected = annotationStore.selectedId;
        if (selected) {
            await annotationStore.deleteAnnotation(selected);
        }
    }

    /**
     * Douglas-Peucker simplification
     */
    _simplifyPath(points, tolerance) {
        if (points.length <= 2) {return points;}

        let maxDist = 0;
        let maxIdx = 0;
        const start = points[0];
        const end = points[points.length - 1];

        for (let i = 1; i < points.length - 1; i++) {
            const dist = this._perpendicularDist(points[i], start, end);
            if (dist > maxDist) {
                maxDist = dist;
                maxIdx = i;
            }
        }

        if (maxDist > tolerance) {
            const left = this._simplifyPath(points.slice(0, maxIdx + 1), tolerance);
            const right = this._simplifyPath(points.slice(maxIdx), tolerance);
            return left.slice(0, -1).concat(right);
        }

        return [start, end];
    }

    _perpendicularDist(point, lineStart, lineEnd) {
        const dx = lineEnd.x - lineStart.x;
        const dy = lineEnd.y - lineStart.y;
        const lenSq = dx * dx + dy * dy;

        if (lenSq === 0) {
            const ddx = point.x - lineStart.x;
            const ddy = point.y - lineStart.y;
            return Math.sqrt(ddx * ddx + ddy * ddy);
        }

        const num = Math.abs(
            dy * point.x - dx * point.y + lineEnd.x * lineStart.y - lineEnd.y * lineStart.x,
        );
        return num / Math.sqrt(lenSq);
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    destroy() {
        this._cancelDrawing();

        // Properly unsubscribe from all event listeners
        this._unsubscribers.forEach(unsubscribe => unsubscribe());
        this._unsubscribers = [];

        if (this._boundKeyHandler) {
            document.removeEventListener('keydown', this._boundKeyHandler);
            this._boundKeyHandler = null;
        }

        // Re-enable OSD navigation
        if (this.viewer) {
            this.viewer.setMouseNavEnabled(true);
        }

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { DrawingTools };
export default DrawingTools;
