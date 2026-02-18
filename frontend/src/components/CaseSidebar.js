/**
 * Case Sidebar Component - Right sidebar in viewer listing sibling slides
 *
 * Shows all slides from the same case (parent folder) with active
 * indicator. Clicking a slide triggers onSlideSwitch callback for
 * rapid intra-case switching without returning to home.
 *
 * @module components/CaseSidebar
 */

/**
 * Extract stain type from a slide filename.
 * (Duplicated from CaseBrowser for standalone usage.)
 *
 * @param {string} slideName - Slide filename
 * @returns {string|null} Detected stain or null
 */
function extractStain(slideName) {
    const stem = slideName.replace(/\.[^.]+$/, '').toUpperCase();
    const stains = [
        'H&E', 'HE', 'CK5/6', 'CK5', 'CK7', 'CK20',
        'P63', 'P53', 'KI-67', 'KI67',
        'HER2', 'ER', 'PR', 'PD-L1',
        'CD3', 'CD20', 'CD45',
        'PAS', 'MASSON',
    ];
    return stains.find(s => stem.includes(s.replace(/[/-]/g, ''))) || null;
}

/**
 * Normalize stain name for display.
 *
 * @param {string} stain - Raw stain
 * @returns {string} Display name
 */
function normalizeStainDisplay(stain) {
    const map = {
        'HE': 'H&E',
        'KI67': 'Ki-67',
        'KI-67': 'Ki-67',
        'CK5/6': 'CK5/6',
        'PD-L1': 'PD-L1',
    };
    return map[stain] || stain;
}

/**
 * CaseSidebar - Class-based component for viewer right sidebar.
 */
export class CaseSidebar {
    /**
     * @param {HTMLElement} container - Parent element to mount into
     * @param {Object} [options={}]
     * @param {Function} [options.onSlideSwitch] - Callback(slide) when switching slide
     */
    constructor(container, options = {}) {
        this.container = container;
        this.onSlideSwitch = options.onSlideSwitch || null;

        this.casePath = null;
        this.slides = [];
        this.activeSlideId = null;

        this.element = document.createElement('div');
        this.element.className = 'case-sidebar';
        this.container.appendChild(this.element);

        this._render();
    }

    /**
     * Set case data and render the slide list.
     *
     * @param {string} casePath - Parent folder path
     * @param {Array} slides - Array of sibling slide objects
     * @param {string} activeSlideId - Currently active slide ID
     */
    setCase(casePath, slides, activeSlideId) {
        this.casePath = casePath;
        this.slides = slides || [];
        this.activeSlideId = activeSlideId;
        this._render();
    }

    /**
     * Update the active slide indicator without refetching.
     *
     * @param {string} slideId - New active slide ID
     */
    setActiveSlide(slideId) {
        this.activeSlideId = slideId;

        // Update DOM classes
        const items = this.element.querySelectorAll('.case-sidebar__item');
        items.forEach(item => {
            const itemId = item.dataset.slideId;
            if (itemId === slideId) {
                item.classList.add('is-active');
            } else {
                item.classList.remove('is-active');
            }
        });
    }

    /**
     * Render the sidebar content.
     * @private
     */
    _render() {
        this.element.textContent = '';

        if (!this.slides || this.slides.length === 0) {
            return;
        }

        // Header
        const header = document.createElement('div');
        header.className = 'case-sidebar__header';

        const title = document.createElement('div');
        title.className = 'case-sidebar__title';
        const caseName = this.casePath
            ? this.casePath.split('/').filter(Boolean).pop() || 'Cas'
            : 'Cas';
        title.textContent = `Cas: ${caseName}`;
        header.appendChild(title);

        const count = document.createElement('div');
        count.className = 'case-sidebar__count';
        count.textContent = `${this.slides.length} lame${this.slides.length !== 1 ? 's' : ''}`;
        header.appendChild(count);

        this.element.appendChild(header);

        // Slide list
        const list = document.createElement('div');
        list.className = 'case-sidebar__list';

        this.slides.forEach(slide => {
            const item = document.createElement('div');
            item.className = 'case-sidebar__item';
            item.dataset.slideId = slide.id;

            if (slide.id === this.activeSlideId) {
                item.classList.add('is-active');
            }

            // Dot indicator
            const dot = document.createElement('div');
            dot.className = 'case-sidebar__dot';
            item.appendChild(dot);

            // Info block
            const info = document.createElement('div');
            info.className = 'case-sidebar__item-info';

            const name = document.createElement('div');
            name.className = 'case-sidebar__name';
            name.textContent = slide.name;
            name.title = slide.name;
            info.appendChild(name);

            // Stain badge
            const stain = extractStain(slide.name);
            if (stain) {
                const stainBadge = document.createElement('span');
                stainBadge.className = 'case-sidebar__stain';
                stainBadge.textContent = normalizeStainDisplay(stain);
                info.appendChild(stainBadge);
            }

            item.appendChild(info);

            // Click to switch
            item.addEventListener('click', () => {
                if (slide.id !== this.activeSlideId && this.onSlideSwitch) {
                    this.onSlideSwitch(slide);
                }
            });

            list.appendChild(item);
        });

        this.element.appendChild(list);
    }

    /**
     * Destroy the sidebar and clean up DOM.
     */
    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.slides = [];
        this.onSlideSwitch = null;
    }
}
