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
import { userFriendlyMLError } from '../services/mlErrors.js';
import { requestMLWorkerAccess } from '../services/mlWorkerAccess.js';
import { i18nService } from '../services/I18nService.js';

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
        this._viewerInstance = options.viewerInstance || null;
        this.slideId = null;

        // State
        this.analysisScope = 'slide';
        this.selectedModelId = null;
        this.prediction = null;
        this.heatmapVisible = false;
        this.heatmapOpacity = 0.5;
        this.isLoading = false;
        this.isCollapsed = (() => { try { return localStorage.getItem('varuna_panel_ml_open') !== 'true'; } catch (_) { return true; } })();
        this._qualityScore = null;

        // Elements
        this.element = null;
        this.modelSelect = null;
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
        const _t = (k, p) => i18nService.t(k, p);

        // Build panel structure with DOM API for safety
        // Header (collapsible)
        const header = document.createElement('div');
        header.className = 'ml-panel__header ml-panel__header--collapsible';
        const titleSpan = document.createElement('span');
        titleSpan.className = 'ml-panel__title';
        // SVG icon for header - static constant, not user input
        titleSpan.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>';
        titleSpan.appendChild(document.createTextNode(' ' + _t('panel.ml')));
        header.appendChild(titleSpan);
        const chevron = document.createElement('span');
        chevron.className = 'ml-panel__chevron';
        chevron.textContent = '\u25B6';
        header.appendChild(chevron);
        this.element.appendChild(header);

        // Content wrapper
        const content = document.createElement('div');
        content.className = 'ml-panel__content';

        // Model selector
        const modelDiv = document.createElement('div');
        modelDiv.className = 'ml-panel__model-selector';
        const modelLabel = document.createElement('label');
        modelLabel.className = 'ml-panel__model-label';
        modelLabel.textContent = _t('ml.model');
        modelDiv.appendChild(modelLabel);
        const modelSelect = document.createElement('select');
        modelSelect.className = 'ml-panel__model-select';
        modelSelect.disabled = true;
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = _t('ml.loading');
        modelSelect.appendChild(defaultOpt);
        modelDiv.appendChild(modelSelect);
        content.appendChild(modelDiv);

        // Scope
        const scopeDiv = document.createElement('div');
        scopeDiv.className = 'ml-panel__scope';
        const scopeLabel = document.createElement('label');
        scopeLabel.className = 'ml-panel__scope-label';
        scopeLabel.textContent = _t('ml.scope');
        scopeDiv.appendChild(scopeLabel);
        const scopeRadios = document.createElement('div');
        scopeRadios.className = 'ml-panel__scope-radios';
        const slideOption = document.createElement('label');
        slideOption.className = 'ml-panel__scope-option';
        const slideRadio = document.createElement('input');
        slideRadio.type = 'radio'; slideRadio.name = 'ml-scope'; slideRadio.value = 'slide'; slideRadio.checked = true;
        slideOption.appendChild(slideRadio);
        slideOption.appendChild(document.createTextNode(' ' + _t('ml.scopeSlide')));
        const vpOption = document.createElement('label');
        vpOption.className = 'ml-panel__scope-option';
        const vpRadio = document.createElement('input');
        vpRadio.type = 'radio'; vpRadio.name = 'ml-scope'; vpRadio.value = 'viewport';
        vpOption.appendChild(vpRadio);
        vpOption.appendChild(document.createTextNode(' ' + _t('ml.scopeViewport')));
        scopeRadios.appendChild(slideOption);
        scopeRadios.appendChild(vpOption);
        scopeDiv.appendChild(scopeRadios);
        content.appendChild(scopeDiv);

        // GPU toggle
        const deviceDiv = document.createElement('div');
        deviceDiv.className = 'ml-panel__device';
        const deviceLabel = document.createElement('label');
        deviceLabel.className = 'ml-panel__device-label';
        deviceLabel.textContent = _t('ml.device') || 'Device';
        deviceDiv.appendChild(deviceLabel);
        const deviceSelect = document.createElement('select');
        deviceSelect.className = 'ml-panel__device-select';
        for (const [val, label] of [['auto', 'Auto'], ['cuda', 'GPU (CUDA)'], ['cpu', 'CPU']]) {
            const opt = document.createElement('option');
            opt.value = val; opt.textContent = label;
            deviceSelect.appendChild(opt);
        }
        deviceDiv.appendChild(deviceSelect);
        this._deviceStatus = document.createElement('span');
        this._deviceStatus.className = 'ml-panel__device-status';
        deviceDiv.appendChild(this._deviceStatus);
        content.appendChild(deviceDiv);
        this._deviceSelect = deviceSelect;
        this._fetchDeviceStatus();
        deviceSelect.addEventListener('change', () => this._switchDevice(deviceSelect.value));

        // Actions
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'ml-panel__actions';
        const predictBtn = document.createElement('button');
        predictBtn.className = 'ml-panel__btn ml-panel__btn--predict';
        predictBtn.disabled = true;
        // Static SVG icon - not user input
        predictBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';
        predictBtn.appendChild(document.createTextNode(' ' + _t('ml.analyze')));
        actionsDiv.appendChild(predictBtn);
        const heatmapBtn = document.createElement('button');
        heatmapBtn.className = 'ml-panel__btn ml-panel__btn--heatmap';
        heatmapBtn.disabled = true;
        // Static SVG icon - not user input
        heatmapBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>';
        heatmapBtn.appendChild(document.createTextNode(' ' + _t('ml.showHeatmap')));
        actionsDiv.appendChild(heatmapBtn);
        content.appendChild(actionsDiv);

        // Opacity
        const opacityDiv = document.createElement('div');
        opacityDiv.className = 'ml-panel__opacity';
        opacityDiv.style.display = 'none';
        const opacityLabel = document.createElement('label');
        opacityLabel.textContent = _t('ml.heatmapOpacity');
        opacityDiv.appendChild(opacityLabel);
        const slider = document.createElement('input');
        slider.type = 'range'; slider.min = '0'; slider.max = '100'; slider.value = '50';
        slider.className = 'ml-panel__slider';
        opacityDiv.appendChild(slider);
        const opacityValue = document.createElement('span');
        opacityValue.className = 'ml-panel__opacity-value';
        opacityValue.textContent = '50%';
        opacityDiv.appendChild(opacityValue);
        content.appendChild(opacityDiv);

        // Results
        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'ml-panel__results';
        const placeholder = document.createElement('div');
        placeholder.className = 'ml-panel__placeholder';
        placeholder.textContent = _t('ml.loadAndAnalyze');
        resultsDiv.appendChild(placeholder);
        content.appendChild(resultsDiv);

        this.element.appendChild(content);

        // Get references
        this.predictBtn = this.element.querySelector('.ml-panel__btn--predict');
        this.heatmapBtn = this.element.querySelector('.ml-panel__btn--heatmap');
        this.opacitySlider = this.element.querySelector('.ml-panel__slider');
        this.opacityContainer = this.element.querySelector('.ml-panel__opacity');
        this.opacityValue = this.element.querySelector('.ml-panel__opacity-value');
        this.resultsContainer = this.element.querySelector('.ml-panel__results');
        this.content = this.element.querySelector('.ml-panel__content');
        this.modelSelect = this.element.querySelector('.ml-panel__model-select');

        // Make header clickable for accordion
        const panelHeader = this.element.querySelector('.ml-panel__header');
        if (panelHeader) {
            panelHeader.setAttribute('role', 'button');
            panelHeader.setAttribute('tabindex', '0');
            panelHeader.setAttribute('aria-expanded', String(!this.isCollapsed));
            panelHeader.addEventListener('click', () => this._toggleCollapse());
            panelHeader.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this._toggleCollapse();
                }
            });
        }

        this._loadModels();

        this.container.appendChild(this.element);

        // Apply initial collapse state (collapsed by default, persisted via localStorage)
        const body = this.element.querySelector('.ml-panel__content');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        const chevronEl = this.element.querySelector('.ml-panel__chevron');
        if (chevronEl) {
            chevronEl.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
    }

    /**
     * Setup event listeners
     * @private
     */
    _setupEventListeners() {
        // Scope radios
        this.element.querySelectorAll('input[name="ml-scope"]').forEach((radio) => {
            radio.addEventListener('change', (e) => {
                this.analysisScope = e.target.value;
            });
        });

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

        // Listen for heatmap errors to reset toggle state
        this._unsubscribers.push(
            eventBus.on(Events.ML_HEATMAP_ERROR, (data) => {
                if (data.viewerId === this.viewerId) {
                    this.heatmapVisible = false;
                    this.heatmapBtn.classList.remove('is-active');
                    this.opacityContainer.style.display = 'none';
                    this._displayError(data.error || 'Heatmap generation failed');
                }
            }),
        );

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

        // Listen for quality score to show cross-validation warning
        this._unsubscribers.push(
            eventBus.on(Events.QUALITY_READY, ({ slideId, metrics, data }) => {
                if (slideId === this.slideId) {
                    const m = metrics || data || {};
                    this._qualityScore = m.overall_score ?? m.score ?? null;
                    this._updateQualityWarning();
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
        this._qualityScore = null;
        const existing = this.element.querySelector('.ml-panel__quality-warning');
        if (existing) existing.remove();

        // Enable predict button
        this.predictBtn.disabled = false;
        this.heatmapBtn.disabled = true;
        this.heatmapBtn.classList.remove('is-active');
        this.opacityContainer.style.display = 'none';

        // Reset results
        this.resultsContainer.textContent = '';
        const hint = document.createElement('div');
        hint.className = 'ml-panel__placeholder';
        hint.textContent = i18nService.t('ml.analyzeHint');
        this.resultsContainer.appendChild(hint);
    }

    /**
     * Show or hide quality warning banner based on quality score
     * @private
     */
    _updateQualityWarning() {
        const existing = this.element.querySelector('.ml-panel__quality-warning');
        if (existing) existing.remove();

        if (this._qualityScore !== null && this._qualityScore < 0.6) {
            const warning = document.createElement('div');
            warning.className = 'ml-panel__quality-warning';
            warning.textContent = i18nService.t('ml.qualityWarning', {
                score: (this._qualityScore * 100).toFixed(0),
            });
            const content = this.element.querySelector('.ml-panel__content');
            if (content) content.prepend(warning);
        }
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

        this.resultsContainer.textContent = '';
        const ph = document.createElement('div');
        ph.className = 'ml-panel__placeholder';
        ph.textContent = i18nService.t('ml.loadAndAnalyze');
        this.resultsContainer.appendChild(ph);
    }

    /**
     * Fetch ML device status from backend
     * @private
     */
    async _fetchDeviceStatus() {
        try {
            const health = await apiService.getMLHealth();
            if (this._deviceSelect && health.device) {
                // Set select to match actual device
                const val = health.device === 'cuda' ? 'cuda' : health.device === 'cpu' ? 'cpu' : 'auto';
                this._deviceSelect.value = val;
            }
            if (this._deviceStatus) {
                const icon = health.gpu_available ? '\u2705' : '\u26A0\uFE0F';
                const name = health.gpu_name || 'CPU';
                this._deviceStatus.textContent = ` ${icon} ${name}`;
                this._deviceStatus.title = health.gpu_available
                    ? `GPU: ${health.gpu_name} | Active: ${health.device}`
                    : 'No GPU detected - using CPU';
            }
        } catch (_) {
            if (this._deviceStatus) this._deviceStatus.textContent = '';
        }
    }

    /**
     * Switch ML device
     * @param {string} device - "auto", "cuda", or "cpu"
     * @private
     */
    async _switchDevice(device) {
        try {
            this._deviceSelect.disabled = true;
            if (this._deviceStatus) this._deviceStatus.textContent = ' ...';
            const result = await apiService.setMLDevice(device);
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: `ML device: ${result.device} (stride: ${result.adaptive_stride})`,
            });
            await this._fetchDeviceStatus();
        } catch (err) {
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'error',
                message: err.message || 'Failed to switch device',
            });
            await this._fetchDeviceStatus();
        } finally {
            this._deviceSelect.disabled = false;
        }
    }

    /**
     * Run ML prediction
     * @private
     */
    async _runPrediction() {
        if (!this.slideId || this.isLoading) {return;}

        const canProceed = await requestMLWorkerAccess(i18nService.t('ml.workerLabel'));
        if (!canProceed) return;

        this.isLoading = true;
        this.predictBtn.disabled = true;
        // Update predict button to show spinner
        this.predictBtn.textContent = '';
        const spinner = document.createElement('span');
        spinner.className = 'ml-panel__spinner';
        this.predictBtn.appendChild(spinner);
        this.predictBtn.appendChild(document.createTextNode(' ' + i18nService.t('ml.analyzing')));

        // Show loading in results
        this.resultsContainer.textContent = '';
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'ml-panel__loading';
        const spinnerLarge = document.createElement('span');
        spinnerLarge.className = 'ml-panel__spinner ml-panel__spinner--large';
        loadingDiv.appendChild(spinnerLarge);
        const loadP = document.createElement('p');
        loadP.textContent = i18nService.t('ml.analysisInProgress');
        loadingDiv.appendChild(loadP);
        const subP = document.createElement('p');
        subP.className = 'ml-panel__loading-sub';
        subP.textContent = i18nService.t('ml.analysisDuration');
        loadingDiv.appendChild(subP);
        this.resultsContainer.appendChild(loadingDiv);

        eventBus.emit(Events.ML_WORKER_BUSY, { panel: 'ml', label: i18nService.t('panel.ml') });
        eventBus.emit(Events.ML_PREDICTION_START, {
            viewerId: this.viewerId,
            slideId: this.slideId,
        });

        try {
            const predictOptions = {
                numMcSamples: 10,
                modelId: this.selectedModelId || undefined,
            };

            // Viewport mode: send pixel region
            if (this.analysisScope === 'viewport' && this._viewerInstance) {
                const region = this._viewerInstance.getViewportPixelBounds();
                if (region) {
                    predictOptions.region = region;
                }
            }

            const result = await apiService.predict(this.slideId, predictOptions);

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
            this._displayError(userFriendlyMLError(error));

            eventBus.emit(Events.ML_PREDICTION_ERROR, {
                viewerId: this.viewerId,
                slideId: this.slideId,
                error: error.message,
            });
        } finally {
            this.isLoading = false;
            this.predictBtn.disabled = false;
            // Restore predict button with icon + translated text
            // Static SVG icon - not user input
            this.predictBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';
            this.predictBtn.appendChild(document.createTextNode(' ' + i18nService.t('ml.analyze')));
            eventBus.emit(Events.ML_WORKER_FREE);
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

        const _t = (k) => i18nService.t(k);

        // Build results via DOM API
        this.resultsContainer.textContent = '';
        const resultDiv = document.createElement('div');
        resultDiv.className = 'ml-panel__result';

        // Prediction label
        const predRow = document.createElement('div');
        predRow.className = 'ml-panel__prediction';
        const predLabel = document.createElement('span');
        predLabel.className = 'ml-panel__prediction-label';
        predLabel.textContent = _t('ml.prediction');
        predRow.appendChild(predLabel);
        const predClass = document.createElement('span');
        predClass.className = 'ml-panel__prediction-class';
        predClass.textContent = result.prediction_class;
        predRow.appendChild(predClass);
        resultDiv.appendChild(predRow);

        // Metrics
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'ml-panel__metrics';

        // Confidence
        const confMetric = document.createElement('div');
        confMetric.className = 'ml-panel__metric';
        const confLabel = document.createElement('span');
        confLabel.className = 'ml-panel__metric-label';
        confLabel.textContent = _t('ml.confidence');
        confMetric.appendChild(confLabel);
        const confValue = document.createElement('span');
        confValue.className = 'ml-panel__metric-value';
        confValue.style.color = confColor;
        confValue.textContent = `${confidence}%`;
        confMetric.appendChild(confValue);
        metricsDiv.appendChild(confMetric);

        // Uncertainty
        if (uncertainty !== null) {
            const uncMetric = document.createElement('div');
            uncMetric.className = 'ml-panel__metric';
            const uncLabel = document.createElement('span');
            uncLabel.className = 'ml-panel__metric-label';
            uncLabel.textContent = _t('ml.uncertainty');
            uncMetric.appendChild(uncLabel);
            const uncValue = document.createElement('span');
            uncValue.className = 'ml-panel__metric-value ml-panel__metric-value--uncertainty';
            uncValue.textContent = `\u00b1${uncertainty}%`;
            uncMetric.appendChild(uncValue);
            metricsDiv.appendChild(uncMetric);
        }

        // Time
        const timeMetric = document.createElement('div');
        timeMetric.className = 'ml-panel__metric';
        const timeLabel = document.createElement('span');
        timeLabel.className = 'ml-panel__metric-label';
        timeLabel.textContent = _t('ml.time');
        timeMetric.appendChild(timeLabel);
        const timeValue = document.createElement('span');
        timeValue.className = 'ml-panel__metric-value';
        timeValue.textContent = `${result.execution_time_ms?.toFixed(0) || '?'}ms`;
        timeMetric.appendChild(timeValue);
        metricsDiv.appendChild(timeMetric);

        resultDiv.appendChild(metricsDiv);

        // Probabilities
        const probDiv = document.createElement('div');
        probDiv.className = 'ml-panel__probabilities';
        const probTitle = document.createElement('span');
        probTitle.className = 'ml-panel__prob-title';
        probTitle.textContent = _t('ml.classProbabilities');
        probDiv.appendChild(probTitle);

        const sortedProbs = Object.entries(result.probabilities || {}).sort((a, b) => b[1] - a[1]);
        for (const [cls, prob] of sortedProbs) {
            const pct = (prob * 100).toFixed(1);
            const isMain = cls === result.prediction_class;
            const row = document.createElement('div');
            row.className = `ml-panel__prob-row${isMain ? ' is-main' : ''}`;
            const label = document.createElement('span');
            label.className = 'ml-panel__prob-label';
            label.textContent = cls;
            row.appendChild(label);
            const barOuter = document.createElement('div');
            barOuter.className = 'ml-panel__prob-bar';
            const barFill = document.createElement('div');
            barFill.className = 'ml-panel__prob-fill';
            barFill.style.width = `${pct}%`;
            barOuter.appendChild(barFill);
            row.appendChild(barOuter);
            const val = document.createElement('span');
            val.className = 'ml-panel__prob-value';
            val.textContent = `${pct}%`;
            row.appendChild(val);
            probDiv.appendChild(row);
        }
        resultDiv.appendChild(probDiv);

        this.resultsContainer.appendChild(resultDiv);
    }

    /**
     * Display error message
     * @param {string} message - Error message
     * @private
     */
    _displayError(message) {
        this.resultsContainer.textContent = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'ml-panel__error';
        // Static SVG icon - not user input
        errorDiv.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
        const errTitle = document.createElement('p');
        errTitle.textContent = i18nService.t('error.analysisError');
        errorDiv.appendChild(errTitle);
        const errDetail = document.createElement('p');
        errDetail.className = 'ml-panel__error-detail';
        errDetail.textContent = message;
        errorDiv.appendChild(errDetail);
        this.resultsContainer.appendChild(errorDiv);
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

        // Static SVG icon constant - not user input
        const heatmapSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/><path d="M15 3v18"/></svg>';
        if (this.heatmapVisible) {
            this.opacityContainer.style.display = 'flex';
            this.heatmapBtn.innerHTML = heatmapSvg;
            this.heatmapBtn.appendChild(document.createTextNode(' ' + i18nService.t('ml.hideHeatmap')));
        } else {
            this.opacityContainer.style.display = 'none';
            this.heatmapBtn.innerHTML = heatmapSvg;
            this.heatmapBtn.appendChild(document.createTextNode(' ' + i18nService.t('ml.showHeatmap')));
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
     * Load available ML models and populate the selector
     * @private
     */
    async _loadModels() {
        try {
            const models = await apiService.listModels();
            this._populateModelSelector(models);
        } catch (err) {
            console.warn('[MLPanel] Could not load models:', err);
        }
    }

    /**
     * Get user-friendly model name
     * @param {Object} model
     * @returns {string}
     * @private
     */
    _friendlyModelName(model) {
        const nameMap = {
            'phikon-v2_features_1024d': 'Phikon v2',
            'phikon-v2': 'Phikon v2',
            'phikon': 'Phikon v2',
            'ctranspath': 'CTransPath',
            'uni': 'UNI',
            'resnet50_imagenet': 'ResNet-50',
        };
        const name = model.model_name || model.model_id;
        const nameLower = name.toLowerCase();
        // Check exact match first, then partial
        if (nameMap[nameLower]) {
            return nameMap[nameLower];
        }
        for (const [key, friendly] of Object.entries(nameMap)) {
            if (nameLower.includes(key)) {
                return friendly;
            }
        }
        // Fallback: capitalize and clean up underscores/dashes
        return name
            .replace(/[_-]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    }

    /**
     * Get a short description/tooltip for a model
     * @param {Object} model
     * @returns {string}
     * @private
     */
    _modelTooltip(model) {
        const tooltipMap = {
            'phikon': 'Mod\u00e8le fondation histopathologie, 1024 dimensions',
            'ctranspath': 'Transformeur pr\u00e9-entra\u00een\u00e9 pour la pathologie computationnelle',
            'uni': 'Universal image encoder pour la pathologie',
            'resnet50': 'R\u00e9seau r\u00e9siduel classique pr\u00e9-entra\u00een\u00e9 sur ImageNet',
        };
        const name = (model.model_name || model.model_id).toLowerCase();
        for (const [key, tip] of Object.entries(tooltipMap)) {
            if (name.includes(key)) {
                return tip;
            }
        }
        return model.description || '';
    }

    /**
     * Populate the model selector dropdown
     * @param {Array} models
     * @private
     */
    _populateModelSelector(models) {
        const select = this.element.querySelector('.ml-panel__model-select');
        if (!select) {
            return;
        }

        // Clear existing options
        while (select.firstChild) {
            select.removeChild(select.firstChild);
        }

        if (models.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = i18nService.t('ml.noModels');
            select.appendChild(opt);
            return;
        }

        models.forEach((model, i) => {
            const opt = document.createElement('option');
            opt.value = model.model_id;
            const friendly = this._friendlyModelName(model);
            opt.textContent = i === 0 ? `${friendly} (${i18nService.t('ml.recommended')})` : friendly;
            const tooltip = this._modelTooltip(model);
            if (tooltip) {
                opt.title = tooltip;
            }
            select.appendChild(opt);
        });

        select.disabled = false;
        select.addEventListener('change', (e) => {
            this.selectedModelId = e.target.value || null;
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
        const header = this.element.querySelector('.ml-panel__header');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
        try { localStorage.setItem('varuna_panel_ml_open', String(!this.isCollapsed)); } catch (_) { /* noop */ }
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
