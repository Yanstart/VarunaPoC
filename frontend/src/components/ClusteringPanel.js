/**
 * ClusteringPanel - Morphological clustering visualization
 *
 * Workflow:
 * 1. User selects number of clusters (2-8)
 * 2. Clicks "Lancer le clustering"
 * 3. Loading state while backend runs clustering
 * 4. Results: color legend per cluster, visibility toggles, opacity slider
 *
 * Follows CellCountingPanel pattern: collapsible accordion, state machine.
 *
 * Note: innerHTML usage is safe here — only used to clear containers (innerHTML = '')
 * and for a static SVG icon with no user-supplied data interpolated.
 *
 * Reference: Wave 4 clustering feature
 * @module components/ClusteringPanel
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';
import { userFriendlyMLError } from '../services/mlErrors.js';
import { requestMLWorkerAccess } from '../services/mlWorkerAccess.js';

class ClusteringPanel {
    /**
     * @param {HTMLElement} container
     * @param {Object} options
     * @param {string} options.slideId
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        // State
        this.isCollapsed = (() => { try { return localStorage.getItem('varuna_panel_clustering_open') !== 'true'; } catch (_) { return true; } })();
        this.isClustering = false;
        this.nClusters = 4;
        this.result = null;

        // Per-cluster visibility (all visible by default)
        this._visibleClusters = new Set();
        this._opacity = 0.5;

        /** @type {Array<Function>} Unsubscribe functions for event listeners */
        this._unsubscribers = [];

        this.element = null;
        this._create();
    }

    setSlide(slideId) {
        this.slideId = slideId;
        this.result = null;
        this.isClustering = false;
        this._renderIdle();
    }

    _create() {
        this.element = document.createElement('div');
        this.element.className = 'clustering-panel';

        // Collapsible header
        const header = document.createElement('div');
        header.className = 'clustering-panel__header';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'clustering-panel__title';
        titleSpan.textContent = i18nService.t('clustering.title');

        const chevron = document.createElement('span');
        chevron.className = 'clustering-panel__chevron';
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
        this._body.className = 'clustering-panel__body';
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
        // Safe: clearing container, no user data
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'clustering-panel__section';

        // Cluster count selector
        const control = document.createElement('div');
        control.className = 'clustering-panel__control';
        const label = document.createElement('label');
        label.textContent = i18nService.t('clustering.numClusters');
        control.appendChild(label);

        const input = document.createElement('input');
        input.className = 'clustering-panel__select';
        input.type = 'number';
        input.min = '2';
        input.max = '8';
        input.value = String(this.nClusters);
        input.addEventListener('change', (e) => {
            const val = parseInt(e.target.value, 10);
            if (val >= 2 && val <= 8) {
                this.nClusters = val;
            } else {
                e.target.value = String(this.nClusters);
            }
        });
        control.appendChild(input);
        section.appendChild(control);

        // Run button — static SVG icon only, no user data in innerHTML
        const btn = document.createElement('button');
        btn.className = 'clustering-panel__btn clustering-panel__btn--primary';
        if (!this.slideId) btn.disabled = true;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="8" cy="8" r="3"/><circle cx="16" cy="16" r="3"/><circle cx="16" cy="8" r="2"/><circle cx="8" cy="16" r="2"/>
        </svg> Lancer le clustering`;
        btn.addEventListener('click', () => this._runClustering());
        section.appendChild(btn);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: LOADING
    // ==========================================

    _renderLoading() {
        // Safe: clearing container, no user data
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'clustering-panel__section';

        const loading = document.createElement('div');
        loading.className = 'clustering-panel__loading';

        const spinner = document.createElement('div');
        spinner.className = 'clustering-panel__spinner';
        loading.appendChild(spinner);

        const text = document.createElement('span');
        text.textContent = i18nService.t('clustering.running');
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
        // Safe: clearing container, no user data
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'clustering-panel__section';

        // Color legend
        const legend = document.createElement('div');
        legend.className = 'clustering-panel__legend';

        for (const cluster of r.clusters) {
            const item = document.createElement('div');
            item.className = 'clustering-panel__legend-item';

            // Visibility toggle checkbox
            const checkbox = document.createElement('input');
            checkbox.className = 'clustering-panel__legend-toggle';
            checkbox.type = 'checkbox';
            checkbox.checked = this._visibleClusters.has(cluster.id);
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this._visibleClusters.add(cluster.id);
                } else {
                    this._visibleClusters.delete(cluster.id);
                }
                eventBus.emit(Events.CLUSTERING_OVERLAY_TOGGLE, {
                    clusterId: cluster.id,
                    visible: e.target.checked,
                });
            });
            item.appendChild(checkbox);

            // Color dot
            const dot = document.createElement('span');
            dot.className = 'clustering-panel__color-dot';
            dot.style.backgroundColor = cluster.color;
            item.appendChild(dot);

            // Label
            const labelSpan = document.createElement('span');
            labelSpan.textContent = cluster.label;
            item.appendChild(labelSpan);

            // Tile count
            const count = document.createElement('span');
            count.className = 'clustering-panel__legend-count';
            count.textContent = cluster.tile_count + ' tuiles';
            item.appendChild(count);

            legend.appendChild(item);
        }
        section.appendChild(legend);

        // Opacity slider
        const opacitySection = document.createElement('div');
        opacitySection.className = 'clustering-panel__opacity';

        const opacityLabel = document.createElement('label');
        opacityLabel.textContent = i18nService.t('clustering.opacity');
        const opacityValue = document.createElement('span');
        opacityValue.className = 'clustering-panel__opacity-value';
        opacityValue.textContent = String(this._opacity);
        opacityLabel.appendChild(opacityValue);
        opacitySection.appendChild(opacityLabel);

        const slider = document.createElement('input');
        slider.className = 'clustering-panel__slider';
        slider.type = 'range';
        slider.min = '0';
        slider.max = '1';
        slider.step = '0.05';
        slider.value = String(this._opacity);
        slider.addEventListener('input', (e) => {
            this._opacity = parseFloat(e.target.value);
            opacityValue.textContent = String(this._opacity);
            eventBus.emit(Events.CLUSTERING_OVERLAY_OPACITY, {
                opacity: this._opacity,
            });
        });
        opacitySection.appendChild(slider);
        section.appendChild(opacitySection);

        // Relaunch button
        const btn = document.createElement('button');
        btn.className = 'clustering-panel__btn clustering-panel__btn--secondary';
        btn.textContent = i18nService.t('clustering.rerun');
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
        // Safe: clearing container, no user data
        this._body.innerHTML = '';

        const section = document.createElement('div');
        section.className = 'clustering-panel__section';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'clustering-panel__error';

        const p = document.createElement('p');
        p.textContent = i18nService.t('generic.error', { message });
        errorDiv.appendChild(p);

        const btn = document.createElement('button');
        btn.className = 'clustering-panel__btn clustering-panel__btn--secondary';
        btn.textContent = i18nService.t('clustering.retry');
        btn.addEventListener('click', () => this._renderIdle());
        errorDiv.appendChild(btn);

        section.appendChild(errorDiv);
        this._body.appendChild(section);
    }

    // ==========================================
    // CLUSTERING LOGIC
    // ==========================================

    async _runClustering() {
        if (!this.slideId || this.isClustering) return;

        const canProceed = await requestMLWorkerAccess('Clustering morphologique');
        if (!canProceed) return;

        this.isClustering = true;
        this._renderLoading();
        eventBus.emit(Events.ML_WORKER_BUSY, { panel: 'clustering', label: 'Clustering morphologique' });
        eventBus.emit(Events.CLUSTERING_START, { slideId: this.slideId, nClusters: this.nClusters });

        try {
            this.result = await apiService.clusterSlide(this.slideId, {
                n_clusters: this.nClusters,
            });

            // Initialize all clusters as visible
            this._visibleClusters.clear();
            if (this.result && this.result.clusters) {
                for (const cluster of this.result.clusters) {
                    this._visibleClusters.add(cluster.id);
                }
            }

            this._renderResults();
            eventBus.emit(Events.CLUSTERING_COMPLETE, {
                slideId: this.slideId,
                result: this.result,
            });
        } catch (err) {
            console.error('[ClusteringPanel] Clustering failed:', err);
            this._visibleClusters.clear();
            eventBus.emit(Events.CLUSTERING_ERROR, { error: err.message });
            this._renderError(userFriendlyMLError(err));
        } finally {
            this.isClustering = false;
            eventBus.emit(Events.ML_WORKER_FREE);
        }
    }

    // ==========================================
    // COLLAPSE / DESTROY
    // ==========================================

    _toggleCollapse() {
        this.isCollapsed = !this.isCollapsed;
        const body = this.element.querySelector('.clustering-panel__body');
        const chevron = this.element.querySelector('.clustering-panel__chevron');
        const header = this.element.querySelector('.clustering-panel__header');
        if (body) {
            body.style.display = this.isCollapsed ? 'none' : 'block';
        }
        if (chevron) {
            chevron.textContent = this.isCollapsed ? '\u25B6' : '\u25BC';
        }
        if (header) {
            header.setAttribute('aria-expanded', String(!this.isCollapsed));
        }
        try { localStorage.setItem('varuna_panel_clustering_open', String(!this.isCollapsed)); } catch (_) { /* noop */ }
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

export { ClusteringPanel };
export default ClusteringPanel;
