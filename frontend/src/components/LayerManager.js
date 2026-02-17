/**
 * LayerManager - Annotation layer visibility and opacity control
 *
 * Panel showing annotation layers grouped by label and type,
 * with toggle visibility, opacity slider, and count per layer.
 *
 * @module components/LayerManager
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';

class LayerManager {
    /**
     * @param {HTMLElement} container - Parent container element
     */
    constructor(container) {
        this.container = container;
        this.element = null;
        this._unsubscribers = [];
        this._create();
        this._setupEventListeners();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'layer-manager';
        this.element.innerHTML = `
            <div class="layer-manager__header">
                <h3>Couches</h3>
                <button class="layer-manager__export" title="Exporter GeoJSON">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
            </div>
            <div class="layer-manager__list"></div>
        `;

        this.element.querySelector('.layer-manager__export').addEventListener('click', () => {
            this._exportGeoJSON();
        });

        this.container.appendChild(this.element);
    }

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATIONS_LOADED, () => this.render()),
            eventBus.on(Events.ANNOTATION_CREATED, () => this.render()),
            eventBus.on(Events.ANNOTATION_DELETED, () => this.render()),
            eventBus.on(Events.DETECTION_CONFIRM, () => this.render()),
        );
    }

    render() {
        if (!this.element) {return;}
        const list = this.element.querySelector('.layer-manager__list');
        list.innerHTML = '';

        const annotations = annotationStore.getAll();
        if (annotations.length === 0) {
            list.innerHTML = '<div class="layer-manager__empty">Aucune annotation</div>';
            return;
        }

        // Group by label, then by annotation_type
        const groups = new Map();

        for (const anno of annotations) {
            const label = anno.label;
            const key = label ? label.id : `type:${anno.annotation_type}`;
            const name = label ? label.name : anno.annotation_type;
            const color = label ? label.color : this._typeColor(anno.annotation_type);

            if (!groups.has(key)) {
                groups.set(key, { key, name, color, count: 0, type: anno.annotation_type });
            }
            groups.get(key).count++;
        }

        for (const group of groups.values()) {
            const item = this._createLayerItem(group);
            list.appendChild(item);
        }
    }

    _createLayerItem(group) {
        const isVisible = annotationStore.isLayerVisible(group.key);
        const opacity = annotationStore.getLayerOpacity(group.key);

        const eyeOpen = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
        const eyeClosed = '<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';

        const item = document.createElement('div');
        item.className = 'layer-item';
        item.innerHTML = `
            <button class="layer-item__visibility ${isVisible ? 'is-visible' : ''}" title="Afficher/masquer">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${isVisible ? eyeOpen : eyeClosed}
                </svg>
            </button>
            <span class="layer-item__color" style="background: ${group.color}"></span>
            <span class="layer-item__name">${group.name}</span>
            <span class="layer-item__count">${group.count}</span>
            <input
                type="range"
                class="layer-item__opacity"
                min="0" max="1" step="0.05"
                value="${opacity}"
                title="Opacité : ${Math.round(opacity * 100)}%"
            >
        `;

        // Toggle visibility
        item.querySelector('.layer-item__visibility').addEventListener('click', () => {
            const newVisible = !annotationStore.isLayerVisible(group.key);
            annotationStore.setLayerVisibility(group.key, newVisible);
            this.render();
        });

        // Opacity slider
        item.querySelector('.layer-item__opacity').addEventListener('input', (e) => {
            annotationStore.setLayerOpacity(group.key, parseFloat(e.target.value));
        });

        return item;
    }

    _typeColor(type) {
        switch (type) {
            case 'manual': return '#4a9eff';
            case 'auto': return '#FFA500';
            case 'auto_confirmed': return '#4CAF50';
            default: return '#888';
        }
    }

    async _exportGeoJSON() {
        try {
            const geojson = await annotationStore.exportGeoJSON();
            if (!geojson) {return;}

            const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `annotations_${annotationStore.slideId || 'export'}.geojson`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('[LayerManager] Export failed:', err);
        }
    }

    destroy() {
        for (const unsub of this._unsubscribers) {
            unsub();
        }
        this._unsubscribers = [];

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { LayerManager };
export default LayerManager;
