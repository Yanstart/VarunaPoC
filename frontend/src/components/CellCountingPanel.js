/**
 * CellCountingPanel - Automated Ki-67 / IHC cell counting
 *
 * Workflow:
 * 1. User selects stain type (Ki-67 / HER2 / PD-L1)
 * 2. Clicks "Compter les cellules"
 * 3. Loading state while backend runs counting
 * 4. Results: large percentage index, ratio bar, counts breakdown
 *
 * Follows DetectionPanel pattern: collapsible accordion, state machine.
 *
 * Note: innerHTML usage is safe here — all values are numeric from our own
 * backend API (total_cells, positive, negative, ratio, processing_time_ms).
 * No user-supplied strings are interpolated into HTML.
 *
 * Reference: Issue #83 [W4-ML02]
 * @module components/CellCountingPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';
import { userFriendlyMLError } from '../services/mlErrors.js';
import { requestMLWorkerAccess } from '../services/mlWorkerAccess.js';
import { ExportService } from '../services/ExportService.js';

class CellCountingPanel {
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
        this.isCollapsed = (() => { try { return localStorage.getItem('varuna_panel_cellcounting_open') !== 'true'; } catch (_) { return true; } })();
        this.isCounting = false;
        this.stain = 'Ki67';
        this.result = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this.element = null;
        this._create();
    }

    setSlide(slideId) {
        this.slideId = slideId;
        this.result = null;
        this.isCounting = false;
        this._renderIdle();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'cell-counting-panel';

        // Collapsible header
        const header = document.createElement('div');
        header.className = 'cell-counting-panel__header';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'cell-counting-panel__title';
        titleSpan.textContent = 'Comptage cellulaire';

        const chevron = document.createElement('span');
        chevron.className = 'cell-counting-panel__chevron';
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

        // Body container
        this._body = document.createElement('div');
        this._body.className = 'cell-counting-panel__body';
        this.element.appendChild(this._body);

        this._renderIdle();
        this.container.appendChild(this.element);

        // Apply initial collapse state (collapsed by default, persisted via localStorage)
        this._body.style.display = this.isCollapsed ? 'none' : 'block';
        if (!this.isCollapsed) {
            chevron.textContent = '\u25BC';
        }
    }

    // ==========================================
    // STATE: IDLE
    // ==========================================

    _renderIdle() {
        // Safe: only static strings and this.stain (controlled enum value)
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'cell-counting-panel__section';

        // Stain selector
        const control = document.createElement('div');
        control.className = 'cell-counting-panel__control';
        const label = document.createElement('label');
        label.textContent = 'Coloration';
        control.appendChild(label);

        const select = document.createElement('select');
        select.className = 'cell-counting-panel__select';
        const stains = [
            { value: 'Ki67', label: 'Ki-67' },
            { value: 'HER2', label: 'HER2' },
            { value: 'PDL1', label: 'PD-L1' },
        ];
        for (const s of stains) {
            const opt = document.createElement('option');
            opt.value = s.value;
            opt.textContent = s.label;
            if (this.stain === s.value) opt.selected = true;
            select.appendChild(opt);
        }
        select.addEventListener('change', (e) => { this.stain = e.target.value; });
        control.appendChild(select);
        section.appendChild(control);

        // Scope toggle
        const scopeDiv = document.createElement('div');
        scopeDiv.className = 'cell-counting-panel__scope';
        const scopeLabel = document.createElement('label');
        scopeLabel.textContent = 'Portee';
        scopeDiv.appendChild(scopeLabel);

        const scopeRadios = document.createElement('div');
        scopeRadios.className = 'cell-counting-panel__scope-radios';

        for (const opt of [{ value: 'slide', text: 'Lame entiere' }, { value: 'viewport', text: 'Vue actuelle' }]) {
            const lbl = document.createElement('label');
            lbl.className = 'cell-counting-panel__scope-option';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'cellcount-scope';
            radio.value = opt.value;
            if (this.analysisScope === opt.value) radio.checked = true;
            radio.addEventListener('change', (e) => { this.analysisScope = e.target.value; });
            lbl.appendChild(radio);
            lbl.appendChild(document.createTextNode(` ${opt.text}`));
            scopeRadios.appendChild(lbl);
        }
        scopeDiv.appendChild(scopeRadios);
        section.appendChild(scopeDiv);

        // Count button
        const btn = document.createElement('button');
        btn.className = 'cell-counting-panel__btn cell-counting-panel__btn--primary';
        if (!this.slideId) btn.disabled = true;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="4 2"/>
        </svg> Compter les cellules`;
        btn.addEventListener('click', () => this._runCounting());
        section.appendChild(btn);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: LOADING
    // ==========================================

    _renderLoading() {
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'cell-counting-panel__section';

        const loading = document.createElement('div');
        loading.className = 'cell-counting-panel__loading';

        const spinner = document.createElement('div');
        spinner.className = 'cell-counting-panel__spinner';
        loading.appendChild(spinner);

        const text = document.createElement('span');
        text.textContent = 'Comptage en cours...';
        loading.appendChild(text);

        section.appendChild(loading);
        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: RESULTS
    // ==========================================

    _renderResults() {
        if (!this.result) return;

        const r = this.result;
        const positivePct = r.ratio * 100;
        const negativePct = 100 - positivePct;
        const timeStr = r.processing_time_ms < 1000
            ? `${Math.round(r.processing_time_ms)} ms`
            : `${(r.processing_time_ms / 1000).toFixed(1)} s`;

        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'cell-counting-panel__section';

        // Large percentage index
        const indexDiv = document.createElement('div');
        indexDiv.className = 'cell-counting-panel__index';
        const indexValue = document.createElement('span');
        indexValue.className = 'cell-counting-panel__index-value';
        indexValue.textContent = r.percentage;
        const indexLabel = document.createElement('span');
        indexLabel.className = 'cell-counting-panel__index-label';
        indexLabel.textContent = `Index ${this.stain === 'Ki67' ? 'Ki-67' : this.stain}`;
        indexDiv.appendChild(indexValue);
        indexDiv.appendChild(indexLabel);
        section.appendChild(indexDiv);

        // Ratio bar
        const bar = document.createElement('div');
        bar.className = 'cell-counting-panel__bar';
        const barPos = document.createElement('div');
        barPos.className = 'cell-counting-panel__bar-positive';
        barPos.style.width = `${positivePct}%`;
        const barNeg = document.createElement('div');
        barNeg.className = 'cell-counting-panel__bar-negative';
        barNeg.style.width = `${negativePct}%`;
        bar.appendChild(barPos);
        bar.appendChild(barNeg);
        section.appendChild(bar);

        // Three-column counts
        const counts = document.createElement('div');
        counts.className = 'cell-counting-panel__counts';

        const items = [
            { value: r.total_cells, label: 'Total', modifier: '' },
            { value: r.positive, label: 'Positives', modifier: '--positive' },
            { value: r.negative, label: 'N\u00e9gatives', modifier: '--negative' },
        ];
        for (const item of items) {
            const div = document.createElement('div');
            div.className = `cell-counting-panel__count-item${item.modifier ? ` cell-counting-panel__count-item${item.modifier}` : ''}`;
            const val = document.createElement('span');
            val.className = 'cell-counting-panel__count-value';
            val.textContent = String(item.value);
            const lbl = document.createElement('span');
            lbl.className = 'cell-counting-panel__count-label';
            lbl.textContent = item.label;
            div.appendChild(val);
            div.appendChild(lbl);
            counts.appendChild(div);
        }
        section.appendChild(counts);

        // Processing time
        const time = document.createElement('div');
        time.className = 'cell-counting-panel__time';
        time.textContent = `Temps de traitement : ${timeStr}`;
        section.appendChild(time);

        // Cell marker controls
        const markerControls = document.createElement('div');
        markerControls.className = 'cell-counting-panel__marker-controls';

        const checkLabel = document.createElement('label');
        checkLabel.className = 'cell-counting-panel__marker-toggle';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.addEventListener('change', () => {
            eventBus.emit(Events.CELL_MARKERS_TOGGLE, { visible: checkbox.checked });
        });
        checkLabel.appendChild(checkbox);
        const checkText = document.createTextNode(` ${i18nService.t('counting.showMarkers')}`);
        checkLabel.appendChild(checkText);
        markerControls.appendChild(checkLabel);

        const opacityLabel = document.createElement('label');
        opacityLabel.className = 'cell-counting-panel__marker-opacity';
        opacityLabel.textContent = i18nService.t('counting.opacity');
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.min = '0';
        slider.max = '100';
        slider.value = '70';
        slider.addEventListener('input', () => {
            eventBus.emit(Events.CELL_MARKERS_OPACITY, { opacity: parseInt(slider.value, 10) / 100 });
        });
        opacityLabel.appendChild(slider);
        markerControls.appendChild(opacityLabel);

        section.appendChild(markerControls);

        // Relaunch button
        const btn = document.createElement('button');
        btn.className = 'cell-counting-panel__btn cell-counting-panel__btn--secondary';
        btn.textContent = 'Relancer';
        btn.addEventListener('click', () => {
            this.result = null;
            this._renderIdle();
        });
        section.appendChild(btn);

        // Export CSV button
        const exportBtn = document.createElement('button');
        exportBtn.className = 'cell-counting-panel__btn cell-counting-panel__btn--export';
        exportBtn.textContent = i18nService.t('export.csv');
        exportBtn.addEventListener('click', () => this._exportCSV());
        section.appendChild(exportBtn);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: ERROR
    // ==========================================

    _renderError(message) {
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'cell-counting-panel__section';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'cell-counting-panel__error';

        const p = document.createElement('p');
        p.textContent = `Erreur : ${message}`;
        errorDiv.appendChild(p);

        const btn = document.createElement('button');
        btn.className = 'cell-counting-panel__btn cell-counting-panel__btn--secondary';
        btn.textContent = 'R\u00e9essayer';
        btn.addEventListener('click', () => this._renderIdle());
        errorDiv.appendChild(btn);

        section.appendChild(errorDiv);
        this._body.appendChild(section);
    }

    // ==========================================
    // COUNTING LOGIC
    // ==========================================

    async _runCounting() {
        if (!this.slideId || this.isCounting) return;

        const canProceed = await requestMLWorkerAccess('Comptage cellulaire');
        if (!canProceed) return;

        this.isCounting = true;
        this._renderLoading();
        eventBus.emit(Events.ML_WORKER_BUSY, { panel: 'cellCounting', label: 'Comptage cellulaire' });
        eventBus.emit(Events.CELL_COUNTING_START, { slideId: this.slideId, stain: this.stain });

        try {
            const countParams = { stain: this.stain };

            if (this.analysisScope === 'viewport' && this._viewerInstance) {
                const bounds = this._viewerInstance.getViewportPixelBounds();
                if (bounds) {
                    // Backend expects GeoJSON Polygon for count endpoint
                    const { x, y, width, height } = bounds;
                    countParams.region = {
                        type: 'Polygon',
                        coordinates: [[
                            [x, y], [x + width, y],
                            [x + width, y + height], [x, y + height],
                            [x, y],
                        ]],
                    };
                }
            }

            this.result = await apiService.countCells(this.slideId, { ...countParams, includePositions: true });

            this._renderResults();
            eventBus.emit(Events.CELL_COUNTING_COMPLETE, {
                slideId: this.slideId,
                result: this.result,
            });
        } catch (err) {
            console.error('[CellCountingPanel] Counting failed:', err);
            eventBus.emit(Events.CELL_COUNTING_ERROR, { error: err.message });
            this._renderError(userFriendlyMLError(err));
        } finally {
            this.isCounting = false;
            eventBus.emit(Events.ML_WORKER_FREE);
        }
    }

    // ==========================================
    // EXPORT
    // ==========================================

    _exportCSV() {
        if (!this.result) return;
        const r = this.result;

        const headers = ['metric', 'value'];
        const rows = [
            ['total_cells', r.total_cells],
            ['positive', r.positive],
            ['negative', r.negative],
            ['ratio', r.ratio],
            ['percentage', r.percentage],
        ];

        // Add cell positions if available
        if (r.cells && r.cells.length > 0) {
            rows.push(['', '']);  // Empty separator
            rows.push(['cell_x', 'cell_y', 'positive']);
            for (const cell of r.cells) {
                rows.push([cell.x, cell.y, cell.positive]);
            }
        }

        const csv = ExportService.toCSV(headers, rows);
        const slideName = this.slideId || 'slide';
        ExportService.download(csv, `${slideName}_counting_${ExportService.dateStamp()}.csv`);
    }

    // ==========================================
    // COLLAPSE / DESTROY
    // ==========================================

    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const body = this.element.querySelector('.cell-counting-panel__body');
        const chevron = this.element.querySelector('.cell-counting-panel__chevron');
        const header = this.element.querySelector('.cell-counting-panel__header');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
        try { localStorage.setItem('varuna_panel_cellcounting_open', String(!this.isCollapsed)); } catch (_) { /* noop */ }
    }

    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
        this.result = null;
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { CellCountingPanel };
export default CellCountingPanel;
