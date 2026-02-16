/**
 * MLPanel - Machine Learning Controls and Results Display
 *
 * Provides UI for:
 * - Running ML predictions on slides
 * - Displaying prediction results with confidence/uncertainty
 * - Toggling heatmap overlay
 * - Adjusting heatmap opacity
 *
 * @module components/MLPanel
 */

import { apiService } from '../services/ApiService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

/**
 * MLPanel component
 */
class MLPanel {
    /**
     * Create MLPanel
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Configuration options
     * @param {string} options.viewerId - Associated viewer ID
     */
    constructor(container, options = {}) {
        this.container = container;
        this.viewerId = options.viewerId || null;
        this.slideId = null;

        // State
        this.prediction = null;
        this.heatmapVisible = false;
        this.heatmapOpacity = 0.5;
        this.isLoading = false;
        this.isCollapsed = true;

        // Elements
        this.element = null;
        this.predictBtn = null;
        this.heatmapBtn = null;
        this.opacitySlider = null;
        this.resultsContainer = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this._build();
        this._setupEventListeners();
    }

    /**
     * Build the panel DOM
     * @private
     */
    _build() {
        this.element = document.createElement('div');
        this.element.className = 'ml-panel';
        this.element.innerHTML = `
            <div class="ml-panel__header ml-panel__header--collapsible">
                <span class="ml-panel__title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                    Analyse IA
                </span>
                <span class="ml-panel__chevron">\u25B6</span>
            </div>
            <div class="ml-panel__content">
                <div class="ml-panel__actions">
                    <button class="ml-panel__btn ml-panel__btn--predict" disabled>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 16v-4"/>
                            <path d="M12 8h.01"/>
                        </svg>
                        Analyser la lame
                    </button>
                    <button class="ml-panel__btn ml-panel__btn--heatmap" disabled>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2"/>
                            <path d="M3 9h18"/>
                            <path d="M3 15h18"/>
                            <path d="M9 3v18"/>
                            <path d="M15 3v18"/>
                        </svg>
                        Afficher la carte de chaleur
                    </button>
                </div>
                <div class="ml-panel__opacity" style="display: none;">
                    <label>Opacité de la carte</label>
                    <input type="range" min="0" max="100" value="50" class="ml-panel__slider">
                    <span class="ml-panel__opacity-value">50%</span>
                </div>
                <div class="ml-panel__results">
                    <div class="ml-panel__placeholder">
                        Chargez une lame et cliquez « Analyser » pour lancer la prédiction IA
                    </div>
                </div>
            </div>
        `;

        // Get references
        this.predictBtn = this.element.querySelector('.ml-panel__btn--predict');
        this.heatmapBtn = this.element.querySelector('.ml-panel__btn--heatmap');
        this.opacitySlider = this.element.querySelector('.ml-panel__slider');
        this.opacityContainer = this.element.querySelector('.ml-panel__opacity');
        this.opacityValue = this.element.querySelector('.ml-panel__opacity-value');
        this.resultsContainer = this.element.querySelector('.ml-panel__results');
        this.content = this.element.querySelector('.ml-panel__content');

        // Make header clickable for accordion
        const header = this.element.querySelector('.ml-panel__header');
        if (header) {
            header.addEventListener('click', () => this._toggleCollapse());
        }

        this.container.appendChild(this.element);

        // Start collapsed by default
        const body = this.element.querySelector('.ml-panel__content');
        if (body) body.style.display = 'none';
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Predict button
        this.predictBtn.addEventListener('click', () => this._runPrediction());

        // Heatmap toggle
        this.heatmapBtn.addEventListener('click', () => this._toggleHeatmap());

        // Opacity slider
        this.opacitySlider.addEventListener('input', (e) => {
            this.heatmapOpacity = e.target.value / 100;
            this.opacityValue.textContent = `${e.target.value}%`;
            eventBus.emit(Events.ML_HEATMAP_OPACITY_CHANGE, {
                viewerId: this.viewerId,
                opacity: this.heatmapOpacity,
            });
        });

        // Listen for slide loaded events - Store unsubscribe functions
        this._unsubscribers.push(
            eventBus.on(Events.SLIDE_LOADED, (data) => {
                if (data.viewerId === this.viewerId) {
                    this.setSlide(data.slideId);
                }
            }),
        );

        // Listen for slide unloaded
        this._unsubscribers.push(
            eventBus.on(Events.SLIDE_UNLOADED, (data) => {
                if (data.viewerId === this.viewerId) {
                    this.reset();
                }
            }),
        );
    }

