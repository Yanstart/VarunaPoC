/**
 * AnnotationLayer - SVG overlay for rendering annotations on OpenSeadragon
 *
 * Renders spatial annotations as SVG elements overlaid on the slide viewer.
 * Supports polygons, rectangles, points, circles, and freehand drawings.
 * Recalculates viewBox on each viewport change for correct positioning.
 *
 * @module components/AnnotationLayer
 */

import OpenSeadragon from 'openseadragon';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';

class AnnotationLayer {
    /**
     * @param {Object} viewerInstance - ViewerInstance wrapper
     * @param {Object} [options]
     * @param {number} [options.defaultOpacity=0.4] - Default fill opacity
     */
    constructor(viewerInstance, options = {}) {
        this.viewerInstance = viewerInstance;
        this.viewer = viewerInstance.viewer;
        this.viewerId = viewerInstance.id;

        this.defaultOpacity = options.defaultOpacity || 0.4;

        /** @type {SVGSVGElement|null} */
        this.svg = null;

        /** @type {Object|null} Slide dimensions {width, height} */
        this.slideDimensions = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this._quizMode = false;
        this._revealedAnnotations = new Set();

        this._boundUpdate = this._updateViewBox.bind(this);
        this._create();
        this._setupEventListeners();
    }

    // ==========================================
    // SETUP
    // ==========================================

    _create() {
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.classList.add('annotation-layer');
        this.svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        this.svg.setAttribute('aria-hidden', 'true');
        this.svg.style.cssText = `
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 200;
        `;

        // Defs for patterns (dashed preview)
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        this.svg.appendChild(defs);

        // Annotation group
        this.annoGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.annoGroup.classList.add('annotations');
        this.svg.appendChild(this.annoGroup);

        // Preview group (detection previews, drawing in-progress)
        this.previewGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.previewGroup.classList.add('previews');
        this.svg.appendChild(this.previewGroup);

        // Disagreement overlay group (quality metrics)
        this.disagreementGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.disagreementGroup.classList.add('disagreements');
        this.svg.appendChild(this.disagreementGroup);

        // Insert into OSD container
        const container = this.viewer.container;
        container.appendChild(this.svg);
    }

