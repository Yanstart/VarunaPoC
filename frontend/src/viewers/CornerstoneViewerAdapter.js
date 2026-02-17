import { ViewerInterface } from './ViewerInterface.js';

/**
 * CornerstoneViewerAdapter — Placeholder for future Cornerstone3D integration.
 * See docs/architecture/cornerstone3d-evaluation.md for Go/No-Go decision.
 */
export class CornerstoneViewerAdapter extends ViewerInterface {
    constructor() {
        super();
        console.warn('CornerstoneViewerAdapter is a stub — Cornerstone3D integration is deferred.');
    }

    panTo() { this._notImplemented(); }
    zoomTo() { this._notImplemented(); }
    fitBounds() { this._notImplemented(); }
    setSource() { this._notImplemented(); }
    addOverlay() { this._notImplemented(); }
    removeOverlay() { this._notImplemented(); }
    on() { this._notImplemented(); }
    off() { this._notImplemented(); }
    getViewport() { this._notImplemented(); }
    setViewport() { this._notImplemented(); }
    getZoom() { this._notImplemented(); }
    destroy() {}

    _notImplemented() {
        throw new Error('CornerstoneViewerAdapter is not yet implemented. See cornerstone3d-evaluation.md');
    }
}
