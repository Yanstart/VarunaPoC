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

class CellCountingPanel {
    /**
     * @param {HTMLElement} container
     * @param {Object} options
     * @param {string} options.slideId
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        // State
        this.isCollapsed = (() => { try { return localStorage.getItem('varuna_panel_cellcounting_open') !== 'true'; } catch (_) { return true; } })();
        this.isCounting = false;
        this.stain = 'Ki67';
        this.result = null;

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
        header.addEventListener('click', () => this._toggleCollapse());
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

        // Relaunch button
        const btn = document.createElement('button');
        btn.className = 'cell-counting-panel__btn cell-counting-panel__btn--secondary';
        btn.textContent = 'Relancer';
        btn.addEventListener('click', () => {
            this.result = null;
            this._renderIdle();
        });
        section.appendChild(btn);

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

        this.isCounting = true;
        this._renderLoading();
        eventBus.emit(Events.CELL_COUNTING_START, { slideId: this.slideId, stain: this.stain });

        try {
            this.result = await apiService.countCells(this.slideId, {
                stain: this.stain,
            });

            this._renderResults();
            eventBus.emit(Events.CELL_COUNTING_COMPLETE, {
                slideId: this.slideId,
                result: this.result,
            });
        } catch (err) {
            console.error('[CellCountingPanel] Counting failed:', err);
            eventBus.emit(Events.CELL_COUNTING_ERROR, { error: err.message });
            this._renderError(err.message);
        } finally {
            this.isCounting = false;
        }
    }

    // ==========================================
    // COLLAPSE / DESTROY
    // ==========================================

    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const body = this.element.querySelector('.cell-counting-panel__body');
        const chevron = this.element.querySelector('.cell-counting-panel__chevron');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        try { localStorage.setItem('varuna_panel_cellcounting_open', String(!this.isCollapsed)); } catch (_) { /* noop */ }
    }

    destroy() {
        this.result = null;
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}

export { CellCountingPanel };
export default CellCountingPanel;
