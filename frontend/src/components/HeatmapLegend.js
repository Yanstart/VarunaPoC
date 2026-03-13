/**
 * HeatmapLegend - Color scale legend for ML heatmap overlay
 *
 * Shows a gradient bar (jet colormap) with labels when the
 * heatmap is visible. Positioned bottom-left of viewer area.
 *
 * @module components/HeatmapLegend
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { i18nService } from '../services/I18nService.js';

export class HeatmapLegend {
    /**
     * @param {HTMLElement} container - Parent element (viewer-area)
     */
    constructor(container) {
        this.container = container;
        this._unsubscribers = [];

        this._build();
        this._setupEventListeners();
    }

    _build() {
        this.el = document.createElement('div');
        this.el.className = 'heatmap-legend';
        this.el.setAttribute('role', 'img');
        this.el.setAttribute('aria-label', 'Heatmap color scale');

        this._lowLabel = document.createElement('span');
        this._lowLabel.className = 'heatmap-legend__label';
        this._lowLabel.textContent = i18nService.t('legend.low');
        this.el.appendChild(this._lowLabel);

        const gradient = document.createElement('div');
        gradient.className = 'heatmap-legend__gradient';
        this.el.appendChild(gradient);

        this._highLabel = document.createElement('span');
        this._highLabel.className = 'heatmap-legend__label';
        this._highLabel.textContent = i18nService.t('legend.high');
        this.el.appendChild(this._highLabel);

        this._title = document.createElement('div');
        this._title.className = 'heatmap-legend__title';
        this._title.textContent = i18nService.t('legend.attention');
        this.el.appendChild(this._title);

        this.container.appendChild(this.el);
    }

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ML_HEATMAP_TOGGLE, ({ visible }) => {
                this.el.classList.toggle('heatmap-legend--visible', visible);
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ML_HEATMAP_OPACITY_CHANGE, ({ opacity }) => {
                this.el.style.opacity = Math.max(0.3, opacity);
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.LOCALE_CHANGED, () => {
                this._lowLabel.textContent = i18nService.t('legend.low');
                this._highLabel.textContent = i18nService.t('legend.high');
                this._title.textContent = i18nService.t('legend.attention');
            }),
        );
    }

    destroy() {
        for (const unsub of this._unsubscribers) {
            if (typeof unsub === 'function') unsub();
        }
        this._unsubscribers = [];

        if (this.el && this.el.parentNode) {
            this.el.parentNode.removeChild(this.el);
        }
        this.el = null;
    }
}
