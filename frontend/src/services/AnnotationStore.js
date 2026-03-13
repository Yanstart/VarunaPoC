/**
 * AnnotationStore - Client-side state management for annotations
 *
 * Manages the local annotation state, communicates with the backend API,
 * and emits events for UI components (AnnotationLayer, DrawingTools, etc.).
 *
 * @module services/AnnotationStore
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from './ApiService.js';

/**
 * Singleton instance
 * @type {AnnotationStore|null}
 */
let instance = null;

class AnnotationStore {
    constructor() {
        if (instance) {return instance;}

        /** @type {Map<string, Object>} annotation id → annotation object */
        this.annotations = new Map();

        /** @type {string|null} Currently selected annotation ID */
        this.selectedId = null;

        /** @type {string} Active drawing tool: select, rectangle, polygon, point, circle, freehand */
        this.activeTool = 'select';

        /** @type {string|null} Active label ID for new annotations */
        this.activeLabel = null;

        /** @type {Map<string, boolean>} Layer visibility by label ID or type */
        this.visibleLayers = new Map();

        /** @type {Map<string, number>} Layer opacity by label ID or type */
        this.layerOpacity = new Map();

        /** @type {string|null} Current slide ID */
        this.slideId = null;

        /** @type {Array<Object>} Available labels */
        this.labels = [];

        /** @type {Array<Object>} Detection preview (not yet saved) */
        this.detectionPreview = [];

        /** @type {Object|null} Cached annotation statistics */
        this.stats = null;

        instance = this;
    }

    static getInstance() {
        if (!instance) {instance = new AnnotationStore();}
        return instance;
    }

    // ==========================================
    // SLIDE MANAGEMENT
    // ==========================================

    /**
     * Set the active slide and load its annotations
     * @param {string} slideId
     */
    async setSlide(slideId) {
        this.slideId = slideId;
        this.annotations.clear();
        this.selectedId = null;
        this.detectionPreview = [];

        await this.loadAnnotations();
        await this.loadLabels();
    }

    /**
     * Clear all state (on page navigation)
     */
    clear() {
        this.annotations.clear();
        this.selectedId = null;
        this.slideId = null;
        this.detectionPreview = [];
    }

    // ==========================================
    // ANNOTATION CRUD
    // ==========================================

    async loadAnnotations() {
        if (!this.slideId) {return;}

        try {
            const annotations = await apiService.getAnnotations(this.slideId);
            this.annotations.clear();
            for (const anno of annotations) {
                this.annotations.set(anno.id, anno);
            }
            eventBus.emit(Events.ANNOTATIONS_LOADED, {
                slideId: this.slideId,
                count: this.annotations.size,
            });
            this.loadStats();
        } catch (err) {
            console.error('[AnnotationStore] Failed to load annotations:', err);
        }
    }