    _setupEventListeners() {
        // Viewport changes
        this.viewer.addHandler('viewport-change', this._boundUpdate);
        this.viewer.addHandler('resize', this._boundUpdate);
        this.viewer.addHandler('open', () => {
            this._extractSlideDimensions();
            this._updateViewBox();
            this.render();
        });

        // Annotation store events - Store unsubscribe functions
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATIONS_LOADED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_CREATED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_UPDATED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_DELETED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_SELECTED, ({ annotationId }) => {
                this._highlightSelected(annotationId);
            }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.LAYER_VISIBILITY_CHANGED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.LAYER_OPACITY_CHANGED, () => this.render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_PREVIEW, ({ features }) => {
                this._renderPreviews(features);
            }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_ITEM_CLICKED, ({ index }) => {
                this._highlightDetectionPreview(index);
            }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_HIGHLIGHT, ({ regionIndex, visible }) => {
                if (visible !== undefined && regionIndex !== null && regionIndex !== undefined) {
                    const target = this.previewGroup?.querySelector(`[data-detection-index="${regionIndex}"]`);
                    if (target) {
                        target.style.display = visible ? '' : 'none';
                    }
                }
            }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.QUALITY_DISAGREEMENT_TOGGLE, ({ visible, features }) => {
                this._renderDisagreements(visible ? features : []);
            }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ML_OVERLAYS_TOGGLE, ({ visible }) => {
                const previews = this.svg?.querySelectorAll('.detection-preview');
                if (previews) {
                    previews.forEach(el => { el.style.display = visible ? '' : 'none'; });
                }
            }),
        );

        // Skip hit-testing while drawing annotations
        this._isDrawing = false;
        this._unsubscribers.push(
            eventBus.on(Events.DRAWING_START, () => { this._isDrawing = true; }),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DRAWING_END, () => { this._isDrawing = false; }),
        );

        // Centralized click handler via OSD — replaces per-element pointer-events.
        // SVG elements stay pointer-events:none so OSD receives all mouse events
        // (pan/zoom works). On click, we convert coords and hit-test SVG shapes.
        this._boundCanvasClick = (event) => {
            if (this._isDrawing) { return; }

            const tiledImage = this.viewer.world.getItemAt(0);
            if (!tiledImage) {return;}

            // Convert click position to image pixel coordinates
            const viewportPoint = this.viewer.viewport.pointFromPixel(event.position);
            const imagePoint = tiledImage.viewportToImageCoordinates(viewportPoint);

            // Create SVG point for hit-testing
            const svgPoint = this.svg.createSVGPoint();
            svgPoint.x = imagePoint.x;
            svgPoint.y = imagePoint.y;

            // 1) Test detection previews first (higher priority, on top)
            const previews = this.previewGroup.querySelectorAll('.detection-preview');
            for (const polygon of previews) {
                if (polygon.style.display === 'none') {continue;}
                try {
                    if (polygon.isPointInFill(svgPoint) || polygon.isPointInStroke(svgPoint)) {
                        const index = parseInt(polygon.dataset.detectionIndex);
                        this._highlightDetectionPreview(index);
                        eventBus.emit(Events.DETECTION_PREVIEW_CLICKED, { index });
                        event.preventDefaultAction = true;
                        return;
                    }
                } catch (_) { /* isPointInFill not supported — skip */ }
            }

            // 2) Test annotation shapes
            const shapes = this.annoGroup.querySelectorAll('[data-annotation-id]');
            for (const shape of shapes) {
                try {
                    // For <g> elements (MultiPolygon), test children
                    const targets = shape.tagName === 'g'
                        ? shape.querySelectorAll('polygon, circle, rect')
                        : [shape];
                    for (const target of targets) {
                        if (target.isPointInFill?.(svgPoint) || target.isPointInStroke?.(svgPoint)) {
                            // Quiz mode: reveal before selecting
                            if (this._quizMode && !this._revealedAnnotations.has(shape.dataset.annotationId)) {
                                this._revealedAnnotations.add(shape.dataset.annotationId);
                                this.render();
                                event.preventDefaultAction = true;
                                return;
                            }
                            annotationStore.selectAnnotation(shape.dataset.annotationId);
                            event.preventDefaultAction = true;
                            return;
                        }
                    }
                } catch (_) { /* skip */ }
            }
        };
        this.viewer.addHandler('canvas-click', this._boundCanvasClick);

        // Quiz mode toggle
        this._unsubscribers.push(
            eventBus.on(Events.QUIZ_MODE_TOGGLE, ({ enabled }) => {
                this._quizMode = enabled;
                this._revealedAnnotations.clear();
                this.render();
            }),
        );
    }

    _extractSlideDimensions() {
        try {
            const tiledImage = this.viewer.world.getItemAt(0);
            if (tiledImage) {
                const size = tiledImage.getContentSize();
                this.slideDimensions = { width: size.x, height: size.y };
            }
        } catch {
            // Will be set later when image loads
        }
    }

    // ==========================================
    // VIEWBOX MANAGEMENT
    // ==========================================

    _updateViewBox() {
        if (!this.svg || !this.viewer || !this.slideDimensions) {return;}

        const viewport = this.viewer.viewport;
        const bounds = viewport.getBounds(true);
        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) {return;}

        // Convert viewport bounds to image pixel coordinates
        const topLeft = tiledImage.viewportToImageCoordinates(bounds.x, bounds.y);
        const bottomRight = tiledImage.viewportToImageCoordinates(
            bounds.x + bounds.width,
            bounds.y + bounds.height,
        );

        const x = topLeft.x;
        const y = topLeft.y;
        const w = bottomRight.x - topLeft.x;
        const h = bottomRight.y - topLeft.y;

        this.svg.setAttribute('viewBox', `${x} ${y} ${w} ${h}`);
    }

    // ==========================================
    // RENDERING
    // ==========================================

    render() {
        if (!this.annoGroup) {return;}

        // Clear existing
        while (this.annoGroup.firstChild) {
            this.annoGroup.removeChild(this.annoGroup.firstChild);
        }

        const annotations = annotationStore.getAll();

        for (const anno of annotations) {
            // Check layer visibility
            const layerKey = anno.label_id || anno.annotation_type;
            if (!annotationStore.isLayerVisible(layerKey)) {continue;}

            const el = this._createAnnotationElement(anno);
            if (el) {
                this.annoGroup.appendChild(el);
            }
        }
    }

    _createAnnotationElement(anno) {
        let color = anno.label?.color || annotationStore.getLabelColor(anno.label_id) || '#FF0000';
        const opacity = annotationStore.getLayerOpacity(anno.label_id || anno.annotation_type);
        const isSelected = anno.id === annotationStore.selectedId;

        // Quiz mode: mask label colors until revealed
        if (this._quizMode && !this._revealedAnnotations.has(anno.id)) {
            color = '#6b7280'; // neutral gray
        }

        const geom = anno.geometry;
        if (!geom) {return null;}

        let el = null;

        switch (geom.type) {
            case 'Polygon':
                el = this._createPolygon(geom.coordinates, color, opacity);
                break;
            case 'Point':
                el = this._createPoint(geom.coordinates, color, opacity);
                break;
            case 'MultiPolygon':
                el = this._createMultiPolygon(geom.coordinates, color, opacity);
                break;
            case 'LineString':
                el = this._createArrow(geom.coordinates, color, opacity, anno.properties?.text);
                break;
            default:
                el = this._createPolygon(geom.coordinates, color, opacity);
        }

        if (el) {
            el.dataset.annotationId = anno.id;

            if (isSelected) {
                el.classList.add('annotation--selected');
            }
        }

        return el;
    }

    _createPolygon(coordinates, color, opacity) {
        if (!coordinates || !coordinates[0]) {return null;}

        const ring = coordinates[0];
        const points = ring.map(c => `${c[0]},${c[1]}`).join(' ');

        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points);
        polygon.setAttribute('fill', color);
        polygon.setAttribute('fill-opacity', opacity);
        polygon.setAttribute('stroke', color);
        polygon.setAttribute('stroke-width', this._getStrokeWidth());
        polygon.setAttribute('stroke-opacity', '0.9');
        polygon.classList.add('annotation-shape');

        return polygon;
    }

    _createMultiPolygon(coordinates, color, opacity) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        for (const polygonCoords of coordinates) {
            const el = this._createPolygon(polygonCoords, color, opacity);
            if (el) {g.appendChild(el);}
        }
        return g;
    }

    _createPoint(coordinates, color, opacity) {
        const [x, y] = coordinates;
        const r = this._getPointRadius();

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', x);
        circle.setAttribute('cy', y);
        circle.setAttribute('r', r);
        circle.setAttribute('fill', color);
        circle.setAttribute('fill-opacity', opacity);
        circle.setAttribute('stroke', color);
        circle.setAttribute('stroke-width', this._getStrokeWidth());
        circle.classList.add('annotation-shape');

        return circle;
    }

    /**
     * Create an arrow annotation (SVG group with line + arrowhead + text)
     * @param {Array} coordinates - [[x1,y1],[x2,y2]]
     * @param {string} color
     * @param {number} opacity
     * @param {string} [text]
     * @returns {SVGGElement}
     * @private
     */
    _createArrow(coordinates, color, opacity, text) {
        if (!coordinates || coordinates.length < 2) {return null;}

        const [[x1, y1], [x2, y2]] = coordinates;
        const strokeWidth = this._getStrokeWidth();
        const markerId = this._ensureArrowMarker(color);

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.classList.add('annotation-shape', 'annotation-arrow');

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('stroke', color);
        line.setAttribute('stroke-width', strokeWidth);
        line.setAttribute('stroke-opacity', opacity);
        line.setAttribute('marker-end', `url(#${markerId})`);
        g.appendChild(line);

        if (text) {
            const svgText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            svgText.setAttribute('x', x2);
            svgText.setAttribute('y', y2 - strokeWidth * 4);
            svgText.setAttribute('text-anchor', 'middle');
            svgText.setAttribute('fill', color);
            svgText.setAttribute('font-size', strokeWidth * 8);
            svgText.setAttribute('font-family', 'JetBrains Mono, monospace');
            svgText.classList.add('annotation-arrow__text');
            // Use textContent — safe, no innerHTML with user data
            svgText.textContent = text;
            g.appendChild(svgText);
        }

        return g;
    }

    /**
     * Ensure an arrowhead marker for the given color exists in SVG defs.
     * Returns the marker id.
     * @param {string} color
     * @returns {string} marker id
     * @private
     */
    _ensureArrowMarker(color) {
        // Create a stable id from the color string (strip non-alphanumeric)
        const safeColor = color.replace(/[^a-zA-Z0-9]/g, '');
        const markerId = `arrow-marker-${safeColor}`;

        const defs = this.svg.querySelector('defs');
        if (defs.querySelector(`#${markerId}`)) {
            return markerId;
        }

        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', markerId);
        marker.setAttribute('markerWidth', '8');
        marker.setAttribute('markerHeight', '8');
        marker.setAttribute('refX', '6');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        marker.setAttribute('markerUnits', 'strokeWidth');

        const triangle = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        triangle.setAttribute('points', '0 0, 6 3, 0 6');
        triangle.setAttribute('fill', color);
        marker.appendChild(triangle);

        defs.appendChild(marker);
        return markerId;
    }

    _getStrokeWidth() {
        // Scale stroke width with zoom so it stays visible
        if (!this.slideDimensions) {return 3;}
        return Math.max(1, this.slideDimensions.width / 5000);
    }

    _getPointRadius() {
        if (!this.slideDimensions) {return 10;}
        return Math.max(5, this.slideDimensions.width / 2000);
    }

    // ==========================================
    // SELECTION
    // ==========================================

    _highlightSelected(annotationId) {
        // Remove previous selection highlight
        const prev = this.svg.querySelector('.annotation--selected');
        if (prev) {prev.classList.remove('annotation--selected');}

        if (annotationId) {
            const el = this.svg.querySelector(`[data-annotation-id="${annotationId}"]`);
            if (el) {el.classList.add('annotation--selected');}
        }
    }

    // ==========================================
    // DETECTION PREVIEWS
    // ==========================================

    _renderPreviews(features) {
        while (this.previewGroup.firstChild) {
            this.previewGroup.removeChild(this.previewGroup.firstChild);
        }

        if (!features || features.length === 0) {return;}

        for (let i = 0; i < features.length; i++) {
            const f = features[i];
            if (f.geometry.type !== 'Polygon') {continue;}

            const ring = f.geometry.coordinates[0];
            const points = ring.map(c => `${c[0]},${c[1]}`).join(' ');
            const confidence = f.properties?.confidence || 0;

            const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            polygon.setAttribute('points', points);
            polygon.setAttribute('fill', `rgba(255, 165, 0, ${confidence * 0.3})`);
            polygon.setAttribute('stroke', '#FFA500');
            polygon.setAttribute('stroke-width', this._getStrokeWidth());
            polygon.setAttribute('stroke-dasharray', `${this._getStrokeWidth() * 3} ${this._getStrokeWidth() * 2}`);
            polygon.setAttribute('stroke-opacity', '0.8');
            polygon.classList.add('detection-preview');
            polygon.dataset.detectionIndex = i;

            this.previewGroup.appendChild(polygon);
        }
    }

    /**
     * Highlight a specific detection preview on the slide
     * @param {number} index - Detection index to highlight
     * @private
     */
    _highlightDetectionPreview(index) {
        // Remove previous highlight
        const prev = this.previewGroup.querySelector('.detection-preview--active');
        if (prev) {
            prev.classList.remove('detection-preview--active');
            prev.setAttribute('stroke', '#FFA500');
            prev.setAttribute('stroke-width', this._getStrokeWidth());
        }

        // Apply highlight to target
        const target = this.previewGroup.querySelector(`[data-detection-index="${index}"]`);
        if (target) {
            target.classList.add('detection-preview--active');
            target.setAttribute('stroke', '#FF4500');
            target.setAttribute('stroke-width', this._getStrokeWidth() * 2.5);

            eventBus.emit(Events.DETECTION_HIGHLIGHT, { index });
        }
    }

    // ==========================================
    // DISAGREEMENT OVERLAY (Quality Metrics)
    // ==========================================

    _renderDisagreements(features) {
        while (this.disagreementGroup.firstChild) {
            this.disagreementGroup.removeChild(this.disagreementGroup.firstChild);
        }

        if (!features || features.length === 0) {return;}

        // Add hatched pattern to defs if not already present
        const defs = this.svg.querySelector('defs');
        if (!defs.querySelector('#disagreement-hatch')) {
            const pattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
            pattern.setAttribute('id', 'disagreement-hatch');
            pattern.setAttribute('patternUnits', 'userSpaceOnUse');
            const hatchSize = this._getStrokeWidth() * 6;
            pattern.setAttribute('width', hatchSize);
            pattern.setAttribute('height', hatchSize);
            pattern.setAttribute('patternTransform', 'rotate(45)');

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', '0');
            line.setAttribute('y1', '0');
            line.setAttribute('x2', '0');
            line.setAttribute('y2', hatchSize);
            line.setAttribute('stroke', 'rgba(244, 67, 54, 0.6)');
            line.setAttribute('stroke-width', this._getStrokeWidth() * 2);
            pattern.appendChild(line);
            defs.appendChild(pattern);
        }

        for (const feature of features) {
            const geom = feature.geometry;
            if (!geom) {continue;}

            let el = null;
            if (geom.type === 'Polygon' && geom.coordinates && geom.coordinates[0]) {
                const points = geom.coordinates[0].map(c => `${c[0]},${c[1]}`).join(' ');
                el = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                el.setAttribute('points', points);
            } else if (geom.type === 'MultiPolygon' && geom.coordinates) {
                el = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                for (const polyCoords of geom.coordinates) {
                    if (polyCoords[0]) {
                        const points = polyCoords[0].map(c => `${c[0]},${c[1]}`).join(' ');
                        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                        poly.setAttribute('points', points);
                        poly.setAttribute('fill', 'url(#disagreement-hatch)');
                        poly.setAttribute('fill-opacity', '0.4');
                        poly.setAttribute('stroke', '#f44336');
                        poly.setAttribute('stroke-width', this._getStrokeWidth());
                        poly.setAttribute('stroke-opacity', '0.8');
                        el.appendChild(poly);
                    }
                }
            }

            if (el && el.tagName !== 'g') {
                el.setAttribute('fill', 'url(#disagreement-hatch)');
                el.setAttribute('fill-opacity', '0.4');
                el.setAttribute('stroke', '#f44336');
                el.setAttribute('stroke-width', this._getStrokeWidth());
                el.setAttribute('stroke-opacity', '0.8');
            }

            if (el) {
                el.classList.add('disagreement-region');
                const props = feature.properties || {};
                el.dataset.labelA = props.label_a || '';
                el.dataset.labelB = props.label_b || '';
                this.disagreementGroup.appendChild(el);
            }
        }
    }

    // ==========================================
    // PUBLIC API FOR DRAWING TOOLS
    // ==========================================

    /**
     * Get the SVG element for drawing tools to draw on
     */
    getSvg() {
        return this.svg;
    }

    /**
     * Get the preview group for temporary drawing shapes
     */
    getPreviewGroup() {
        return this.previewGroup;
    }

    /**
     * Convert screen pixel coordinates to slide pixel coordinates
     * @param {number} screenX
     * @param {number} screenY
     * @returns {{x: number, y: number}} Slide pixel coordinates
     */
    screenToSlide(screenX, screenY) {
        const point = this.viewer.viewport.pointFromPixel(
            new OpenSeadragon.Point(screenX, screenY),
        );
        const tiledImage = this.viewer.world.getItemAt(0);
        if (!tiledImage) {return { x: screenX, y: screenY };}

        const imagePoint = tiledImage.viewportToImageCoordinates(point);
        return { x: imagePoint.x, y: imagePoint.y };
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    destroy() {
        if (this.viewer) {
            this.viewer.removeHandler('viewport-change', this._boundUpdate);
            this.viewer.removeHandler('resize', this._boundUpdate);
        }

        if (this.viewer && this._boundCanvasClick) {
            this.viewer.removeHandler('canvas-click', this._boundCanvasClick);
        }

        // Properly unsubscribe from all event listeners
        this._unsubscribers.forEach(unsubscribe => unsubscribe());
        this._unsubscribers = [];

        if (this.svg && this.svg.parentNode) {
            this.svg.parentNode.removeChild(this.svg);
        }

        this.svg = null;
        this.annoGroup = null;
        this.previewGroup = null;
        this.disagreementGroup = null;
    }
}

export { AnnotationLayer };
export default AnnotationLayer;
