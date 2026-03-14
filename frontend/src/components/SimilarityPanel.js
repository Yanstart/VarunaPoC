/**
 * SimilarityPanel - Slide similarity search with thumbnail gallery
 *
 * Displays the K most similar slides to the current slide using
 * FAISS-based cosine similarity. Shows thumbnail grid with scores.
 *
 * UI Pattern:
 * - Accordion header "Lames similaires" with chevron (collapsed by default)
 * - "Rechercher" button to trigger API call
 * - Thumbnail grid with score badges (color-coded)
 *
 * @module components/SimilarityPanel
 */

import { apiService } from '../services/ApiService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

class SimilarityPanel {
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
        this.results = [];

        /** @type {HTMLElement|null} */
        this.element = null;
        /** @type {HTMLElement|null} */
        this._body = null;

        this._create();
    }

    /**
     * Set the current slide ID
     * @param {string} slideId
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this.results = [];
        this._renderIdle();
    }

    /**
     * Build the panel DOM
     * @private
     */
    _create() {
        this.element = document.createElement('div');
        this.element.className = 'similarity-panel';

        // Accordion header
        const header = document.createElement('div');
        header.className = 'similarity-panel__header similarity-panel__header--collapsible';

        const titleSpan = document.createElement('span');
        titleSpan.className = 'similarity-panel__title';
        titleSpan.textContent = 'Lames similaires';

        const chevron = document.createElement('span');
        chevron.className = 'similarity-panel__chevron';
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
        this._body.className = 'similarity-panel__body';
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
        const chevron = this.element.querySelector('.similarity-panel__chevron');
        const header = this.element.querySelector('.similarity-panel__header');
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
     * Render the idle state with search button
     * @private
     */
    _renderIdle() {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'similarity-panel__section';

        const desc = document.createElement('p');
        desc.className = 'similarity-panel__desc';
        desc.textContent = 'Recherche de lames similaires par analyse vectorielle.';
        section.appendChild(desc);

        const searchBtn = document.createElement('button');
        searchBtn.className = 'similarity-panel__btn similarity-panel__btn--primary';
        searchBtn.textContent = 'Rechercher';
        searchBtn.disabled = !this.slideId;
        searchBtn.addEventListener('click', () => this._loadSimilar());
        section.appendChild(searchBtn);

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
        section.className = 'similarity-panel__section';

        const loading = document.createElement('div');
        loading.className = 'similarity-panel__loading';

        const spinner = document.createElement('div');
        spinner.className = 'similarity-panel__spinner';

        const text = document.createElement('span');
        text.textContent = 'Recherche en cours\u2026';

        loading.appendChild(spinner);
        loading.appendChild(text);
        section.appendChild(loading);

        this._body.appendChild(section);
    }

    // ==========================================
    // STATE: RESULTS
    // ==========================================

    /**
     * Render search results as thumbnail grid
     * @private
     */
    _renderResults() {
        this._clearBody();

        const section = document.createElement('div');
        section.className = 'similarity-panel__section';

        // Summary
        const summary = document.createElement('div');
        summary.className = 'similarity-panel__summary';

        const countSpan = document.createElement('span');
        countSpan.className = 'similarity-panel__count';
        countSpan.textContent = String(this.results.length);

        const labelSpan = document.createElement('span');
        labelSpan.className = 'similarity-panel__count-label';
        labelSpan.textContent = this.results.length === 1 ? 'lame similaire' : 'lames similaires';

        summary.appendChild(countSpan);
        summary.appendChild(labelSpan);
        section.appendChild(summary);

        // Thumbnail grid
        const grid = document.createElement('div');
        grid.className = 'similarity-panel__grid';

        this.results.forEach((result) => {
            const card = this._createResultCard(result);
            grid.appendChild(card);
        });

        section.appendChild(grid);

        // Reload button
        const reloadBtn = document.createElement('button');
        reloadBtn.className = 'similarity-panel__btn similarity-panel__btn--secondary';
        reloadBtn.textContent = 'Rechercher';
        reloadBtn.addEventListener('click', () => this._loadSimilar());
        section.appendChild(reloadBtn);

        this._body.appendChild(section);
    }

    /**
     * Create a result card with thumbnail, name, and score
     * @param {Object} result - {slide_id, score, name, overview_url}
     * @returns {HTMLElement}
     * @private
     */
    _createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'similarity-panel__card';

        // Thumbnail image
        if (result.overview_url) {
            const img = document.createElement('img');
            img.className = 'similarity-panel__card-thumb';
            img.src = result.overview_url;
            img.alt = result.name || result.slide_id;
            img.width = 80;
            img.height = 60;
            card.appendChild(img);
        }

        // Name
        const name = document.createElement('div');
        name.className = 'similarity-panel__card-name';
        name.textContent = result.name || result.slide_id;
        name.title = result.name || result.slide_id;
        card.appendChild(name);

        // Score badge
        const badge = this._createScoreBadge(result.score);
        card.appendChild(badge);

        // Click to open in new tab
        card.addEventListener('click', () => {
            eventBus.emit(Events.CASE_SLIDE_SWITCH, { slideId: result.slide_id });
        });

        return card;
    }

    /**
     * Create a colored score badge
     * @param {number} score - Score value 0-1
     * @returns {HTMLElement}
     * @private
     */
    _createScoreBadge(score) {
        const badge = document.createElement('span');
        badge.className = 'similarity-panel__score-badge';

        const pct = Math.round(score * 100);
        badge.textContent = pct + '%';

        if (score >= 0.9) {
            badge.classList.add('similarity-panel__score-badge--high');
        } else if (score >= 0.7) {
            badge.classList.add('similarity-panel__score-badge--medium');
        } else {
            badge.classList.add('similarity-panel__score-badge--low');
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
        section.className = 'similarity-panel__section';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'similarity-panel__error';

        const errorText = document.createElement('p');
        errorText.textContent = 'Erreur : ' + message;
        errorDiv.appendChild(errorText);

        const retryBtn = document.createElement('button');
        retryBtn.className = 'similarity-panel__btn similarity-panel__btn--secondary';
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
     * Load similar slides from the API
     * @private
     */
    async _loadSimilar() {
        if (!this.slideId || this.isLoading) {return;}

        this.isLoading = true;
        this._renderLoading();

        try {
            const response = await apiService.getSimilarSlides(this.slideId, {
                topK: 5,
            });

            this.results = response.results || [];
            this._renderResults();
        } catch (err) {
            console.error('[SimilarityPanel] Failed to load similar slides:', err);
            this._renderError(err.message || 'Erreur inconnue');
        } finally {
            this.isLoading = false;
        }
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
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this._body = null;
        this.results = [];
    }
}

export { SimilarityPanel };
export default SimilarityPanel;
