/**
 * DriftDashboard - Admin dashboard for ML model drift monitoring
 *
 * Full page component showing drift metrics for all loaded models.
 * Fetches model list and drift reports from the backend API.
 *
 * Uses DOM methods for all dynamic content (no innerHTML).
 *
 * Reference: Issue #96
 * @module components/DriftDashboard
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';

class DriftDashboard {
    /**
     * @param {HTMLElement} container - Root container element
     */
    constructor(container) {
        this.container = container;

        /** @type {HTMLElement|null} */
        this.element = null;

        /** @type {Array} */
        this.models = [];

        /** @type {Map<string, Object>} model_id -> drift report */
        this.reports = new Map();

        /** @type {boolean} */
        this.isLoading = false;

        this._create();
        this._loadData();
    }

    // ==========================================
    // DOM CREATION
    // ==========================================

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'drift-dashboard';

        // Header
        const header = document.createElement('div');
        header.className = 'drift-dashboard__header';

        const backBtn = document.createElement('button');
        backBtn.className = 'drift-dashboard__back-btn';
        backBtn.textContent = i18nService.t('drift.back');
        backBtn.addEventListener('click', () => {
            eventBus.emit(Events.PAGE_CHANGED, { page: 'home' });
        });
        header.appendChild(backBtn);

        const title = document.createElement('h1');
        title.className = 'drift-dashboard__title';
        title.textContent = i18nService.t('drift.title');
        header.appendChild(title);

        this._refreshBtn = document.createElement('button');
        this._refreshBtn.className = 'drift-dashboard__refresh-btn';
        this._refreshBtn.textContent = i18nService.t('drift.refresh');
        this._refreshBtn.addEventListener('click', () => this._loadData());
        header.appendChild(this._refreshBtn);

        this.element.appendChild(header);

        // Content area (cards go here)
        this._content = document.createElement('div');
        this._content.className = 'drift-dashboard__content';
        this.element.appendChild(this._content);

        this.container.appendChild(this.element);
    }

    /**
     * Remove all child nodes from an element safely.
     * @param {HTMLElement} el
     */
    _clearElement(el) {
        while (el.firstChild) {
            el.removeChild(el.firstChild);
        }
    }

    // ==========================================
    // DATA LOADING
    // ==========================================

    async _loadData() {
        if (this.isLoading) return;

        this.isLoading = true;
        this._refreshBtn.disabled = true;
        this._renderLoading();
        eventBus.emit(Events.DRIFT_LOADING);

        try {
            // Fetch model list
            const modelsResponse = await apiService.listModels();
            // modelsResponse could be an array directly or { models: [...] }
            this.models = Array.isArray(modelsResponse) ? modelsResponse : (modelsResponse.models || []);

            // Fetch drift reports for each model
            this.reports.clear();
            for (const model of this.models) {
                try {
                    const report = await apiService.getDriftReport(model.model_id);
                    this.reports.set(model.model_id, report);
                } catch (err) {
                    console.warn('[DriftDashboard] Failed to fetch drift for', model.model_id, err);
                }
            }

            this._renderCards();
            eventBus.emit(Events.DRIFT_READY, { modelCount: this.models.length });
        } catch (err) {
            console.error('[DriftDashboard] Load failed:', err);
            this._renderError(err.message);
            eventBus.emit(Events.DRIFT_ERROR, { error: err.message });
        } finally {
            this.isLoading = false;
            this._refreshBtn.disabled = false;
        }
    }

    // ==========================================
    // RENDER STATES
    // ==========================================

    _renderLoading() {
        this._clearElement(this._content);
        const loading = document.createElement('div');
        loading.className = 'drift-dashboard__loading';
        loading.textContent = i18nService.t('drift.loading');
        this._content.appendChild(loading);
    }

    _renderError(message) {
        this._clearElement(this._content);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'drift-dashboard__error';
        errorDiv.textContent = i18nService.t('generic.error', { message });
        this._content.appendChild(errorDiv);
    }

    _renderCards() {
        this._clearElement(this._content);

        if (this.models.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'drift-dashboard__empty';
            empty.textContent = i18nService.t('drift.noModels');
            this._content.appendChild(empty);
            return;
        }

        for (const model of this.models) {
            const report = this.reports.get(model.model_id);
            const card = this._createModelCard(model, report);
            this._content.appendChild(card);
        }
    }

    // ==========================================
    // MODEL CARD
    // ==========================================

    _createModelCard(model, report) {
        const card = document.createElement('div');
        card.className = 'drift-dashboard__card';

        // Model header with name and badge
        const headerDiv = document.createElement('div');
        headerDiv.className = 'drift-dashboard__model-header';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'drift-dashboard__model-name';
        nameSpan.textContent = model.model_name || model.model_id;
        headerDiv.appendChild(nameSpan);

        const badge = document.createElement('span');
        const isLoaded = model.status === 'loaded';
        badge.className = 'drift-dashboard__model-badge drift-dashboard__model-badge--' +
            (isLoaded ? 'loaded' : 'available');
        badge.textContent = isLoaded ? i18nService.t('drift.modelLoaded') : i18nService.t('drift.modelAvailable');
        headerDiv.appendChild(badge);

        card.appendChild(headerDiv);

        // Drift metrics
        if (report && report.metrics) {
            for (const metric of report.metrics) {
                const metricRow = this._createMetricRow(metric);
                card.appendChild(metricRow);
            }

            // Overall status
            const statusDiv = document.createElement('div');
            statusDiv.className = 'drift-dashboard__status ' +
                (report.overall_drifted ? 'drift-dashboard__status--drifted' : 'drift-dashboard__status--ok');
            statusDiv.textContent = report.overall_drifted ? i18nService.t('drift.driftDetected') : i18nService.t('drift.driftNormal');
            card.appendChild(statusDiv);

            // Recommendation
            const recDiv = document.createElement('div');
            recDiv.className = 'drift-dashboard__recommendation';
            recDiv.textContent = report.recommendation;
            card.appendChild(recDiv);
        } else {
            const noData = document.createElement('div');
            noData.className = 'drift-dashboard__recommendation';
            noData.textContent = i18nService.t('drift.none');
            card.appendChild(noData);
        }

        return card;
    }

    _createMetricRow(metric) {
        const row = document.createElement('div');
        row.className = 'drift-dashboard__metric';

        // Label
        const label = document.createElement('span');
        label.className = 'drift-dashboard__metric-label';
        label.textContent = metric.metric_name === 'mmd' ? i18nService.t('drift.metricMMD') : i18nService.t('drift.metricKS');
        row.appendChild(label);

        // Value
        const value = document.createElement('span');
        value.className = 'drift-dashboard__metric-value';
        value.textContent = metric.value.toFixed(4);
        row.appendChild(value);

        // Bar with threshold line
        const barContainer = document.createElement('div');
        barContainer.className = 'drift-dashboard__bar';

        const barFill = document.createElement('div');
        barFill.className = 'drift-dashboard__bar-fill';

        // Determine fill width as percentage of a reasonable max
        // Use 2x threshold as the visual max range
        const visualMax = metric.threshold * 2;
        const fillPct = Math.min((metric.value / visualMax) * 100, 100);
        barFill.style.width = fillPct + '%';

        // Color based on drift status
        if (metric.is_drifted) {
            barFill.classList.add('drift-dashboard__bar-fill--warning');
        } else {
            barFill.classList.add('drift-dashboard__bar-fill--ok');
        }
        barContainer.appendChild(barFill);

        // Threshold line
        const thresholdLine = document.createElement('div');
        thresholdLine.className = 'drift-dashboard__bar-threshold';
        const thresholdPct = Math.min((metric.threshold / visualMax) * 100, 100);
        thresholdLine.style.left = thresholdPct + '%';
        barContainer.appendChild(thresholdLine);

        row.appendChild(barContainer);

        return row;
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    destroy() {
        this.models = [];
        this.reports.clear();
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this._content = null;
        this._refreshBtn = null;
    }
}

export { DriftDashboard };
export default DriftDashboard;
