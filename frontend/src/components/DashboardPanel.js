/**
 * DashboardPanel - AI Contribution Dashboard
 *
 * Motivational panel showing the pathologist's AI correction impact.
 * Displays how many AI detections they validated/rejected, encouraging
 * them to keep correcting because each correction improves the model.
 *
 * Data sources:
 * - Slide-level stats: loaded from backend report on ANNOTATIONS_LOADED
 * - Session counters: local, incremented via ANNOTATION_VALIDATED / ANNOTATION_REJECTED
 *
 * @module components/DashboardPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';

class DashboardPanel {
    /**
     * @param {HTMLElement} container - Parent element
     * @param {Object} [options]
     * @param {string} [options.slideId]
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        /** @type {boolean} */
        this.isCollapsed = (() => {
            try {
                return localStorage.getItem('varuna_panel_dashboard_open') !== 'true';
            } catch (_) {
                return true;
            }
        })();

        /** @type {{total_ai: number, validated: number, rejected: number}|null} */
        this._aiCorrections = null;

        /** @type {{pending: number, validated: number, rejected: number}|null} */
        this._validation = null;

        /** Session-level counters (reset on construction) */
        this._sessionValidated = 0;
        this._sessionRejected = 0;

        /** @type {Array<Function>} */
        this._unsubscribers = [];

        this.element = null;
        this._create();
        this._setupEventListeners();
    }

    // ==========================================
    // CONSTRUCTION
    // ==========================================

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'dashboard-panel';

        const header = document.createElement('div');
        header.className = 'dashboard-panel__header';
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');
        header.setAttribute('aria-expanded', String(!this.isCollapsed));

        const titleSpan = document.createElement('span');
        titleSpan.className = 'dashboard-panel__title';
        titleSpan.textContent = 'AI Contributions';

        const chevron = document.createElement('span');
        chevron.className = 'dashboard-panel__chevron';
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

        this._content = document.createElement('div');
        this._content.className = 'dashboard-panel__content';
        this._content.style.display = this.isCollapsed ? 'none' : 'block';

        this.element.appendChild(header);
        this.element.appendChild(this._content);
        this.container.appendChild(this.element);

        this._renderContent();
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATIONS_LOADED, ({ slideId }) => {
                if (slideId && slideId !== this.slideId) {
                    this.slideId = slideId;
                }
                this._loadReport();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_VALIDATED, () => {
                this._sessionValidated++;
                this._renderContent();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_REJECTED, () => {
                this._sessionRejected++;
                this._renderContent();
            }),
        );
    }

    // ==========================================
    // DATA LOADING
    // ==========================================

    async _loadReport() {
        if (!this.slideId) { return; }
        try {
            const report = await apiService.getAnnotationReport(this.slideId);
            this._aiCorrections = report.ai_corrections || null;
            this._validation = report.validation || null;
        } catch (err) {
            console.warn('[DashboardPanel] Could not load annotation report:', err);
            this._aiCorrections = null;
            this._validation = null;
        }
        this._renderContent();
    }

    // ==========================================
    // RENDERING
    // ==========================================

    _renderContent() {
        this._content.textContent = '';

        const totalAI = this._aiCorrections ? this._aiCorrections.total_ai : 0;
        const validated = this._aiCorrections ? this._aiCorrections.validated : 0;
        const rejected = this._aiCorrections ? this._aiCorrections.rejected : 0;
        const pending = this._validation ? this._validation.pending : 0;

        const corrected = validated + rejected;
        const accuracyPct = corrected > 0 ? Math.round((validated / corrected) * 100) : null;

        // Hero section
        const hero = document.createElement('div');
        hero.className = 'dashboard-panel__hero';

        const heroNumber = document.createElement('div');
        heroNumber.className = 'dashboard-panel__hero-number';
        heroNumber.textContent = String(totalAI);

        const heroSubtitle = document.createElement('div');
        heroSubtitle.className = 'dashboard-panel__hero-subtitle';

        const validatedSpan = document.createElement('span');
        validatedSpan.className = 'dashboard-panel__hero-validated';
        validatedSpan.textContent = String(validated) + ' validated';

        const sep1 = document.createTextNode(', ');

        const rejectedSpan = document.createElement('span');
        rejectedSpan.className = 'dashboard-panel__hero-rejected';
        rejectedSpan.textContent = String(rejected) + ' rejected';

        const sep2 = document.createTextNode(', ');

        const pendingText = document.createTextNode(String(pending) + ' pending');

        heroSubtitle.appendChild(validatedSpan);
        heroSubtitle.appendChild(sep1);
        heroSubtitle.appendChild(rejectedSpan);
        heroSubtitle.appendChild(sep2);
        heroSubtitle.appendChild(pendingText);

        const heroLabel = document.createElement('div');
        heroLabel.className = 'dashboard-panel__hero-label';
        heroLabel.textContent = 'AI detections on this slide';

        hero.appendChild(heroNumber);
        hero.appendChild(heroLabel);
        hero.appendChild(heroSubtitle);
        this._content.appendChild(hero);

        // Accuracy section
        const accuracySection = document.createElement('div');
        accuracySection.className = 'dashboard-panel__accuracy';

        const accuracyLabel = document.createElement('div');
        accuracyLabel.className = 'dashboard-panel__accuracy-label';
        accuracyLabel.textContent = 'AI accuracy after your corrections:';

        const accuracyValue = document.createElement('div');
        accuracyValue.className = 'dashboard-panel__accuracy-value';

        if (accuracyPct !== null) {
            accuracyValue.textContent = String(accuracyPct) + '%';
        } else {
            accuracyValue.textContent = '\u2014';
            accuracyValue.classList.add('dashboard-panel__accuracy-value--empty');
        }

        const barTrack = document.createElement('div');
        barTrack.className = 'dashboard-panel__accuracy-track';

        const barFill = document.createElement('div');
        barFill.className = 'dashboard-panel__accuracy-fill';
        barFill.style.width = (accuracyPct !== null ? accuracyPct : 0) + '%';

        barTrack.appendChild(barFill);
        accuracySection.appendChild(accuracyLabel);
        accuracySection.appendChild(accuracyValue);
        accuracySection.appendChild(barTrack);
        this._content.appendChild(accuracySection);

        // Session section
        const sessionSection = document.createElement('div');
        sessionSection.className = 'dashboard-panel__session';

        const sessionTitle = document.createElement('div');
        sessionTitle.className = 'dashboard-panel__session-title';
        sessionTitle.textContent = 'This session:';

        const sessionRows = document.createElement('div');
        sessionRows.className = 'dashboard-panel__session-rows';

        const rowValidated = document.createElement('div');
        rowValidated.className = 'dashboard-panel__session-row dashboard-panel__session-row--validated';

        const rowValidatedLabel = document.createElement('span');
        rowValidatedLabel.textContent = 'Validated:';

        const rowValidatedCount = document.createElement('span');
        rowValidatedCount.className = 'dashboard-panel__session-count dashboard-panel__session-count--validated';
        rowValidatedCount.textContent = String(this._sessionValidated);

        rowValidated.appendChild(rowValidatedLabel);
        rowValidated.appendChild(rowValidatedCount);

        const rowRejected = document.createElement('div');
        rowRejected.className = 'dashboard-panel__session-row dashboard-panel__session-row--rejected';

        const rowRejectedLabel = document.createElement('span');
        rowRejectedLabel.textContent = 'Rejected:';

        const rowRejectedCount = document.createElement('span');
        rowRejectedCount.className = 'dashboard-panel__session-count dashboard-panel__session-count--rejected';
        rowRejectedCount.textContent = String(this._sessionRejected);

        rowRejected.appendChild(rowRejectedLabel);
        rowRejected.appendChild(rowRejectedCount);

        sessionRows.appendChild(rowValidated);
        sessionRows.appendChild(rowRejected);

        sessionSection.appendChild(sessionTitle);
        sessionSection.appendChild(sessionRows);
        this._content.appendChild(sessionSection);

        // Motivation section
        const motivation = document.createElement('div');
        motivation.className = 'dashboard-panel__motivation';
        motivation.textContent = 'Each correction trains the AI for better diagnoses';
        this._content.appendChild(motivation);
    }

    // ==========================================
    // COLLAPSE
    // ==========================================

    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const chevron = this.element.querySelector('.dashboard-panel__chevron');
        const header = this.element.querySelector('.dashboard-panel__header');

        this._content.style.display = this.isCollapsed ? 'none' : 'block';

        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }

        try {
            localStorage.setItem('varuna_panel_dashboard_open', String(!this.isCollapsed));
        } catch (_) {
            // noop
        }
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    /**
     * Set the current slide and reload report data
     * @param {string} slideId
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this._aiCorrections = null;
        this._validation = null;
        this._renderContent();
        this._loadReport();
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

export { DashboardPanel };
export default DashboardPanel;
