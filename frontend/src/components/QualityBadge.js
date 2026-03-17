/**
 * QualityBadge - Displays slide quality assessment as a badge
 *
 * Shows a colored dot + label in the viewer header.
 * On hover/click: tooltip with artifact details.
 *
 * @module components/QualityBadge
 */

import { apiService } from '../services/ApiService.js';
import { Events } from '../core/Constants.js';
import { i18nService } from '../services/I18nService.js';

/**
 * QualityBadge component
 */
export class QualityBadge {
    /**
     * @param {string} slideId - Slide identifier
     * @param {import('../core/EventBus.js').default} [eventBus] - Optional event bus
     */
    constructor(slideId, eventBus = null) {
        /** @type {string|null} */
        this.slideId = slideId;

        /** @type {import('../core/EventBus.js').default|null} */
        this.eventBus = eventBus;

        /** @type {HTMLElement|null} */
        this.el = null;

        /** @type {HTMLElement|null} */
        this._tooltip = null;

        /** @type {Object|null} */
        this._data = null;

        /** @type {boolean} */
        this._destroyed = false;

        this._build();
    }

    /**
     * Build the badge DOM structure.
     * @private
     */
    _build() {
        this.el = document.createElement('span');
        this.el.className = 'quality-badge';
        this.el.setAttribute('role', 'status');
        this.el.setAttribute('aria-label', i18nService.t('quality.evaluating'));

        // Dot indicator
        this._dot = document.createElement('span');
        this._dot.className = 'quality-badge__dot';
        this.el.appendChild(this._dot);

        // Text label
        this._label = document.createElement('span');
        this._label.className = 'quality-badge__label';
        this._label.textContent = i18nService.t('quality.clickToEvaluate');
        this.el.appendChild(this._label);

        // Tooltip (hidden by default)
        this._tooltip = document.createElement('div');
        this._tooltip.className = 'quality-badge__tooltip';
        this._tooltip.style.display = 'none';
        this.el.appendChild(this._tooltip);

        // Event listeners for tooltip
        this._onMouseEnter = () => this._showTooltip();
        this._onMouseLeave = () => this._hideTooltip();
        this._onClick = () => this._toggleTooltip();

        this.el.addEventListener('mouseenter', this._onMouseEnter);
        this.el.addEventListener('mouseleave', this._onMouseLeave);
        this.el.addEventListener('click', this._onClick);
    }

    /**
     * Fetch quality data from API.
     * @param {string} slideId
     * @private
     */
    async _fetchQuality(slideId) {
        if (this._destroyed || this._loading) return;

        this._loading = true;
        this._label.textContent = i18nService.t('quality.evaluating');

        if (this.eventBus) {
            this.eventBus.emit(Events.QUALITY_LOADING, { slideId });
        }

        try {
            const data = await apiService.getSlideQuality(slideId);
            if (this._destroyed || this.slideId !== slideId) return;

            this._data = data;
            this._render(data);

            // Warn on low quality
            if (data.overall_score < 0.5 && this.eventBus) {
                this.eventBus.emit(Events.TOAST_SHOW, {
                    type: 'warning',
                    message: i18nService.t('quality.lowWarning', { pct: Math.round(data.overall_score * 100) }),
                });
            }

            if (this.eventBus) {
                this.eventBus.emit(Events.QUALITY_READY, { slideId, data });
            }
        } catch (err) {
            if (this._destroyed) return;

            this._renderError();

            if (this.eventBus) {
                this.eventBus.emit(Events.QUALITY_ERROR, { slideId, error: err });
            }
        } finally {
            this._loading = false;
        }
    }

    /**
     * Render badge with quality data.
     * @param {Object} data - Quality response
     * @private
     */
    _render(data) {
        const { overall_score, quality_label, artifacts, recommendation } = data;
        const pct = Math.round(overall_score * 100);

        // Determine variant
        let variant;
        if (overall_score > 0.8) {
            variant = 'good';
        } else if (overall_score >= 0.6) {
            variant = 'acceptable';
        } else {
            variant = 'poor';
        }

        // Update badge class
        this.el.className = `quality-badge quality-badge--${variant}`;
        this.el.setAttribute('aria-label', i18nService.t('quality.label', { label: quality_label, pct }));

        // Update dot
        this._dot.className = `quality-badge__dot quality-badge__dot--${variant}`;

        // Update label text using textContent (safe from XSS)
        this._label.textContent = i18nService.t('quality.label', { label: quality_label, pct });

        // Build tooltip content using DOM methods
        this._buildTooltipContent(data);
    }

