/**
 * FocusAssistPanel - IA Focus Assist with zone navigation
 *
 * Displays top-N zones of interest identified by the ML heatmap,
 * sorted by descending attention score. Clicking a zone navigates
 * the viewer to that region.
 *
 * UI Pattern:
 * - Accordion header "Zones d'interet IA" with chevron (collapsed by default)
 * - "Charger les zones" button to trigger API call
 * - Zone list with rank, score badge, and click-to-navigate
 *
 * @module components/FocusAssistPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { userFriendlyMLError } from '../services/mlErrors.js';
import { requestMLWorkerAccess } from '../services/mlWorkerAccess.js';

class FocusAssistPanel {
    /**
     * @param {HTMLElement} container - Parent element to append panel to
     * @param {Object} [options={}]
     * @param {string} [options.slideId] - Current slide ID
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        // State
        this.isCollapsed = true;
        this.isLoading = false;
        this.zones = [];
        this.activeZoneIndex = -1;
        this.topN = 10;
        this.threshold = 0.5;

        /** @type {HTMLElement|null} */
        this.element = null;
        /** @type {HTMLElement|null} */
        this._body = null;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this._create();
    }

    /**
     * Set the current slide ID
     * @param {string} slideId
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this.zones = [];
        this.activeZoneIndex = -1;
        this._renderIdle();
    }

    /**
     * Build the panel DOM
     * @private
     */
    _create() {
        this.element = document.createElement('div');
        this.element.className = 'focus-assist-panel';

        // Accordion header
        const header = document.createElement('div');
        header.className = 'focus-assist-panel__header focus-assist-panel__header--collapsible';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'focus-assist-panel__title';
        titleSpan.textContent = 'Zones d\u2019int\u00e9r\u00eat IA';

        const chevron = document.createElement('span');
        chevron.className = 'focus-assist-panel__chevron';
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
        this._body.className = 'focus-assist-panel__body';
        this.element.appendChild(this._body);

        this._renderIdle();
        this.container.appendChild(this.element);

        // Start collapsed
        this._body.style.display = 'none';
    }

    /**
     * Toggle collapse state
     * @private
     */
    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const chevron = this.element.querySelector('.focus-assist-panel__chevron');
        const header = this.element.querySelector('.focus-assist-panel__header');
        if (this._body) {
            this._body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
    }

    // ==========================================
    // STATE: IDLE
    // ==========================================

    /**
     * Render the idle state with load button
     * @private
     */
    _renderIdle() {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'focus-assist-panel__section';

        const desc = document.createElement('p');
        desc.className = 'focus-assist-panel__desc';
        desc.textContent = 'Identification automatique des r\u00e9gions d\u2019attention \u00e9lev\u00e9e par analyse IA.';
        section.appendChild(desc);

        const loadBtn = document.createElement('button');
        loadBtn.className = 'focus-assist-panel__btn focus-assist-panel__btn--primary';
        loadBtn.textContent = 'Charger les zones';
        loadBtn.disabled = !this.slideId;
        loadBtn.addEventListener('click', () => this._loadZones());
        section.appendChild(loadBtn);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: LOADING
    // ==========================================

    /**
     * Render the loading state
     * @private
     */
    _renderLoading() {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'focus-assist-panel__section';

        const loading = document.createElement('div');
        loading.className = 'focus-assist-panel__loading';

        const spinner = document.createElement('div');
        spinner.className = 'focus-assist-panel__spinner';

        const text = document.createElement('span');
        text.textContent = 'Analyse en cours\u2026';

        loading.appendChild(spinner);
        loading.appendChild(text);
        section.appendChild(loading);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: RESULTS
    // ==========================================

    /**
     * Render zone results
     * @private
     */
    _renderResults() {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'focus-assist-panel__section';

        // Summary
        const summary = document.createElement('div');
        summary.className = 'focus-assist-panel__summary';

        const countSpan = document.createElement('span');
        countSpan.className = 'focus-assist-panel__count';
        countSpan.textContent = String(this.zones.length);

        const labelSpan = document.createElement('span');
        labelSpan.className = 'focus-assist-panel__count-label';
        labelSpan.textContent = this.zones.length === 1 ? 'zone d\u2019int\u00e9r\u00eat' : 'zones d\u2019int\u00e9r\u00eat';

        summary.appendChild(countSpan);
        summary.appendChild(labelSpan);
        section.appendChild(summary);

        // Zone list
        const list = document.createElement('div');
        list.className = 'focus-assist-panel__list';

        this.zones.forEach((zone, index) => {
            const item = this._createZoneItem(zone, index);
            list.appendChild(item);
        });

        section.appendChild(list);

        // Reload button
        const reloadBtn = document.createElement('button');
        reloadBtn.className = 'focus-assist-panel__btn focus-assist-panel__btn--secondary';
        reloadBtn.textContent = 'Recharger';
        reloadBtn.addEventListener('click', () => this._loadZones());
        section.appendChild(reloadBtn);

        this._body.appendChild(section);
    }

    /**
     * Create a single zone item element
     * @param {Object} zone - Zone data {rank, score, centroid, bbox, area_px}
     * @param {number} index - Index in zones array
     * @returns {HTMLElement}
     * @private
     */
    _createZoneItem(zone, index) {
        const item = document.createElement('div');
        item.className = 'focus-assist-panel__zone-item';
        if (index === this.activeZoneIndex) {
            item.classList.add('is-active');
        }
        item.dataset.index = String(index);

        // Info container
        const info = document.createElement('div');
        info.className = 'focus-assist-panel__zone-info';

        // Label: "Zone {rank}"
        const label = document.createElement('span');
        label.className = 'focus-assist-panel__zone-label';
        label.textContent = 'Zone ' + zone.rank;

        // Score badge
        const badge = this._createScoreBadge(zone.score);

        info.appendChild(label);
        info.appendChild(badge);

        // Navigate button (arrow icon)
        const navBtn = document.createElement('button');
        navBtn.className = 'focus-assist-panel__zone-nav';
        navBtn.title = 'Naviguer vers cette zone';

        const arrow = document.createElement('span');
        arrow.textContent = '\u279C';
        navBtn.appendChild(arrow);

        navBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this._selectZone(index);
        });

        item.appendChild(info);
        item.appendChild(navBtn);

        // Click on item also navigates
        item.addEventListener('click', () => {
            this._selectZone(index);
        });

        return item;
    }

    /**
     * Create a colored score badge
     * @param {number} score - Score value 0-1
     * @returns {HTMLElement}
     * @private
     */
    _createScoreBadge(score) {
        const badge = document.createElement('span');
        badge.className = 'focus-assist-panel__score-badge';

        const pct = Math.round(score * 100);
        badge.textContent = pct + '%';

        if (score >= 0.8) {
            badge.classList.add('focus-assist-panel__score-badge--high');
        } else if (score >= 0.5) {
            badge.classList.add('focus-assist-panel__score-badge--medium');
        } else {
            badge.classList.add('focus-assist-panel__score-badge--low');
        }

        return badge;
    }

    // ==========================================
    // STATE: ERROR
    // ==========================================

    /**
     * Render error state
     * @param {string} message
     * @private
     */
    _renderError(message) {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'focus-assist-panel__section';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'focus-assist-panel__error';

        const errorText = document.createElement('p');
        errorText.textContent = 'Erreur : ' + message;
        errorDiv.appendChild(errorText);

        const retryBtn = document.createElement('button');
        retryBtn.className = 'focus-assist-panel__btn focus-assist-panel__btn--secondary';
        retryBtn.textContent = 'R\u00e9essayer';
        retryBtn.addEventListener('click', () => this._renderIdle());

        errorDiv.appendChild(retryBtn);
        section.appendChild(errorDiv);

        this._body.appendChild(section);
    }

    // ==========================================
    // LOGIC
    // ==========================================

    /**
     * Load focus zones from the API
     * @private
     */
    async _loadZones() {
        if (!this.slideId || this.isLoading) {return;}

        const canProceed = await requestMLWorkerAccess('Zones d\u2019int\u00e9r\u00eat IA');
        if (!canProceed) return;

        this.isLoading = true;
        this._renderLoading();
        eventBus.emit(Events.ML_WORKER_BUSY, { panel: 'focusAssist', label: 'Zones d\u2019int\u00e9r\u00eat IA' });

        try {
            const response = await apiService.getFocusZones(this.slideId, {
                topN: this.topN,
                threshold: this.threshold,
            });

            this.zones = response.zones || [];
            this.activeZoneIndex = -1;
            this._renderResults();
        } catch (err) {
            console.error('[FocusAssistPanel] Failed to load zones:', err);
            this._renderError(userFriendlyMLError(err));
        } finally {
            this.isLoading = false;
            eventBus.emit(Events.ML_WORKER_FREE);
        }
    }

    /**
     * Select a zone and emit navigation event
     * @param {number} index
     * @private
     */
    _selectZone(index) {
        if (index < 0 || index >= this.zones.length) {return;}

        this.activeZoneIndex = index;
        const zone = this.zones[index];

        // Update active state in DOM
        const items = this.element.querySelectorAll('.focus-assist-panel__zone-item');
        items.forEach((item, i) => {
            item.classList.toggle('is-active', i === index);
        });

        // Emit event for viewer navigation
        eventBus.emit('focus:zone-selected', {
            slideId: this.slideId,
            zone: zone,
            bbox: zone.bbox,
            centroid: zone.centroid,
            rank: zone.rank,
            score: zone.score,
        });
    }

    /**
     * Clear the body element
     * @private
     */
    _clearBody() {
        if (!this._body) {return;}
        while (this._body.firstChild) {
            this._body.removeChild(this._body.firstChild);
        }
    }

    /**
     * Destroy the panel and clean up
     */
    destroy() {
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this._body = null;
        this.zones = [];
    }
}

export { FocusAssistPanel };
export default FocusAssistPanel;
