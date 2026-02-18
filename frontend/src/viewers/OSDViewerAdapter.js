import { ViewerInterface } from './ViewerInterface.js';

/**
 * OSDViewerAdapter — OpenSeadragon implementation of ViewerInterface.
 * Wraps an existing OSD viewer instance.
 */
export class OSDViewerAdapter extends ViewerInterface {
    /**
     * @param {OpenSeadragon.Viewer} osdViewer - An existing OSD viewer instance
     */
    constructor(osdViewer) {
        super();
        this._osd = osdViewer;
        this._listeners = new Map();
        this._setupEventBridge();
    }

    panTo(x, y) {
        const point = new OpenSeadragon.Point(x, y);
        const viewportPoint = this._osd.viewport.imageToViewportCoordinates(point);
        this._osd.viewport.panTo(viewportPoint);
    }

    zoomTo(level) {
        this._osd.viewport.zoomTo(level);
    }

    fitBounds() {
        this._osd.viewport.goHome();
    }

    setSource(tileSource) {
        this._osd.open(tileSource);
    }

    addOverlay(element, location) {
        this._osd.addOverlay({ element, location: new OpenSeadragon.Rect(...location) });
    }

    removeOverlay(element) {
        this._osd.removeOverlay(element);
    }

    on(event, callback) {
        // Map ViewerInterface events to OSD events
        const osdEvent = this._mapEvent(event);
        if (osdEvent) {
            const handler = (osdEvt) => callback(this._normalizeEvent(osdEvt));
            this._listeners.set(`${event}:${callback}`, handler);
            this._osd.addHandler(osdEvent, handler);
        }
    }

    off(event, callback) {
        const key = `${event}:${callback}`;
        const handler = this._listeners.get(key);
        if (handler) {
            const osdEvent = this._mapEvent(event);
            this._osd.removeHandler(osdEvent, handler);
            this._listeners.delete(key);
        }
    }

    getViewport() {
        const bounds = this._osd.viewport.getBounds();
        return { x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height };
    }

    setViewport(bounds) {
        this._osd.viewport.fitBounds(
            new OpenSeadragon.Rect(bounds.x, bounds.y, bounds.width, bounds.height)
        );
    }

    getZoom() {
        return this._osd.viewport.getZoom();
    }

    destroy() {
        this._listeners.clear();
        // Don't destroy the OSD viewer itself — that's managed by ViewerInstance
    }

    _mapEvent(event) {
        const map = {
            [ViewerInterface.Events.ZOOM_CHANGED]: 'zoom',
            [ViewerInterface.Events.PAN_CHANGED]: 'pan',
            [ViewerInterface.Events.VIEWPORT_CHANGED]: 'viewport-change',
            [ViewerInterface.Events.TILE_LOADED]: 'tile-loaded',
            [ViewerInterface.Events.READY]: 'open',
            [ViewerInterface.Events.ERROR]: 'open-failed',
        };
        return map[event] || null;
    }

    _normalizeEvent(osdEvent) {
        return { originalEvent: osdEvent, source: 'openseadragon' };
    }

    _setupEventBridge() {
        // Could auto-emit events here if needed
    }
}