    /**
     * Build tooltip content using safe DOM methods.
     * @param {Object} data
     * @private
     */
    _buildTooltipContent(data) {
        const { overall_score, quality_label, artifacts, recommendation, processing_time_ms } = data;
        const pct = Math.round(overall_score * 100);

        // Clear existing content
        while (this._tooltip.firstChild) {
            this._tooltip.removeChild(this._tooltip.firstChild);
        }

        // Title
        const title = document.createElement('div');
        title.className = 'quality-badge__tooltip-title';
        title.textContent = i18nService.t('quality.label', { label: quality_label, pct });
        this._tooltip.appendChild(title);

        // Recommendation
        const rec = document.createElement('div');
        rec.className = 'quality-badge__tooltip-rec';
        rec.textContent = recommendation;
        this._tooltip.appendChild(rec);

        // Artifacts list
        if (artifacts && artifacts.length > 0) {
            const artifactTitle = document.createElement('div');
            artifactTitle.className = 'quality-badge__tooltip-section';
            artifactTitle.textContent = i18nService.t('quality.artifacts', { count: artifacts.length });
            this._tooltip.appendChild(artifactTitle);

            const list = document.createElement('ul');
            list.className = 'quality-badge__tooltip-list';

            for (const art of artifacts) {
                const li = document.createElement('li');
                li.textContent = `${art.type} - ${art.severity} (${art.area_percent}%)`;
                list.appendChild(li);
            }

            this._tooltip.appendChild(list);
        }

        // Processing time
        if (processing_time_ms !== undefined) {
            const timeEl = document.createElement('div');
            timeEl.className = 'quality-badge__tooltip-time';
            timeEl.textContent = i18nService.t('quality.processingTime', { ms: Math.round(processing_time_ms) });
            this._tooltip.appendChild(timeEl);
        }
    }

    /**
     * Render error state.
     * @private
     */
    _renderError() {
        this.el.className = 'quality-badge quality-badge--poor';
        this._dot.className = 'quality-badge__dot quality-badge__dot--poor';
        this._label.textContent = i18nService.t('quality.error');
        this.el.setAttribute('aria-label', i18nService.t('quality.evaluationFailed'));
    }

    /**
     * Show the tooltip.
     * @private
     */
    _showTooltip() {
        if (this._tooltip && this._data) {
            this._tooltip.style.display = 'block';
        }
    }

    /**
     * Hide the tooltip.
     * @private
     */
    _hideTooltip() {
        if (this._tooltip) {
            this._tooltip.style.display = 'none';
        }
    }

    /**
     * Toggle tooltip visibility.
     * @private
     */
    _toggleTooltip() {
        // First click with no data: trigger manual quality assessment
        if (!this._data && this.slideId && !this._loading) {
            this._fetchQuality(this.slideId);
            return;
        }

        if (this._tooltip && this._data) {
            const isVisible = this._tooltip.style.display !== 'none';
            this._tooltip.style.display = isVisible ? 'none' : 'block';
        }
    }

    /**
     * Switch to a different slide.
     * @param {string} slideId - New slide ID
     */
    setSlide(slideId) {
        this.slideId = slideId;
        this._data = null;
        this._hideTooltip();

        // Reset to loading state
        this.el.className = 'quality-badge';
        this._dot.className = 'quality-badge__dot';
        this._label.textContent = i18nService.t('quality.evaluating');

        // Auto-trigger quality assessment
        if (slideId) {
            this._fetchQuality(slideId);
        }
    }

    /**
     * Clean up and remove the badge.
     */
    destroy() {
        this._destroyed = true;

        if (this.el) {
            this.el.removeEventListener('mouseenter', this._onMouseEnter);
            this.el.removeEventListener('mouseleave', this._onMouseLeave);
            this.el.removeEventListener('click', this._onClick);

            if (this.el.parentNode) {
                this.el.parentNode.removeChild(this.el);
            }
        }

        this.el = null;
        this._tooltip = null;
        this._data = null;
        this.eventBus = null;
    }
}

export default QualityBadge;
