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
 *
 * Coordinates: screen px → OSD viewport → slide pixels
 *
 * @module components/DrawingTools
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';

const TOOLS = ['select', 'rectangle', 'polygon', 'point', 'freehand', 'circle'];

const TOOL_ICONS = {
    select: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>',
    rectangle: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>',
    polygon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l8 6-3 10H7L4 8z"/></svg>',
    point: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="2 2"/></svg>',
    freehand: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17c3-3 6-10 9-10s3 4 6 4 3-2 3-2"/></svg>',
    circle: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/></svg>',
};

const TOOL_LABELS = {
    select: 'Select (V)',
    rectangle: 'Rectangle (R)',
    polygon: 'Polygon (P)',
    point: 'Point (M)',
    freehand: 'Freehand (F)',
    circle: 'Circle (C)',
};

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

        // Drawing state
        this._drawPoints = [];
        this._drawStartSlide = null;
        this._currentPreview = null;

        // DOM
        this.element = null;

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

        for (const tool of TOOLS) {
            const btn = document.createElement('button');
            btn.className = `drawing-tools__btn ${tool === this.activeTool ? 'is-active' : ''}`;
            btn.dataset.tool = tool;
            btn.title = TOOL_LABELS[tool];
            btn.innerHTML = TOOL_ICONS[tool];

            btn.addEventListener('click', () => this._setTool(tool));
            this.element.appendChild(btn);
        }

        // Delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'drawing-tools__btn drawing-tools__btn--danger';
        deleteBtn.title = 'Delete Selected (Del)';
        deleteBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M5 6v14a2 2 0 002 2h10a2 2 0 002-2V6"/></svg>';
        deleteBtn.addEventListener('click', () => this._deleteSelected());
        this.element.appendChild(deleteBtn);
    }

    _setTool(toolName) {
        this.activeTool = toolName;
        annotationStore.setTool(toolName);

        // Update toolbar UI
        this.element.querySelectorAll('.drawing-tools__btn').forEach(btn => {
            btn.classList.toggle('is-active', btn.dataset.tool === toolName);
        });

        // Toggle OSD mouse navigation
        const isDrawTool = toolName !== 'select';
        this.viewer.setMouseNavEnabled(!isDrawTool);

        // Cancel current drawing
        this._cancelDrawing();
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
    }

    _setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle if viewer page is active
            if (!this.element || !this.element.parentNode) {return;}

            switch (e.key) {
                case 'v': case 'V': this._setTool('select'); break;
                case 'r': case 'R': this._setTool('rectangle'); break;
                case 'p': case 'P': this._setTool('polygon'); break;
                case 'm': case 'M': this._setTool('point'); break;
                case 'f': case 'F': this._setTool('freehand'); break;
                case 'c': case 'C': this._setTool('circle'); break;
                case 'Delete': this._deleteSelected(); break;
                case 'Escape': this._cancelDrawing(); break;
            }
        });
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
            properties: { center: [start.x, start.y], radius },
        });

        eventBus.emit(Events.DRAWING_END, { tool: 'circle' });
    }

    // ==========================================
    // UTILITIES
    // ==========================================

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