    async createAnnotation(data) {
        if (!this.slideId) {return null;}

        try {
            const annotation = await apiService.createAnnotation(this.slideId, {
                ...data,
                label_id: data.label_id || this.activeLabel,
            });
            this.annotations.set(annotation.id, annotation);
            eventBus.emit(Events.ANNOTATION_CREATED, { annotation });
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: 'Annotation sauvegard\u00e9e',
                duration: 2000,
            });
            this.loadStats();
            return annotation;
        } catch (err) {
            console.error('[AnnotationStore] Failed to create annotation:', err);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Sauvegarde de l\u2019annotation \u00e9chou\u00e9e. V\u00e9rifiez la connexion.',
            });
            return null;
        }
    }

    async updateAnnotation(annotationId, data) {
        if (!this.slideId) {return null;}

        try {
            const annotation = await apiService.updateAnnotation(
                this.slideId, annotationId, data,
            );
            this.annotations.set(annotation.id, annotation);
            eventBus.emit(Events.ANNOTATION_UPDATED, { annotation });
            return annotation;
        } catch (err) {
            console.error('[AnnotationStore] Failed to update annotation:', err);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Mise \u00e0 jour de l\u2019annotation \u00e9chou\u00e9e.',
            });
            return null;
        }
    }

    async deleteAnnotation(annotationId) {
        if (!this.slideId) {return false;}

        try {
            await apiService.deleteAnnotation(this.slideId, annotationId);
            this.annotations.delete(annotationId);
            if (this.selectedId === annotationId) {
                this.selectedId = null;
            }
            eventBus.emit(Events.ANNOTATION_DELETED, { annotationId });
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: 'Annotation supprim\u00e9e',
                duration: 2000,
            });
            this.loadStats();
            return true;
        } catch (err) {
            console.error('[AnnotationStore] Failed to delete annotation:', err);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: 'Suppression de l\u2019annotation \u00e9chou\u00e9e.',
            });
            return false;
        }
    }

    // ==========================================
    // SELECTION
    // ==========================================

    selectAnnotation(annotationId) {
        this.selectedId = annotationId;
        eventBus.emit(Events.ANNOTATION_SELECTED, {
            annotationId,
            annotation: annotationId ? this.annotations.get(annotationId) : null,
        });
    }

    getSelected() {
        return this.selectedId ? this.annotations.get(this.selectedId) : null;
    }

    // ==========================================
    // TOOLS
    // ==========================================

    setTool(toolName) {
        this.activeTool = toolName;
        eventBus.emit(Events.TOOL_CHANGED, { tool: toolName });
    }

    setActiveLabel(labelId) {
        this.activeLabel = labelId;
    }

    // ==========================================
    // LAYERS
    // ==========================================

    setLayerVisibility(layerKey, visible) {
        this.visibleLayers.set(layerKey, visible);
        eventBus.emit(Events.LAYER_VISIBILITY_CHANGED, { layerKey, visible });
    }

    isLayerVisible(layerKey) {
        return this.visibleLayers.get(layerKey) !== false;
    }

    setLayerOpacity(layerKey, opacity) {
        this.layerOpacity.set(layerKey, opacity);
        eventBus.emit(Events.LAYER_OPACITY_CHANGED, { layerKey, opacity });
    }

    getLayerOpacity(layerKey) {
        return this.layerOpacity.get(layerKey) ?? 0.7;
    }

    // ==========================================
    // LABELS
    // ==========================================

    async loadLabels() {
        try {
            this.labels = await apiService.getLabels();
        } catch (err) {
            console.warn('[AnnotationStore] Labels not available:', err.message);
            this.labels = [];
        }
    }

    getLabelById(labelId) {
        return this.labels.find(l => l.id === labelId);
    }

    getLabelColor(labelId) {
        const label = this.getLabelById(labelId);
        return label ? label.color : '#FF0000';
    }

    // ==========================================
    // DETECTION PREVIEW
    // ==========================================

    setDetectionPreview(features) {
        this.detectionPreview = features;
        eventBus.emit(Events.DETECTION_PREVIEW, { features });
    }

    clearDetectionPreview() {
        this.detectionPreview = [];
        eventBus.emit(Events.DETECTION_PREVIEW, { features: [] });
    }

    async confirmDetections(featureIndices = null, labelId = null) {
        if (!this.slideId || this.detectionPreview.length === 0) {return;}

        const features = featureIndices
            ? featureIndices.map(i => this.detectionPreview[i])
            : this.detectionPreview;

        const annotations = features.map(f => ({
            geometry: f.geometry,
            geometry_type: 'polygon',
            annotation_type: 'auto_confirmed',
            label_id: labelId || null,
            confidence: f.properties?.confidence,
            properties: f.properties,
        }));

        try {
            const created = await apiService.batchCreateAnnotations(
                this.slideId, annotations,
            );
            for (const anno of created) {
                this.annotations.set(anno.id, anno);
            }
            this.clearDetectionPreview();
            eventBus.emit(Events.DETECTION_CONFIRM, { count: created.length });
            this.loadStats();
            eventBus.emit(Events.ANNOTATIONS_LOADED, {
                slideId: this.slideId,
                count: this.annotations.size,
            });
            return created;
        } catch (err) {
            console.error('[AnnotationStore] Failed to confirm detections:', err);
            return null;
        }
    }

    // ==========================================
    // STATISTICS / COUNTING
    // ==========================================

    /**
     * Load annotation statistics from backend
     * @returns {Promise<Object|null>}
     */
    async loadStats() {
        if (!this.slideId) {return null;}
        try {
            this.stats = await apiService.getAnnotationStats(this.slideId);
            eventBus.emit(Events.ANNOTATION_STATS_UPDATED, this.stats);
            return this.stats;
        } catch (err) {
            // Stats endpoint may not be available (no DB)
            this.stats = this.computeLocalStats();
            eventBus.emit(Events.ANNOTATION_STATS_UPDATED, this.stats);
            return this.stats;
        }
    }

    /**
     * Compute stats from local annotation cache (fallback when DB unavailable)
     * @returns {Object}
     */
    computeLocalStats() {
        const all = this.getAll();
        const byType = {};
        const byLabel = {};
        let highConf = 0, medConf = 0, lowConf = 0, unscored = 0;

        for (const a of all) {
            // By type
            byType[a.annotation_type] = (byType[a.annotation_type] || 0) + 1;

            // By label
            if (a.label) {
                const key = a.label.id;
                if (!byLabel[key]) {
                    byLabel[key] = { label_id: a.label.id, name: a.label.name, color: a.label.color, count: 0 };
                }
                byLabel[key].count++;
            }

            // Confidence
            if (a.confidence === null || a.confidence === undefined) {unscored++;} else if (a.confidence >= 0.8) {highConf++;} else if (a.confidence >= 0.5) {medConf++;} else {lowConf++;}
        }

        return {
            slide_id: this.slideId,
            total: all.length,
            by_type: Object.entries(byType).map(([type, count]) => ({ type, count })),
            by_label: Object.values(byLabel),
            unlabeled: all.filter(a => !a.label_id).length,
            confidence_distribution: { high: highConf, medium: medConf, low: lowConf, unscored },
        };
    }

    // ==========================================
    // EXPORT
    // ==========================================

    async exportGeoJSON() {
        if (!this.slideId) {return null;}
        return apiService.exportAnnotations(this.slideId);
    }

    // ==========================================
    // ACCESSORS
    // ==========================================

    getAll() {
        return Array.from(this.annotations.values());
    }

    getBySlide(slideId) {
        return this.getAll().filter(a => a.slide_id === slideId);
    }

    getByType(type) {
        return this.getAll().filter(a => a.annotation_type === type);
    }
}

export const annotationStore = AnnotationStore.getInstance();
export { AnnotationStore };
export default annotationStore;
