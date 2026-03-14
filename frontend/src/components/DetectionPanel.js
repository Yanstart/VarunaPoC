/**
 * DetectionPanel - Auto-detection workflow with accept/reject and classification
 *
 * Workflow:
 * 1. User clicks "Auto-Detect"
 * 2. Adjusts threshold slider
 * 3. Loading state while backend runs detection pipeline
 * 4. Preview mode: detected regions shown as dashed outlines
 * 5. User classifies detections via label selector
 * 6. User accepts/rejects individual detections
 * 7. "Confirm All" → batch POST to annotations API (type=auto_confirmed)
 *
 * Counting: Shows confidence distribution and region summary after detection.
 *
 * @module components/DetectionPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { i18nService } from '../services/I18nService.js';
import { userFriendlyMLError } from '../services/mlErrors.js';
import { requestMLWorkerAccess } from '../services/mlWorkerAccess.js';
import { ExportService } from '../services/ExportService.js';

class DetectionPanel {
    /**
     * @param {HTMLElement} container
     * @param {Object} options
     * @param {string} options.slideId
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;
        this._viewerInstance = options.viewerInstance || null;

        // State
        this.analysisScope = 'slide';
        this.isCollapsed = (() => { try { return localStorage.getItem('varuna_panel_detection_open') !== 'true'; } catch (_) { return true; } })();
        this.isDetecting = false;
        this.threshold = 0.5;
        this.minArea = 100;
        this.predictionClass = 'tissue';
        this.detectionResult = null;
        this.measurementResult = null;

        /** @type {Map<number, string>} Feedback status per detection index */
        this.feedbackStatus = new Map();

        /** @type {Set<number>} Indices of hidden detection zones */
        this.hiddenZones = new Set();

        /** @type {string|null} Selected label ID for classification */
        this.selectedLabelId = null;

        /** @type {Set<number>} Indices of accepted detections */
        this.accepted = new Set();
        /** @type {Set<number>} Indices of rejected detections */
        this.rejected = new Set();

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        /** @type {number|null} Currently highlighted detection index */
        this.highlightedIndex = null;

        this.element = null;
        this._create();
        this._setupEventListeners();
    }

    /**
     * Setup event listeners for bidirectional detection linking
     * @private
     */
    _setupEventListeners() {
        // Listen for clicks on detection previews (SVG on slide)
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_PREVIEW_CLICKED, ({ index }) => {
                this._highlightDetectionItem(index);
                this._scrollToDetectionItem(index);
            }),
        );
    }

    setSlide(slideId) {
        this.slideId = slideId;
        this._resetState();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'detection-panel';

        // Create collapsible header
        const header = document.createElement('div');
        header.className = 'detection-panel__header detection-panel__header--collapsible';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'detection-panel__title';
        titleSpan.textContent = 'Détection automatique';

        const chevron = document.createElement('span');
        chevron.className = 'detection-panel__chevron';
        chevron.textContent = '\u25B6';

        header.appendChild(titleSpan);
        header.appendChild(chevron);
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');
        header.setAttribute('aria-expanded', String(!this.isCollapsed));
        header.addEventListener('click', () => this._toggleCollapse());
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this._toggleCollapse();
            }
        });
        this.element.appendChild(header);

        // Create body container
        this._body = document.createElement('div');
        this._body.className = 'detection-panel__body';
        this.element.appendChild(this._body);

        this._renderIdle();
        this.container.appendChild(this.element);

        // Apply initial collapse state (collapsed by default, persisted via localStorage)
        this._body.style.display = this.isCollapsed ? 'none' : 'block';
        if (!this.isCollapsed) {
            chevron.textContent = '\u25BC';
        }
    }

    /**
     * Build label selector HTML from annotationStore.labels
     * @returns {string}
     * @private
     */
    _buildLabelSelector() {
        const labels = annotationStore.labels || [];
        const options = labels.map(l =>
            `<option value="${l.id}" ${this.selectedLabelId === l.id ? 'selected' : ''}>`
            + `${l.name}</option>`,
        ).join('');

        return `
            <div class="detection-panel__control detection-panel__label-select">
                <label>Étiquette de classification</label>
                <select class="detection-panel__select">
                    <option value="">-- Sans étiquette --</option>
                    ${options}
                </select>
            </div>
        `;
    }

    /**
     * Bind label selector change event
     * @private
     */
    _bindLabelSelector() {
        const select = this.element.querySelector('.detection-panel__select');
        if (select) {
            select.addEventListener('change', (e) => {
                this.selectedLabelId = e.target.value || null;
            });
        }
    }

    // ==========================================
    // STATE: IDLE (no detection running)
    // ==========================================

    _renderIdle() {
        this._body.innerHTML = `
            <div class="detection-panel__section">
                <h4>Détection automatique</h4>
                <p class="detection-panel__desc">
                    Détection des régions d'intérêt par analyse IA.
                </p>

                <div class="detection-panel__control">
                    <label>Seuil : <span class="detection-panel__value">${this.threshold}</span></label>
                    <input type="range" class="detection-panel__slider"
                        min="0.1" max="0.95" step="0.05" value="${this.threshold}">
                </div>

                <div class="detection-panel__control">
                    <label>Surface min. : <span class="detection-panel__value">${this.minArea} px</span></label>
                    <input type="range" class="detection-panel__slider"
                        min="10" max="1000" step="10" value="${this.minArea}">
                </div>

                ${this._buildLabelSelector()}

                <div class="detection-panel__scope">
                    <label>Portee</label>
                    <div class="detection-panel__scope-radios">
                        <label class="detection-panel__scope-option">
                            <input type="radio" name="detect-scope" value="slide" ${this.analysisScope === 'slide' ? 'checked' : ''}>
                            Lame entiere
                        </label>
                        <label class="detection-panel__scope-option">
                            <input type="radio" name="detect-scope" value="viewport" ${this.analysisScope === 'viewport' ? 'checked' : ''}>
                            Vue actuelle
                        </label>
                    </div>
                </div>

                <button class="detection-panel__btn detection-panel__btn--primary" ${!this.slideId ? 'disabled' : ''}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    Détecter les régions
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

        this._bindLabelSelector();

        // Scope radios
        this.element.querySelectorAll('input[name="detect-scope"]').forEach((radio) => {
            radio.addEventListener('change', (e) => {
                this.analysisScope = e.target.value;
            });
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
        this._body.innerHTML = `
            <div class="detection-panel__section">
                <h4>Détection automatique</h4>
                <div class="detection-panel__loading">
                    <div class="detection-panel__spinner"></div>
                    <span>Détection en cours...</span>
                </div>
            </div>
        `;
    }

    // ==========================================
    // STATE: PREVIEW (results ready)
    // ==========================================

    _renderPreview() {
        if (!this.detectionResult) {return;}

        const features = this.detectionResult.geojson.features;
        const total = features.length;
        const acceptedCount = this.accepted.size;
        const rejectedCount = this.rejected.size;
        const pendingCount = total - acceptedCount - rejectedCount;

        // Confidence distribution
        const confDist = this._computeConfidenceDistribution(features);

        this._body.innerHTML = `
            <div class="detection-panel__section">
                <h4>Résultats de détection</h4>

                <div class="detection-panel__count-summary">
                    <div class="count-summary__total">
                        <span class="count-summary__number">${total}</span>
                        <span class="count-summary__label">régions détectées</span>
                    </div>
                    <div class="count-summary__breakdown">
                        <div class="count-summary__bar">
                            <div class="count-summary__segment count-summary__segment--high"
                                 style="width: ${total ? (confDist.high / total * 100) : 0}%"
                                 title="Confiance \u00e9lev\u00e9e (\u22650.8) : ${confDist.high}"></div>
                            <div class="count-summary__segment count-summary__segment--medium"
                                 style="width: ${total ? (confDist.medium / total * 100) : 0}%"
                                 title="Confiance moyenne (0.5-0.8) : ${confDist.medium}"></div>
                            <div class="count-summary__segment count-summary__segment--low"
                                 style="width: ${total ? (confDist.low / total * 100) : 0}%"
                                 title="Confiance faible (<0.5) : ${confDist.low}"></div>
                        </div>
                        <div class="count-summary__legend">
                            <span class="count-summary__legend-item count-summary__legend-item--high">${confDist.high} élevée</span>
                            <span class="count-summary__legend-item count-summary__legend-item--medium">${confDist.medium} moyenne</span>
                            <span class="count-summary__legend-item count-summary__legend-item--low">${confDist.low} faible</span>
                        </div>
                    </div>
                </div>

                <div class="detection-panel__stats">
                    <span class="stat stat--total">${pendingCount} en attente</span>
                    <span class="stat stat--accepted">${acceptedCount} acceptée</span>
                    <span class="stat stat--rejected">${rejectedCount} rejetée</span>
                </div>

                ${this._buildLabelSelector()}

                <div class="detection-panel__results">
                    ${features.map((f, i) => this._renderDetectionItem(f, i)).join('')}
                </div>

                <div class="detection-panel__actions">
                    <button class="detection-panel__btn detection-panel__btn--confirm"
                        ${acceptedCount === 0 && pendingCount === 0 ? 'disabled' : ''}>
                        Tout confirmer ${acceptedCount > 0 ? acceptedCount : ''}
                    </button>
                    <button class="detection-panel__btn detection-panel__btn--secondary">
                        Tout accepter
                    </button>
                    <button class="detection-panel__btn detection-panel__btn--danger">
                        Tout rejeter
                    </button>
                    <button class="detection-panel__btn detection-panel__btn--export">
                        ${i18nService.t('export.csv')}
                    </button>
                </div>
            </div>
        `;

        this._bindLabelSelector();

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

        // Per-zone visibility toggle
        this.element.querySelectorAll('.detection-item__visibility').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(btn.dataset.visibilityIndex);
                this._toggleZoneVisibility(idx);
            });
        });

        // Detection item click for bidirectional linking
        this.element.querySelectorAll('.detection-item').forEach((item) => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on action buttons
                if (e.target.closest('.detection-item__actions') || e.target.closest('.detection-item__feedback')) {
                    return;
                }
                const idx = parseInt(item.dataset.detectionItemIndex);
                if (!isNaN(idx)) {
                    this._highlightDetectionItem(idx);
                    eventBus.emit(Events.DETECTION_ITEM_CLICKED, { index: idx });
                }
            });
        });

        // Hover highlight on detection items
        const resultsContainer = this.element.querySelector('.detection-panel__results');
        if (!this._hoverListenersAdded && resultsContainer) {
            this._hoverListenersAdded = true;
            resultsContainer.addEventListener('mouseenter', (e) => {
                const item = e.target.closest('[data-detection-item-index]');
                if (item) {
                    const idx = parseInt(item.dataset.detectionItemIndex, 10);
                    eventBus.emit(Events.DETECTION_HIGHLIGHT, { regionIndex: idx });
                }
            }, true);

            resultsContainer.addEventListener('mouseleave', (e) => {
                const item = e.target.closest('[data-detection-item-index]');
                if (item) {
                    eventBus.emit(Events.DETECTION_HIGHLIGHT, { regionIndex: null });
                }
            }, true);
        }

        // Feedback buttons (confirm/reject ML prediction)
        this.element.querySelectorAll('.feedback-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.feedbackIndex);
                const type = btn.dataset.feedbackType;
                this._submitFeedback(idx, type);
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

        this.element.querySelector('.detection-panel__btn--export').addEventListener('click', () => {
            this._exportCSV();
        });
    }

    /**
     * Compute confidence distribution from features
     * @param {Array} features
     * @returns {{high: number, medium: number, low: number}}
     * @private
     */
    _computeConfidenceDistribution(features) {
        let high = 0, medium = 0, low = 0;
        for (const f of features) {
            const conf = f.properties?.confidence || 0;
            if (conf >= 0.8) {high++;} else if (conf >= 0.5) {medium++;} else {low++;}
        }
        return { high, medium, low };
    }

    /**
     * Create a confidence badge element
     * @param {number|null|undefined} confidence - Confidence value (0-1)
     * @returns {string} HTML string for the badge
     * @private
     */
    _getConfidenceBadge(confidence) {
        if (confidence === null || confidence === undefined) {
            return '<span class="detection-badge detection-badge--unknown" title="Confiance inconnue">?</span>';
        }
        if (confidence >= 0.8) {
            return `<span class="detection-badge detection-badge--high" title="Confiance élevée">${Math.round(confidence * 100)}%</span>`;
        }
        if (confidence >= 0.5) {
            return `<span class="detection-badge detection-badge--medium" title="Confiance moyenne">${Math.round(confidence * 100)}%</span>`;
        }
        return `<span class="detection-badge detection-badge--low" title="Confiance faible">${Math.round(confidence * 100)}%</span>`;
    }

    _renderDetectionItem(feature, index) {
        const confidence = (feature.properties?.confidence || 0).toFixed(2);
        const area = Math.round(feature.properties?.area_px || 0);
        const isAccepted = this.accepted.has(index);
        const isRejected = this.rejected.has(index);
        const isHighlighted = this.highlightedIndex === index;
        const isHidden = this.hiddenZones.has(index);
        const confLevel = feature.properties?.confidence >= 0.8 ? 'high'
            : feature.properties?.confidence >= 0.5 ? 'medium' : 'low';

        const measurement = this.measurementResult?.measurements?.[index];
        const dimensionHtml = measurement
            ? `<span class="detection-item__dimension">${measurement.feret_diameter_mm} mm</span>`
            : '';

        return `
            <div class="detection-item ${isAccepted ? 'is-accepted' : ''} ${isRejected ? 'is-rejected' : ''} ${isHighlighted ? 'is-highlighted' : ''} ${isHidden ? 'is-hidden-zone' : ''}"
                 data-detection-item-index="${index}">
                <div class="detection-item__info">
                    <span class="detection-item__label">R\u00e9gion ${index + 1}${this._getConfidenceBadge(feature.properties?.confidence)}${dimensionHtml}</span>
                    <span class="detection-item__meta">
                        <span class="detection-item__conf detection-item__conf--${confLevel}">${confidence}</span>
                         | ${area} px
                    </span>
                </div>
                <div class="detection-item__actions">
                    <button class="detection-item__visibility ${isHidden ? 'is-hidden' : ''}" data-visibility-index="${index}" title="${isHidden ? 'Afficher' : 'Masquer'}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            ${isHidden
        ? '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>'
        : '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'}
                        </svg>
                    </button>
                    <button class="detection-item__accept ${isAccepted ? 'is-active' : ''}" data-index="${index}" title="Accepter">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </button>
                    <button class="detection-item__reject ${isRejected ? 'is-active' : ''}" data-index="${index}" title="Rejeter">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="detection-item__feedback">
                    ${this.feedbackStatus.has(index)
        ? `<span class="feedback-badge feedback-badge--${this.feedbackStatus.get(index)}">${
            this.feedbackStatus.get(index) === 'confirmed' ? '\u2714 Confirm\u00e9'
                : this.feedbackStatus.get(index) === 'rejected' ? '\u2718 Rejet\u00e9'
                    : '\u270E Corrig\u00e9'
        }</span>`
        : `<button class="feedback-btn feedback-btn--confirm" data-feedback-index="${index}" data-feedback-type="confirmed" title="Confirmer la pr\u00e9diction IA">Confirmer</button>
           <button class="feedback-btn feedback-btn--correct" data-feedback-index="${index}" data-feedback-type="refined" title="Corriger / re-\u00e9tiqueter">Corriger</button>
           <button class="feedback-btn feedback-btn--reject" data-feedback-index="${index}" data-feedback-type="rejected" title="Rejeter la pr\u00e9diction IA">Rejeter</button>`}
                </div>
            </div>
        `;
    }

    // ==========================================
    // DETECTION LOGIC
    // ==========================================

    async _runDetection() {
        if (!this.slideId || this.isDetecting) {return;}

        const canProceed = await requestMLWorkerAccess('D\u00e9tection automatique');
        if (!canProceed) return;

        this.isDetecting = true;
        this._renderLoading();
        eventBus.emit(Events.ML_WORKER_BUSY, { panel: 'detection', label: 'D\u00e9tection automatique' });
        eventBus.emit(Events.DETECTION_START, { slideId: this.slideId });

        try {
            const detectParams = {
                threshold: this.threshold,
                min_area: this.minArea,
                prediction_class: this.predictionClass,
            };

            if (this.analysisScope === 'viewport' && this._viewerInstance) {
                const bounds = this._viewerInstance.getViewportPixelBounds();
                if (bounds) {
                    detectParams.region = `${bounds.x},${bounds.y},${bounds.width},${bounds.height}`;
                }
            }

            this.detectionResult = await apiService.detect(this.slideId, detectParams);

            // Show preview on annotation layer
            const features = this.detectionResult.geojson?.features || [];
            annotationStore.setDetectionPreview(features);

            // All pending by default (not accepted, not rejected)
            this.accepted.clear();
            this.rejected.clear();

            // Fetch measurements for dimension display
            try {
                this.measurementResult = await apiService.getMeasurement(this.slideId, {
                    threshold: this.threshold,
                });
            } catch (e) {
                console.warn('[DetectionPanel] Measurement fetch failed:', e);
                this.measurementResult = null;
            }

            this._renderPreview();
            eventBus.emit(Events.DETECTION_COMPLETE, {
                slideId: this.slideId,
                numRegions: features.length,
            });

        } catch (err) {
            console.error('[DetectionPanel] Detection failed:', err);
            eventBus.emit(Events.DETECTION_ERROR, { error: err.message });
            this._renderError(userFriendlyMLError(err));
        } finally {
            this.isDetecting = false;
            eventBus.emit(Events.ML_WORKER_FREE);
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
        if (!this.detectionResult) {return;}

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

        if (indices.length === 0) {return;}

        // Store features for confirmation with selected label
        const toConfirm = indices.map(i => features[i]);
        annotationStore.setDetectionPreview(toConfirm);

        const result = await annotationStore.confirmDetections(
            toConfirm.map((_, i) => i),
            this.selectedLabelId,
        );

        if (result) {
            this._resetState();
            this._renderIdle();
        }
    }

    _renderError(message) {
        this._body.textContent = '';
        const section = document.createElement('div');
        section.className = 'detection-panel__section';

        const h4 = document.createElement('h4');
        h4.textContent = 'Détection automatique';
        section.appendChild(h4);

        const wrapper = document.createElement('div');
        wrapper.className = 'detection-panel__error';

        const p = document.createElement('p');
        p.textContent = `Erreur lors de la détection : ${message}`;

        const retryBtn = document.createElement('button');
        retryBtn.className = 'detection-panel__btn detection-panel__btn--secondary';
        retryBtn.textContent = 'Réessayer';
        retryBtn.addEventListener('click', () => this._renderIdle());

        wrapper.appendChild(p);
        wrapper.appendChild(retryBtn);
        section.appendChild(wrapper);
        this._body.appendChild(section);
    }

    /**
     * Submit pathologist feedback for a detection
     * @param {number} index - Detection index
     * @param {string} correctionType - 'confirmed', 'rejected', or 'refined'
     * @private
     */
    async _submitFeedback(index, correctionType) {
        if (!this.detectionResult || this.feedbackStatus.has(index)) {
            return;
        }

        const features = this.detectionResult.geojson?.features || [];
        const feature = features[index];
        if (!feature) {
            return;
        }

        const annotationId = feature.properties?.annotation_id || feature.properties?.id;
        if (!annotationId) {
            console.warn('[DetectionPanel] No annotation ID for feedback at index', index);
            // Still mark locally for UX
            this.feedbackStatus.set(index, correctionType);
            this._renderPreview();
            return;
        }

        try {
            await apiService.submitFeedback(this.slideId, {
                original_annotation_id: annotationId,
                correction_type: correctionType,
                notes: null,
            });
            this.feedbackStatus.set(index, correctionType);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: correctionType === 'confirmed' ? i18nService.t('detection.feedbackConfirmed')
                    : correctionType === 'rejected' ? i18nService.t('detection.feedbackRejected')
                        : i18nService.t('detection.correctionSaved'),
                duration: 2000,
            });
        } catch (e) {
            console.warn('[DetectionPanel] Feedback submission failed:', e);
            // Mark locally anyway for UX feedback
            this.feedbackStatus.set(index, correctionType);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: i18nService.t('detection.feedbackError'),
                duration: 3000,
            });
        }

        this._renderPreview();
    }

    /**
     * Highlight a detection item in the panel
     * @param {number} index - Detection index
     * @private
     */
    _highlightDetectionItem(index) {
        // Remove previous highlight
        const prev = this.element.querySelector('.detection-item.is-highlighted');
        if (prev) {
            prev.classList.remove('is-highlighted');
        }

        this.highlightedIndex = index;

        // Apply highlight
        const item = this.element.querySelector(`[data-detection-item-index="${index}"]`);
        if (item) {
            item.classList.add('is-highlighted');
        }
    }

    /**
     * Scroll to a detection item in the panel results list
     * @param {number} index - Detection index
     * @private
     */
    _scrollToDetectionItem(index) {
        const item = this.element.querySelector(`[data-detection-item-index="${index}"]`);
        if (item) {
            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    _exportCSV() {
        if (!this.detectionResult?.geojson?.features) return;

        const headers = ['region', 'confidence', 'area_px', 'centroid_x', 'centroid_y', 'label'];
        const rows = this.detectionResult.geojson.features.map((f, i) => [
            `detection_${i}`,
            f.properties.confidence,
            f.properties.area_px,
            f.properties.centroid?.[0] ?? '',
            f.properties.centroid?.[1] ?? '',
            this.selectedLabelId || '',
        ]);

        const csv = ExportService.toCSV(headers, rows);
        const slideName = this.slideId || 'slide';
        ExportService.download(csv, `${slideName}_detection_${ExportService.dateStamp()}.csv`);
    }

    /**
     * Toggle visibility of a single detection zone on the overlay.
     * @param {number} index - Detection zone index
     * @private
     */
    _toggleZoneVisibility(index) {
        const nowHidden = !this.hiddenZones.has(index);
        if (nowHidden) {
            this.hiddenZones.add(index);
        } else {
            this.hiddenZones.delete(index);
        }
        eventBus.emit(Events.DETECTION_HIGHLIGHT, {
            regionIndex: index,
            visible: !nowHidden,
        });
        this._renderPreview();
    }

    _resetState() {
        this.detectionResult = null;
        this.measurementResult = null;
        this.feedbackStatus = new Map();
        this.accepted.clear();
        this.rejected.clear();
        this.hiddenZones.clear();
        this.highlightedIndex = null;
        this._hoverListenersAdded = false;
        annotationStore.clearDetectionPreview();
    }

    /**
     * Toggle collapse state of the panel
     * @private
     */
    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const body = this.element.querySelector('.detection-panel__body');
        const chevron = this.element.querySelector('.detection-panel__chevron');
        const header = this.element.querySelector('.detection-panel__header');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
        try { localStorage.setItem('varuna_panel_detection_open', String(!this.isCollapsed)); } catch (_) { /* noop */ }
    }

    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
        this._resetState();
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { DetectionPanel };
export default DetectionPanel;
