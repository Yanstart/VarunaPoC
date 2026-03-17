/**
 * CountingPanel - Annotation counting and classification summary
 *
 * Displays live annotation statistics for the current slide:
 * - Total annotation count
 * - Count by label (with colored dots)
 * - Count by type (manual/auto/auto_confirmed)
 * - Confidence distribution bar
 *
 * Auto-refreshes when annotations are created, deleted, or confirmed.
 *
 * @module components/CountingPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { i18nService } from '../services/I18nService.js';

class CountingPanel {
    /**
     * @param {HTMLElement} container - Parent element
     */
    constructor(container) {
        this.container = container;
        this.element = null;

        /** @type {Array<Function>} Unsubscribe functions */
        this._unsubscribers = [];

        this._create();
        this._setupEventListeners();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'counting-panel';
        this._render();
        this.container.appendChild(this.element);
    }

    _setupEventListeners() {
        // Refresh on any annotation change
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_STATS_UPDATED, () => this._render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATIONS_LOADED, () => this._render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_CREATED, () => this._render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_DELETED, () => this._render()),
        );
        this._unsubscribers.push(
            eventBus.on(Events.DETECTION_CONFIRM, () => this._render()),
        );
    }

    _render() {
        const stats = annotationStore.stats;
        const total = stats ? stats.total : annotationStore.annotations.size;

        if (total === 0 && !stats) {
            /* i18n values are from static locale JSON files, not user input */
            this.element.innerHTML = `
                <div class="counting-panel__empty">
                    ${i18nService.t('counting.noAnnotations')}
                </div>
            `;
            return;
        }

        // Use backend stats if available, otherwise compute locally
        const data = stats || annotationStore.computeLocalStats();

        const byLabelHtml = data.by_label.length > 0
            ? data.by_label.map(l => `
                <div class="counting-panel__row">
                    <span class="counting-panel__dot" style="background: ${l.color}"></span>
                    <span class="counting-panel__name">${l.name}</span>
                    <span class="counting-panel__count">${l.count}</span>
                </div>
            `).join('')
            : '';

        const unlabeledHtml = data.unlabeled > 0
            ? `<div class="counting-panel__row">
                    <span class="counting-panel__dot counting-panel__dot--none"></span>
                    <span class="counting-panel__name">${i18nService.t('counting.noLabel')}</span>
                    <span class="counting-panel__count">${data.unlabeled}</span>
                </div>`
            : '';

        const byTypeHtml = data.by_type.map(t => `
            <div class="counting-panel__row">
                <span class="counting-panel__type-badge counting-panel__type-badge--${t.type}">${t.type}</span>
                <span class="counting-panel__count">${t.count}</span>
            </div>
        `).join('');

        const conf = data.confidence_distribution;
        const confTotal = conf.high + conf.medium + conf.low + conf.unscored;

        this.element.innerHTML = `
            <div class="counting-panel__header">
                <span class="counting-panel__title">${i18nService.t('counting.annotations')}</span>
                <span class="counting-panel__total">${data.total}</span>
            </div>
            <div class="counting-panel__summary">
                <span class="counting-panel__total-big">${data.total}</span>
                <span class="counting-panel__total-label">${data.total === 1 ? i18nService.t('counting.annotation') : i18nService.t('counting.annotationsPlural')}</span>
            </div>
            <div class="counting-panel__body">
                ${byLabelHtml || unlabeledHtml ? `
                    <div class="counting-panel__section">
                        <div class="counting-panel__section-title">${i18nService.t('counting.byLabel')}</div>
                        ${byLabelHtml}
                        ${unlabeledHtml}
                    </div>
                ` : ''}
                ${byTypeHtml ? `
                    <div class="counting-panel__section">
                        <div class="counting-panel__section-title">${i18nService.t('counting.byType')}</div>
                        ${byTypeHtml}
                    </div>
                ` : ''}
                ${confTotal > 0 ? `
                    <div class="counting-panel__section">
                        <div class="counting-panel__section-title">${i18nService.t('counting.confidence')}</div>
                        <div class="counting-panel__conf-bar">
                            <div class="counting-panel__conf-seg counting-panel__conf-seg--high"
                                 style="width: ${confTotal ? (conf.high / confTotal * 100) : 0}%"
                                 title="${i18nService.t('counting.confHigh')} : ${conf.high}"></div>
                            <div class="counting-panel__conf-seg counting-panel__conf-seg--medium"
                                 style="width: ${confTotal ? (conf.medium / confTotal * 100) : 0}%"
                                 title="${i18nService.t('counting.confMedium')} : ${conf.medium}"></div>
                            <div class="counting-panel__conf-seg counting-panel__conf-seg--low"
                                 style="width: ${confTotal ? (conf.low / confTotal * 100) : 0}%"
                                 title="${i18nService.t('counting.confLow')} : ${conf.low}"></div>
                            <div class="counting-panel__conf-seg counting-panel__conf-seg--none"
                                 style="width: ${confTotal ? (conf.unscored / confTotal * 100) : 0}%"
                                 title="n/a : ${conf.unscored}"></div>
                        </div>
                        <div class="counting-panel__conf-legend">
                            ${conf.high ? `<span class="counting-panel__conf-label counting-panel__conf-label--high">${conf.high} ${i18nService.t('counting.confHigh')}</span>` : ''}
                            ${conf.medium ? `<span class="counting-panel__conf-label counting-panel__conf-label--medium">${conf.medium} ${i18nService.t('counting.confMedium')}</span>` : ''}
                            ${conf.low ? `<span class="counting-panel__conf-label counting-panel__conf-label--low">${conf.low} ${i18nService.t('counting.confLow')}</span>` : ''}
                            ${conf.unscored ? `<span class="counting-panel__conf-label counting-panel__conf-label--none">${conf.unscored} n/a</span>` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { CountingPanel };
export default CountingPanel;
