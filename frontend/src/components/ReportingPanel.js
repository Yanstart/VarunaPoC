/**
 * ReportingPanel - Annotation validation statistics and activity reporting
 *
 * Displays a collapsible sidebar panel showing:
 * - Validation breakdown (pending / validated / rejected) with progress bar
 * - AI correction stats
 * - Contributor table (annotations, validations, rejections per user)
 * - Activity timeline (last 20 events, scrollable)
 *
 * Data source: apiService.getAnnotationReport(slideId)
 * Refreshes on: ANNOTATIONS_LOADED, ANNOTATION_UPDATED
 *
 * @module components/ReportingPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';

class ReportingPanel {
    /**
     * @param {HTMLElement} container - Parent element
     * @param {Object} [options]
     * @param {string} [options.slideId]
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        /** @type {Object|null} Last fetched report */
        this._report = null;

        this.isCollapsed = (() => {
            try {
                return localStorage.getItem('varuna_panel_reporting_open') !== 'true';
            } catch (_) {
                return true;
            }
        })();

        this.isLoading = false;

        /** @type {Array<Function>} Unsubscribe functions */
        this._unsubscribers = [];

        this.element = null;
        this._create();
        this._setupEventListeners();
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    /**
     * Set the current slide and reload report data.
     * @param {string} slideId
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this._report = null;
        this._renderContent();
    }

    // ==========================================
    // DOM CONSTRUCTION
    // ==========================================

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'reporting-panel';

        // Header (collapsible trigger)
        const header = document.createElement('div');
        header.className = 'reporting-panel__header';
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');
        header.setAttribute('aria-expanded', String(!this.isCollapsed));

        const titleSpan = document.createElement('span');
        titleSpan.className = 'reporting-panel__title';
        titleSpan.textContent = 'Reporting';

        const chevron = document.createElement('span');
        chevron.className = 'reporting-panel__chevron';
        chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';

        header.appendChild(titleSpan);
        header.appendChild(chevron);

        header.addEventListener('click', () => this._toggleCollapse());
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this._toggleCollapse();
            }
        });

        this.element.appendChild(header);

        // Content area
        this._content = document.createElement('div');
        this._content.className = 'reporting-panel__content';
        this._content.style.display = this.isCollapsed ? 'none' : 'block';
        this.element.appendChild(this._content);

        this._renderContent();
        this.container.appendChild(this.element);
    }

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATIONS_LOADED, ({ slideId }) => {
                if (slideId === this.slideId) {
                    this._loadReport();
                }
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_UPDATED, () => {
                if (this.slideId) {
                    this._loadReport();
                }
            }),
        );
    }

    // ==========================================
    // DATA LOADING
    // ==========================================

    async _loadReport() {
        if (!this.slideId || this.isLoading) { return; }

        this.isLoading = true;
        this._renderContent();

        try {
            this._report = await apiService.getAnnotationReport(this.slideId);
        } catch (err) {
            console.warn('[ReportingPanel] Failed to load report:', err);
            this._report = null;
        } finally {
            this.isLoading = false;
            this._renderContent();
        }
    }

    // ==========================================
    // RENDERING
    // ==========================================

    _renderContent() {
        this._content.textContent = '';

        if (this.isLoading) {
            this._renderLoading();
            return;
        }

        if (!this._report) {
            this._renderEmpty();
            return;
        }

        this._renderStats();
        this._renderProgressBar();
        this._renderAISection();
        this._renderContributorsTable();
        this._renderTimeline();
    }

    _renderLoading() {
        const div = document.createElement('div');
        div.className = 'reporting-panel__loading';
        div.textContent = 'Chargement...';
        this._content.appendChild(div);
    }

    _renderEmpty() {
        const div = document.createElement('div');
        div.className = 'reporting-panel__empty';
        div.textContent = 'Aucune annotation pour cette lame.';
        this._content.appendChild(div);
    }

    _renderStats() {
        const validation = this._report.validation || {};
        const pending = validation.pending || 0;
        const validated = validation.validated || 0;
        const rejected = validation.rejected || 0;
        const total = this._report.total || 0;

        const section = document.createElement('div');
        section.className = 'reporting-panel__stats';

        const cards = [
            { label: 'En attente', value: pending, mod: 'pending' },
            { label: 'Valide', value: validated, mod: 'validated' },
            { label: 'Rejete', value: rejected, mod: 'rejected' },
        ];

        for (const card of cards) {
            const cardEl = document.createElement('div');
            cardEl.className = `reporting-panel__stat-card reporting-panel__stat-card--${card.mod}`;

            const valueEl = document.createElement('span');
            valueEl.className = 'reporting-panel__stat-value';
            valueEl.textContent = String(card.value);

            const labelEl = document.createElement('span');
            labelEl.className = 'reporting-panel__stat-label';
            labelEl.textContent = card.label;

            cardEl.appendChild(valueEl);
            cardEl.appendChild(labelEl);
            section.appendChild(cardEl);
        }

        const totalEl = document.createElement('div');
        totalEl.className = 'reporting-panel__stat-total';
        totalEl.textContent = `Total: ${total} annotations`;
        section.appendChild(totalEl);

        this._content.appendChild(section);
    }

    _renderProgressBar() {
        const validation = this._report.validation || {};
        const total = this._report.total || 0;

        const validated = validation.validated || 0;
        const rejected = validation.rejected || 0;
        const pending = total - validated - rejected;

        const validatedPct = total > 0 ? (validated / total) * 100 : 0;
        const rejectedPct = total > 0 ? (rejected / total) * 100 : 0;
        const pendingPct = total > 0 ? (pending / total) * 100 : 100;

        const wrapper = document.createElement('div');
        wrapper.className = 'reporting-panel__progress';

        const bar = document.createElement('div');
        bar.className = 'reporting-panel__progress-bar';
        bar.setAttribute('role', 'progressbar');
        bar.setAttribute('aria-label', 'Repartition des annotations');

        const segValidated = document.createElement('div');
        segValidated.className = 'reporting-panel__progress-seg reporting-panel__progress-seg--validated';
        segValidated.style.width = `${validatedPct}%`;
        segValidated.title = `Valide: ${validated}`;

        const segRejected = document.createElement('div');
        segRejected.className = 'reporting-panel__progress-seg reporting-panel__progress-seg--rejected';
        segRejected.style.width = `${rejectedPct}%`;
        segRejected.title = `Rejete: ${rejected}`;

        const segPending = document.createElement('div');
        segPending.className = 'reporting-panel__progress-seg reporting-panel__progress-seg--pending';
        segPending.style.width = `${pendingPct}%`;
        segPending.title = `En attente: ${pending}`;

        bar.appendChild(segValidated);
        bar.appendChild(segRejected);
        bar.appendChild(segPending);
        wrapper.appendChild(bar);
        this._content.appendChild(wrapper);
    }

    _renderAISection() {
        const ai = this._report.ai_corrections || {};
        const totalAI = ai.total_ai || 0;

        if (totalAI === 0) { return; }

        const aiValidated = ai.validated || 0;
        const pct = totalAI > 0 ? Math.round((aiValidated / totalAI) * 100) : 0;

        const section = document.createElement('div');
        section.className = 'reporting-panel__ai-section';

        const label = document.createElement('span');
        label.className = 'reporting-panel__ai-label';
        label.textContent = `Corrections IA\u00a0: ${aiValidated}/${totalAI} valides\u00a0(${pct}\u00a0%)`;

        section.appendChild(label);
        this._content.appendChild(section);
    }

    _renderContributorsTable() {
        const contributors = this._report.contributors || {};
        const names = Object.keys(contributors);

        if (names.length === 0) { return; }

        const section = document.createElement('div');
        section.className = 'reporting-panel__contributors';

        const titleEl = document.createElement('div');
        titleEl.className = 'reporting-panel__section-title';
        titleEl.textContent = 'Contributeurs';
        section.appendChild(titleEl);

        const table = document.createElement('table');
        table.className = 'reporting-panel__table';

        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const cols = ['Utilisateur', 'Annot.', 'Valid.', 'Rejet.'];
        for (const col of cols) {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        }
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        for (const name of names) {
            const stats = contributors[name] || {};
            const row = document.createElement('tr');

            const nameCell = document.createElement('td');
            nameCell.className = 'reporting-panel__table-name';
            nameCell.textContent = name;
            row.appendChild(nameCell);

            const annotCell = document.createElement('td');
            annotCell.textContent = String(stats.annotations || 0);
            row.appendChild(annotCell);

            const validCell = document.createElement('td');
            validCell.textContent = String(stats.validations || 0);
            row.appendChild(validCell);

            const rejCell = document.createElement('td');
            rejCell.textContent = String(stats.rejections || 0);
            row.appendChild(rejCell);

            tbody.appendChild(row);
        }
        table.appendChild(tbody);
        section.appendChild(table);
        this._content.appendChild(section);
    }

    _renderTimeline() {
        const timeline = this._report.timeline || [];

        if (timeline.length === 0) { return; }

        const section = document.createElement('div');
        section.className = 'reporting-panel__timeline-section';

        const titleEl = document.createElement('div');
        titleEl.className = 'reporting-panel__section-title';
        titleEl.textContent = 'Activite recente';
        section.appendChild(titleEl);

        const list = document.createElement('div');
        list.className = 'reporting-panel__timeline';

        // Show at most 20 items (most recent first)
        const items = timeline.slice(-20).reverse();

        for (const item of items) {
            const row = document.createElement('div');
            row.className = `reporting-panel__timeline-item reporting-panel__timeline-item--${item.status || 'pending'}`;

            const timeEl = document.createElement('span');
            timeEl.className = 'reporting-panel__timeline-time';
            timeEl.textContent = this._formatTime(item.created_at);

            const detailEl = document.createElement('span');
            detailEl.className = 'reporting-panel__timeline-detail';

            const author = item.created_by || 'anonyme';
            const type = item.type || '';
            const label = item.label || '';
            const status = item.status || '';

            // Safe text assembly — no user data injected via innerHTML
            const parts = [author, type, label, status].filter(Boolean).join(' \u2014 ');
            detailEl.textContent = parts;

            row.appendChild(timeEl);
            row.appendChild(detailEl);
            list.appendChild(row);
        }

        section.appendChild(list);
        this._content.appendChild(section);
    }

    // ==========================================
    // HELPERS
    // ==========================================

    /**
     * Format an ISO datetime string to a short relative or absolute time label.
     * @param {string} isoString
     * @returns {string}
     * @private
     */
    _formatTime(isoString) {
        if (!isoString) { return ''; }
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMin = Math.floor(diffMs / 60000);
            if (diffMin < 1) { return 'maintenant'; }
            if (diffMin < 60) { return `${diffMin}\u00a0min`; }
            const diffH = Math.floor(diffMin / 60);
            if (diffH < 24) { return `${diffH}\u00a0h`; }
            return date.toLocaleDateString('fr-BE', { day: '2-digit', month: '2-digit' });
        } catch (_) {
            return '';
        }
    }

    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const chevron = this.element.querySelector('.reporting-panel__chevron');
        const header = this.element.querySelector('.reporting-panel__header');
        this._content.style.display = this.isCollapsed ? 'none' : 'block';
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
        try {
            localStorage.setItem('varuna_panel_reporting_open', String(!this.isCollapsed));
        } catch (_) { /* noop */ }
    }

    // ==========================================
    // LIFECYCLE
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

export { ReportingPanel };
export default ReportingPanel;
