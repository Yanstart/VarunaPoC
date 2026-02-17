/**
 * AutoTagBadge - Displays auto-detected slide tags
 *
 * Fetches ML-generated tags (organ, stain, tissue type) for a slide
 * and renders them as a discreet line of badges below the slide name.
 *
 * UI: "Prostate -- H&E -- Tissu tumoral"
 *
 * @module components/AutoTagBadge
 */

import { apiService } from '../services/ApiService.js';

class AutoTagBadge {
    /**
     * @param {HTMLElement} container - Parent element to append badge to
     * @param {Object} [options={}]
     * @param {string} [options.slideId] - Current slide ID
     */
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = options.slideId || null;

        // State
        this.tags = [];
        this.isLoading = false;

        /** @type {HTMLElement|null} */
        this.element = null;

        this._create();

        if (this.slideId) {
            this._fetchTags();
        }
    }

    /**
     * Set the current slide and fetch tags
     * @param {string} slideId
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this.tags = [];
        this._render();

        if (slideId) {
            this._fetchTags();
        }
    }

    /**
     * Build the badge container DOM
     * @private
     */
    _create() {
        this.element = document.createElement('div');
        this.element.className = 'auto-tag-badge';
        this._render();
        this.container.appendChild(this.element);
    }

    /**
     * Fetch tags from the API
     * @private
     */
    async _fetchTags() {
        if (!this.slideId || this.isLoading) { return; }

        this.isLoading = true;
        this.element.classList.add('auto-tag-badge--loading');

        try {
            const response = await apiService.getSlideTags(this.slideId);
            // Normalize response: accept {tags: [...]} or {organ, stain, tissue_type}
            if (Array.isArray(response.tags)) {
                this.tags = response.tags;
            } else {
                // Build tags from structured fields
                const tagList = [];
                if (response.organ) { tagList.push(response.organ); }
                if (response.stain) { tagList.push(response.stain); }
                if (response.tissue_type) { tagList.push(response.tissue_type); }
                if (response.diagnosis) { tagList.push(response.diagnosis); }
                this.tags = tagList;
            }
        } catch (err) {
            console.warn('[AutoTagBadge] Failed to fetch tags:', err);
            this.tags = [];
        } finally {
            this.isLoading = false;
            this.element.classList.remove('auto-tag-badge--loading');
            this._render();
        }
    }

    /**
     * Render the tag badges
     * @private
     */
    _render() {
        // Clear existing content
        while (this.element.firstChild) {
            this.element.removeChild(this.element.firstChild);
        }

        if (this.tags.length === 0) {
            return;
        }

        this.tags.forEach((tag, i) => {
            if (i > 0) {
                const sep = document.createElement('span');
                sep.className = 'auto-tag-badge__sep';
                sep.textContent = '\u2014';
                this.element.appendChild(sep);
            }

            const badge = document.createElement('span');
            badge.className = 'auto-tag-badge__tag';
            badge.textContent = tag;
            this.element.appendChild(badge);
        });
    }

    /**
     * Destroy the badge and clean up
     */
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
        this.tags = [];
    }
}

export { AutoTagBadge };
export default AutoTagBadge;
