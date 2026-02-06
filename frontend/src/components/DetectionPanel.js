/**
 * DetectionPanel - Auto-detection workflow with accept/reject
 *
 * Workflow:
 * 1. User clicks "Auto-Detect"
 * 2. Adjusts threshold slider
 * 3. Loading state while backend runs detection pipeline
 * 4. Preview mode: detected regions shown as dashed outlines
 * 5. User accepts/rejects individual detections
 * 6. "Confirm All" → batch POST to annotations API (type=auto_confirmed)
 *
 * This implements the Quality-First feedback loop from VISION_V3.
 *
 * @module components/DetectionPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { annotationStore } from '../services/AnnotationStore.js';

class DetectionPanel {
    /**
     * @param {HTMLElement} container
     * @param {Object} options
     * @param {string} options.slideId
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        // State
        this.isDetecting = false;
        this.threshold = 0.5;
        this.minArea = 100;
        this.predictionClass = 'tissue';
        this.detectionResult = null;

        /** @type {Set<number>} Indices of accepted detections */
        this.accepted = new Set();
        /** @type {Set<number>} Indices of rejected detections */
        this.rejected = new Set();

        this.element = null;
        this._create();
    }

    setSlide(slideId) {
        this.slideId = slideId;
        this._resetState();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'detection-panel';
        this._renderIdle();
        this.container.appendChild(this.element);
    }

    // ==========================================
    // STATE: IDLE (no detection running)
    // ==========================================

    _renderIdle() {
        this.element.innerHTML = `
            <div class="detection-panel__section">
                <h4>Auto-Detection</h4>
                <p class="detection-panel__desc">
                    Detect regions of interest using ML heatmap analysis.
                </p>

                <div class="detection-panel__control">
                    <label>Threshold: <span class="detection-panel__value">${this.threshold}</span></label>
                    <input type="range" class="detection-panel__slider"
                        min="0.1" max="0.95" step="0.05" value="${this.threshold}">
                </div>

                <div class="detection-panel__control">
                    <label>Min Area: <span class="detection-panel__value">${this.minArea} px</span></label>
                    <input type="range" class="detection-panel__slider"
                        min="10" max="1000" step="10" value="${this.minArea}">
                </div>

                <button class="detection-panel__btn detection-panel__btn--primary" ${!this.slideId ? 'disabled' : ''}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    Detect Regions
                </button>
            </div>
        `;

        // Threshold slider
        const sliders = this.element.querySelectorAll('.detection-panel__slider');
        sliders[0].addEventListener('input', (e) => {
            this.threshold = parseFloat(e.target.value);
            e.target.previousElementSibling.querySelector('.detection-panel__value').textContent = this.threshold;
        });

        // Min area slider
        sliders[1].addEventListener('input', (e) => {
            this.minArea = parseInt(e.target.value);
            e.target.previousElementSibling.querySelector('.detection-panel__value').textContent = `${this.minArea} px`;
        });

        // Detect button
        this.element.querySelector('.detection-panel__btn--primary').addEventListener('click', () => {
            this._runDetection();
        });
    }

    // ==========================================
    // STATE: DETECTING (loading)
    // ==========================================

    _renderLoading() {
        this.element.innerHTML = `
            <div class="detection-panel__section">
                <h4>Auto-Detection</h4>
                <div class="detection-panel__loading">
                    <div class="detection-panel__spinner"></div>
                    <span>Detecting regions...</span>
                </div>
            </div>
        `;
    }

    // ==========================================
    // STATE: PREVIEW (results ready)
    // ==========================================

    _renderPreview() {
        if (!this.detectionResult) return;

        const features = this.detectionResult.geojson.features;
        const total = features.length;
        const acceptedCount = this.accepted.size;
        const rejectedCount = this.rejected.size;
        const pendingCount = total - acceptedCount - rejectedCount;

        this.element.innerHTML = `
            <div class="detection-panel__section">
                <h4>Detection Results</h4>
                <div class="detection-panel__stats">
                    <span class="stat stat--total">${total} regions found</span>
                    <span class="stat stat--accepted">${acceptedCount} accepted</span>
                    <span class="stat stat--rejected">${rejectedCount} rejected</span>
                </div>

                <div class="detection-panel__results">
                    ${features.map((f, i) => this._renderDetectionItem(f, i)).join('')}
                </div>

                <div class="detection-panel__actions">
                    <button class="detection-panel__btn detection-panel__btn--confirm"
                        ${acceptedCount === 0 && pendingCount === 0 ? 'disabled' : ''}>
                        Confirm ${acceptedCount > 0 ? acceptedCount : 'All'} Annotations
                    </button>
                    <button class="detection-panel__btn detection-panel__btn--secondary">
                        Accept All
                    </button>
                    <button class="detection-panel__btn detection-panel__btn--danger">
                        Discard All
                    </button>
                </div>
            </div>
        `;

        // Item accept/reject buttons
        this.element.querySelectorAll('.detection-item__accept').forEach((btn) => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                this._toggleAccept(idx);
            });
        });

        this.element.querySelectorAll('.detection-item__reject').forEach((btn) => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.index);
                this._toggleReject(idx);
            });
        });

        // Action buttons
        this.element.querySelector('.detection-panel__btn--confirm').addEventListener('click', () => {
            this._confirmDetections();
        });

        this.element.querySelector('.detection-panel__btn--secondary').addEventListener('click', () => {
            features.forEach((_, i) => {
                this.rejected.delete(i);
                this.accepted.add(i);
            });
            this._renderPreview();
        });

        this.element.querySelector('.detection-panel__btn--danger').addEventListener('click', () => {
            this._resetState();
            this._renderIdle();
        });
    }

    _renderDetectionItem(feature, index) {
        const confidence = (feature.properties?.confidence || 0).toFixed(2);
        const area = Math.round(feature.properties?.area_px || 0);
        const isAccepted = this.accepted.has(index);
        const isRejected = this.rejected.has(index);

        return `
            <div class="detection-item ${isAccepted ? 'is-accepted' : ''} ${isRejected ? 'is-rejected' : ''}">
                <div class="detection-item__info">
                    <span class="detection-item__label">Region ${index + 1}</span>
                    <span class="detection-item__meta">${confidence} conf | ${area} px</span>
                </div>
                <div class="detection-item__actions">
                    <button class="detection-item__accept ${isAccepted ? 'is-active' : ''}" data-index="${index}" title="Accept">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </button>
                    <button class="detection-item__reject ${isRejected ? 'is-active' : ''}" data-index="${index}" title="Reject">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    // ==========================================
    // DETECTION LOGIC
    // ==========================================

    async _runDetection() {
        if (!this.slideId || this.isDetecting) return;

        this.isDetecting = true;
        this._renderLoading();
        eventBus.emit(Events.DETECTION_START, { slideId: this.slideId });

        try {
            this.detectionResult = await apiService.detect(this.slideId, {
                threshold: this.threshold,
                min_area: this.minArea,
                prediction_class: this.predictionClass,
            });

            // Show preview on annotation layer
            const features = this.detectionResult.geojson?.features || [];
            annotationStore.setDetectionPreview(features);

            // All pending by default (not accepted, not rejected)
            this.accepted.clear();
            this.rejected.clear();

            this._renderPreview();
            eventBus.emit(Events.DETECTION_COMPLETE, {
                slideId: this.slideId,
                numRegions: features.length,
            });

        } catch (err) {
            console.error('[DetectionPanel] Detection failed:', err);
            eventBus.emit(Events.DETECTION_ERROR, { error: err.message });
            this._renderError(err.message);
        } finally {
            this.isDetecting = false;
        }
    }

    _toggleAccept(index) {
        if (this.accepted.has(index)) {
            this.accepted.delete(index);
        } else {
            this.rejected.delete(index);
            this.accepted.add(index);
        }
        this._renderPreview();
    }

    _toggleReject(index) {
        if (this.rejected.has(index)) {
            this.rejected.delete(index);
        } else {
            this.accepted.delete(index);
            this.rejected.add(index);
        }
        this._renderPreview();
    }

    async _confirmDetections() {
        if (!this.detectionResult) return;

        const features = this.detectionResult.geojson.features;

        // If nothing explicitly accepted, accept all non-rejected
        let indices;
        if (this.accepted.size > 0) {
            indices = Array.from(this.accepted);
        } else {
            indices = features
                .map((_, i) => i)
                .filter(i => !this.rejected.has(i));
        }

        if (indices.length === 0) return;

        // Store features for confirmation
        const toConfirm = indices.map(i => features[i]);
        annotationStore.setDetectionPreview(toConfirm);

        const result = await annotationStore.confirmDetections(
            toConfirm.map((_, i) => i)
        );

        if (result) {
            this._resetState();
            this._renderIdle();
        }
    }

    _renderError(message) {
        this.element.innerHTML = `
            <div class="detection-panel__section">
                <h4>Auto-Detection</h4>
                <div class="detection-panel__error">
                    <p>Detection failed: ${message}</p>
                    <button class="detection-panel__btn detection-panel__btn--secondary">Retry</button>
                </div>
            </div>
        `;

        this.element.querySelector('.detection-panel__btn--secondary').addEventListener('click', () => {
            this._renderIdle();
        });
    }

    _resetState() {
        this.detectionResult = null;
        this.accepted.clear();
        this.rejected.clear();
        annotationStore.clearDetectionPreview();
    }

    destroy() {
        this._resetState();
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { DetectionPanel };
export default DetectionPanel;
