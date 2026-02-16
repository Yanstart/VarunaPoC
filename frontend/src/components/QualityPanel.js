/**
 * QualityPanel - Inter-annotator agreement metrics panel
 *
 * Sidebar panel displaying kappa scores, confusion matrix,
 * F1/precision/recall per label, IoU histogram, and disagreement toggle.
 *
 * @module components/QualityPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';

class QualityPanel {
    /**
     * @param {HTMLElement} container - Parent element
     */
    constructor(container) {
        this.container = container;
        this.element = null;
        this.slideId = null;

        /** @type {Array<{username: string, annotation_count: number, labels_used: string[]}>} */
        this.annotators = [];

        /** @type {Object|null} Last computed kappa result */
        this.kappaResult = null;
        /** @type {Object|null} Last computed confusion matrix */
        this.confusionResult = null;
        /** @type {Object|null} Last computed F1 metrics */
        this.f1Result = null;
        /** @type {Object|null} Last computed IoU distribution */
        this.iouResult = null;

        this.isLoading = false;
        this.isCollapsed = true;
        this.showDisagreements = false;

        /** @type {Array<Function>} */
        this._unsubscribers = [];

        this._create();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'quality-panel is-collapsed';
        this._render();
        this.container.appendChild(this.element);
    }

    /**
     * Set the current slide and fetch annotators
     * @param {string} slideId
     */
    async setSlide(slideId) {
        this.slideId = slideId;
        this.kappaResult = null;
        this.confusionResult = null;
        this.f1Result = null;
        this.iouResult = null;
        this.showDisagreements = false;

        try {
            this.annotators = await apiService.getAnnotators(slideId);
        } catch {
            this.annotators = [];
        }

        this._render();
    }

    // ==========================================
    // RENDERING
    // ==========================================

    _render() {
        const hasAnnotators = this.annotators.length >= 2;

        this.element.innerHTML = `
            <div class="quality-panel__header">
                <span class="quality-panel__title">Métriques de qualité</span>
                <span class="quality-panel__toggle">&#9660;</span>
            </div>
            <div class="quality-panel__body">
                ${!hasAnnotators
        ? `<div class="quality-panel__empty">
                        ${this.annotators.length === 0
        ? 'No annotators on this slide'
        : 'Need at least 2 annotators'}
                       </div>`
        : this._renderContent()
}
            </div>
        `;

        // Bind header toggle
        const header = this.element.querySelector('.quality-panel__header');
        header.addEventListener('click', () => {
            this.isCollapsed = !this.isCollapsed;
            this.element.classList.toggle('is-collapsed', this.isCollapsed);
        });

        // Bind compute button
        const btn = this.element.querySelector('.quality-panel__compute-btn');
        if (btn) {
            btn.addEventListener('click', () => this._compute());
        }

        // Bind disagreement toggle
        const checkbox = this.element.querySelector('.quality-panel__disagree-checkbox');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.showDisagreements = e.target.checked;
                this._emitDisagreementToggle();
            });
        }
    }

    _renderContent() {
        const opts = this.annotators.map(a =>
            `<option value="${a.username}">${a.username} (${a.annotation_count})</option>`,
        ).join('');

        return `
            <div class="quality-panel__selectors">
                <div class="quality-panel__select-row">
                    <span class="quality-panel__select-label">A</span>
                    <select class="quality-panel__select" id="qp-annotator-a">
                        ${opts}
                    </select>
                </div>
                <div class="quality-panel__select-row">
                    <span class="quality-panel__select-label">B</span>
                    <select class="quality-panel__select" id="qp-annotator-b">
                        ${this.annotators.map((a, i) =>
        `<option value="${a.username}" ${i === 1 ? 'selected' : ''}>${a.username} (${a.annotation_count})</option>`,
    ).join('')}
                    </select>
                </div>
            </div>
            <button class="quality-panel__compute-btn" ${this.isLoading ? 'disabled' : ''}>
                ${this.isLoading ? 'Calcul en cours...' : 'Calculer les métriques'}
            </button>
            ${this.kappaResult ? this._renderKappa() : ''}
            ${this.confusionResult ? this._renderConfusionMatrix() : ''}
            ${this.f1Result ? this._renderF1Metrics() : ''}
            ${this.iouResult ? this._renderIoUHistogram() : ''}
            ${this.kappaResult ? this._renderDisagreementToggle() : ''}
        `;
    }

    _renderKappa() {
        const r = this.kappaResult;
        const cssClass = r.interpretation.toLowerCase().replace(/\s+/g, '-');

        return `
            <div class="quality-panel__section">
                <div class="quality-panel__section-title">Score Kappa</div>
                <div class="quality-panel__kappa quality-panel__kappa--${cssClass}">
                    <span class="quality-panel__kappa-value">${r.kappa.toFixed(3)}</span>
                    <span class="quality-panel__kappa-label">${r.interpretation}</span>
                </div>
                <div class="quality-panel__match-info">
                    Matched: <span>${r.n_matched}</span> |
                    Unmatched A: <span>${r.n_unmatched_a}</span> |
                    Unmatched B: <span>${r.n_unmatched_b}</span>
                </div>
            </div>
        `;
    }

    _renderConfusionMatrix() {
        const r = this.confusionResult;
        if (!r.categories.length) {return '';}

        const headerCells = r.categories.map(c => `<th>${c}</th>`).join('');
        const rows = r.matrix.map((row, i) => {
            const cells = row.map((val, j) => {
                const cls = i === j ? ' class="diagonal"' : '';
                return `<td${cls}>${val}</td>`;
            }).join('');
            return `<tr><th>${r.categories[i]}</th>${cells}</tr>`;
        }).join('');

        return `
            <div class="quality-panel__section">
                <div class="quality-panel__section-title">Confusion Matrix</div>
                <table class="quality-panel__matrix">
                    <tr><th></th>${headerCells}</tr>
                    ${rows}
                </table>
            </div>
        `;
    }

    _renderF1Metrics() {
        const r = this.f1Result;
        if (!r.metrics.length) {return '';}

        const rows = r.metrics.map(m => `
            <div class="quality-panel__f1-row">
                <span class="quality-panel__f1-label">${m.label}</span>
                <span class="quality-panel__f1-value" title="Précision">${m.precision.toFixed(2)}</span>
                <span class="quality-panel__f1-value" title="Rappel">${m.recall.toFixed(2)}</span>
                <span class="quality-panel__f1-value" title="F1">${m.f1.toFixed(2)}</span>
            </div>
        `).join('');

        return `
            <div class="quality-panel__section">
                <div class="quality-panel__section-title">Per-Label Metrics</div>
                <div class="quality-panel__f1-row" style="color: #666; font-size: 10px;">
                    <span class="quality-panel__f1-label">Label</span>
                    <span class="quality-panel__f1-value">P</span>
                    <span class="quality-panel__f1-value">R</span>
                    <span class="quality-panel__f1-value">F1</span>
                </div>
                ${rows}
            </div>
        `;
    }

    _renderIoUHistogram() {
        const r = this.iouResult;
        if (!r.histogram || !r.histogram.length) {return '';}

        const maxCount = Math.max(...r.histogram.map(b => b.count), 1);
        const bars = r.histogram.map(bin => {
            const height = (bin.count / maxCount) * 100;
            return `<div class="quality-panel__hist-bar" style="height: ${height}%" title="${bin.bin_start.toFixed(1)}-${bin.bin_end.toFixed(1)}: ${bin.count}"></div>`;
        }).join('');

        return `
            <div class="quality-panel__section">
                <div class="quality-panel__section-title">IoU Distribution</div>
                <div class="quality-panel__histogram">${bars}</div>
                <div class="quality-panel__hist-labels">
                    <span>0.0</span>
                    <span>0.5</span>
                    <span>1.0</span>
                </div>
                <div class="quality-panel__iou-stats">
                    <span>Mean: <span class="quality-panel__iou-stat-value">${r.mean.toFixed(3)}</span></span>
                    <span>Median: <span class="quality-panel__iou-stat-value">${r.median.toFixed(3)}</span></span>
                </div>
            </div>
        `;
    }

    _renderDisagreementToggle() {
        return `
            <div class="quality-panel__section">
                <label class="quality-panel__disagree-toggle">
                    <input type="checkbox"
                           class="quality-panel__disagree-checkbox"
                           ${this.showDisagreements ? 'checked' : ''}>
                    Superposition des désaccords
                </label>
            </div>
        `;
    }

    // ==========================================
    // COMPUTATION
    // ==========================================

    async _compute() {
        if (!this.slideId || this.isLoading) {return;}

        const selectA = this.element.querySelector('#qp-annotator-a');
        const selectB = this.element.querySelector('#qp-annotator-b');
        if (!selectA || !selectB) {return;}

        const annotatorA = selectA.value;
        const annotatorB = selectB.value;

        if (annotatorA === annotatorB) {
            this.kappaResult = {
                kappa: 1.0,
                interpretation: 'Almost Perfect',
                annotator_a: annotatorA,
                annotator_b: annotatorB,
                n_matched: 0,
                n_unmatched_a: 0,
                n_unmatched_b: 0,
                matching_strategy: 'iou',
            };
            this._render();
            return;
        }

        this.isLoading = true;
        this._render();
        eventBus.emit(Events.QUALITY_LOADING);

        const params = {
            annotator_a: annotatorA,
            annotator_b: annotatorB,
            iou_threshold: 0.5,
            matching_strategy: 'iou',
        };

        try {
            // Run all computations in parallel
            const [kappa, confusion, f1, iou] = await Promise.all([
                apiService.computeKappa(this.slideId, params),
                apiService.computeConfusionMatrix(this.slideId, params),
                apiService.computeF1Metrics(this.slideId, params),
                apiService.computeIoUDistribution(this.slideId, params),
            ]);

            this.kappaResult = kappa;
            this.confusionResult = confusion;
            this.f1Result = f1;
            this.iouResult = iou;

            eventBus.emit(Events.QUALITY_READY, { kappa });

        } catch (err) {
            console.error('[QualityPanel] Computation failed:', err);
            eventBus.emit(Events.QUALITY_ERROR, { error: err.message });
        } finally {
            this.isLoading = false;
            this._render();
        }
    }

    async _emitDisagreementToggle() {
        if (this.showDisagreements && this.slideId) {
            const selectA = this.element.querySelector('#qp-annotator-a');
            const selectB = this.element.querySelector('#qp-annotator-b');
            if (!selectA || !selectB) {return;}

            try {
                const geojson = await apiService.getDisagreements(this.slideId, {
                    annotator_a: selectA.value,
                    annotator_b: selectB.value,
                    iou_threshold: 0.5,
                });
                eventBus.emit(Events.QUALITY_DISAGREEMENT_TOGGLE, {
                    visible: true,
                    features: geojson.features,
                });
            } catch (err) {
                console.error('[QualityPanel] Failed to load disagreements:', err);
            }
        } else {
            eventBus.emit(Events.QUALITY_DISAGREEMENT_TOGGLE, {
                visible: false,
                features: [],
            });
        }
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { QualityPanel };
export default QualityPanel;