    /**
     * Set the current slide
     * @param {string} slideId - Slide ID
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this.prediction = null;
        this.heatmapVisible = false;

        // Enable predict button
        this.predictBtn.disabled = false;
        this.heatmapBtn.disabled = true;
        this.heatmapBtn.classList.remove('is-active');
        this.opacityContainer.style.display = 'none';

        // Reset results
        this.resultsContainer.innerHTML = `
            <div class="ml-panel__placeholder">
                Cliquez « Analyser la lame » pour lancer la prédiction IA
            </div>
        `;
    }

    /**
     * Reset panel state
     */
    reset() {
        this.slideId = null;
        this.prediction = null;
        this.heatmapVisible = false;

        this.predictBtn.disabled = true;
        this.heatmapBtn.disabled = true;
        this.heatmapBtn.classList.remove('is-active');
        this.opacityContainer.style.display = 'none';

        this.resultsContainer.innerHTML = `
            <div class="ml-panel__placeholder">
                Chargez une lame et cliquez « Analyser » pour lancer la prédiction IA
            </div>
        `;
    }

    /**
     * Run ML prediction
     * @private
     */
    async _runPrediction() {
        if (!this.slideId || this.isLoading) {return;}

        this.isLoading = true;
        this.predictBtn.disabled = true;
        this.predictBtn.innerHTML = `
            <span class="ml-panel__spinner"></span>
            Analyse en cours...
        `;

        // Show loading in results
        this.resultsContainer.innerHTML = `
            <div class="ml-panel__loading">
                <span class="ml-panel__spinner ml-panel__spinner--large"></span>
                <p>Analyse IA en cours...</p>
                <p class="ml-panel__loading-sub">Cela peut prendre quelques secondes</p>
            </div>
        `;

        eventBus.emit(Events.ML_PREDICTION_START, {
            viewerId: this.viewerId,
            slideId: this.slideId,
        });

        try {
            const result = await apiService.predict(this.slideId, {
                numMcSamples: 10,
            });

            this.prediction = result;
            this._displayResults(result);

            // Enable heatmap button
            this.heatmapBtn.disabled = false;

            eventBus.emit(Events.ML_PREDICTION_COMPLETE, {
                viewerId: this.viewerId,
                slideId: this.slideId,
                prediction: result,
            });

        } catch (error) {
            console.error('ML Prediction error:', error);
            this._displayError(error.message || 'Prediction failed');

            eventBus.emit(Events.ML_PREDICTION_ERROR, {
                viewerId: this.viewerId,
                slideId: this.slideId,
                error: error.message,
            });
        } finally {
            this.isLoading = false;
            this.predictBtn.disabled = false;
            this.predictBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 16v-4"/>
                    <path d="M12 8h.01"/>
                </svg>
                Analyser la lame
            `;
        }
    }

    /**
     * Display prediction results
     * @param {Object} result - Prediction result
     * @private
     */
    _displayResults(result) {
        const confidence = (result.confidence * 100).toFixed(1);
        const uncertainty = result.uncertainty ? (result.uncertainty * 100).toFixed(1) : null;

        // Get confidence color
        const confColor = this._getConfidenceColor(result.confidence);

        // Build probabilities bars
        const probBars = Object.entries(result.probabilities || {})
            .sort((a, b) => b[1] - a[1])
            .map(([cls, prob]) => {
                const pct = (prob * 100).toFixed(1);
                const isMain = cls === result.prediction_class;
                return `
                    <div class="ml-panel__prob-row ${isMain ? 'is-main' : ''}">
                        <span class="ml-panel__prob-label">${cls}</span>
                        <div class="ml-panel__prob-bar">
                            <div class="ml-panel__prob-fill" style="width: ${pct}%"></div>
                        </div>
                        <span class="ml-panel__prob-value">${pct}%</span>
                    </div>
                `;
            })
            .join('');

        this.resultsContainer.innerHTML = `
            <div class="ml-panel__result">
                <div class="ml-panel__prediction">
                    <span class="ml-panel__prediction-label">Prédiction</span>
                    <span class="ml-panel__prediction-class">${result.prediction_class}</span>
                </div>
                <div class="ml-panel__metrics">
                    <div class="ml-panel__metric">
                        <span class="ml-panel__metric-label">Confiance</span>
                        <span class="ml-panel__metric-value" style="color: ${confColor}">
                            ${confidence}%
                        </span>
                    </div>
                    ${uncertainty !== null ? `
                        <div class="ml-panel__metric">
                            <span class="ml-panel__metric-label">Uncertainty</span>
                            <span class="ml-panel__metric-value ml-panel__metric-value--uncertainty">
                                ±${uncertainty}%
                            </span>
                        </div>
                    ` : ''}
                    <div class="ml-panel__metric">
                        <span class="ml-panel__metric-label">Time</span>
                        <span class="ml-panel__metric-value">
                            ${result.execution_time_ms?.toFixed(0) || '?'}ms
                        </span>
                    </div>
                </div>
                <div class="ml-panel__probabilities">
                    <span class="ml-panel__prob-title">Probabilités par classe</span>
                    ${probBars}
                </div>
            </div>
        `;
    }

    /**
     * Display error message
     * @param {string} message - Error message
     * @private
     */
    _displayError(message) {
        this.resultsContainer.innerHTML = `
            <div class="ml-panel__error">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <p>Analysis failed</p>
                <p class="ml-panel__error-detail">${message}</p>
            </div>
        `;
    }

    /**
     * Get color based on confidence level
     * @param {number} confidence - Confidence value (0-1)
     * @returns {string} CSS color
     * @private
     */
    _getConfidenceColor(confidence) {
        if (confidence >= 0.9) {return 'var(--color-success)';}
        if (confidence >= 0.7) {return 'var(--color-warning)';}
        return 'var(--color-error)';
    }

    /**
     * Toggle heatmap visibility
     * @private
     */
    async _toggleHeatmap() {
        if (!this.prediction) {return;}

        this.heatmapVisible = !this.heatmapVisible;
        this.heatmapBtn.classList.toggle('is-active', this.heatmapVisible);

        if (this.heatmapVisible) {
            this.opacityContainer.style.display = 'flex';
            this.heatmapBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M3 9h18"/>
                    <path d="M3 15h18"/>
                    <path d="M9 3v18"/>
                    <path d="M15 3v18"/>
                </svg>
                Masquer la carte de chaleur
            `;
        } else {
            this.opacityContainer.style.display = 'none';
            this.heatmapBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M3 9h18"/>
                    <path d="M3 15h18"/>
                    <path d="M9 3v18"/>
                    <path d="M15 3v18"/>
                </svg>
                Afficher la carte de chaleur
            `;
        }

        eventBus.emit(Events.ML_HEATMAP_TOGGLE, {
            viewerId: this.viewerId,
            slideId: this.slideId,
            visible: this.heatmapVisible,
            predictionClass: this.prediction.prediction_class,
            opacity: this.heatmapOpacity,
        });
    }

    /**
     * Toggle collapse state of the panel
     * @private
     */
    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const body = this.element.querySelector('.ml-panel__content');
        const chevron = this.element.querySelector('.ml-panel__chevron');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
    }

    /**
     * Destroy the panel
     */
    destroy() {
        // Properly unsubscribe from all event listeners
        this._unsubscribers.forEach(unsubscribe => unsubscribe());
        this._unsubscribers = [];

        if (this.element) {
            this.element.remove();
        }
    }
}

export { MLPanel };
export default MLPanel;
