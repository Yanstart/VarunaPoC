/**
 * SyncControls - UI controls for viewer synchronization and layout
 *
 * Provides a control bar with sync toggle and layout selector buttons.
 * Positioned at the bottom of the screen for easy access.
 *
 * @module components/SyncControls
 *
 * @example
 * const controls = new SyncControls(container, {
 *     onSyncToggle: (enabled) => console.log('Sync:', enabled),
 *     onLayoutChange: (preset) => console.log('Layout:', preset)
 * });
 */

import { CSSClasses, SyncConfig } from '../core/Constants.js';

/**
 * SyncControls class - Sync and layout control bar
 */
class SyncControls {
    /**
     * Create SyncControls
     * @param {HTMLElement} container - Container to append controls to
     * @param {Object} [options={}] - Configuration options
     * @param {Function} [options.onSyncToggle] - Callback when sync toggled
     * @param {Function} [options.onLayoutChange] - Callback when layout changed
     */
    constructor(container, options = {}) {
        /**
         * Options
         * @type {Object}
         */
        this.options = {
            onSyncToggle: null,
            onLayoutChange: null,
            onSyncModeChange: null,
            ...options,
        };

        /**
         * Container element
         * @type {HTMLElement}
         */
        this.container = container;

        /**
         * Controls element
         * @type {HTMLElement}
         */
        this.element = null;

        /**
         * Sync button element
         * @type {HTMLElement}
         */
        this.syncButton = null;

        /**
         * Sync mode selector element
         * @type {HTMLElement}
         */
        this.syncModeSelector = null;

        /**
         * Current sync state
         * @type {boolean}
         */
        this.syncEnabled = true;

        /**
         * Current sync mode
         * @type {string}
         */
        this.syncMode = SyncConfig.MODES.FULL;

        /**
         * Current layout
         * @type {{ columns: number, rows: number }}
         */
        this.currentLayout = { columns: 1, rows: 1 };

        // Keyboard shortcut handler reference
        this._boundKeyHandler = this._handleKeyDown.bind(this);
        document.addEventListener('keydown', this._boundKeyHandler);

        // Build the controls
        this._build();
    }

    /**
     * Build controls DOM structure
     * @private
     */
    _build() {
        this.element = document.createElement('div');
        this.element.className = 'sync-controls';

        // Layout selector
        const layoutSelector = this._buildLayoutSelector();

        // Sync button
        const syncSection = this._buildSyncSection();

        // Sync mode selector
        const syncModeSection = this._buildSyncModeSelector();

        // Status text
        const status = document.createElement('div');
        status.className = 'sync-status';
        status.id = 'sync-status';
        status.textContent = 'Sync : On';

        this.element.appendChild(layoutSelector);
        this.element.appendChild(syncSection);
        this.element.appendChild(syncModeSection);
        this.element.appendChild(status);

        // Add to container
        this.container.appendChild(this.element);

        // Apply initial sync state (default ON)
        this._updateSyncUI();
        if (this.syncEnabled && this.options.onSyncToggle) {
            this.options.onSyncToggle(true);
        }
    }

    /**
     * Build layout selector buttons
     * @returns {HTMLElement} Layout selector element
     * @private
     */
    _buildLayoutSelector() {
        const selector = document.createElement('div');
        selector.className = 'layout-selector';

        // Layout options to show
        const layouts = [
            { preset: 'SINGLE', cols: 1, rows: 1, title: 'Vue unique' },
            { preset: 'SIDE_BY_SIDE', cols: 2, rows: 1, title: 'C\u00f4te \u00e0 c\u00f4te' },
            { preset: 'GRID_2X2', cols: 2, rows: 2, title: 'Grille 2\u00d72' },
        ];

        layouts.forEach(layout => {
            const btn = document.createElement('button');
            btn.className = 'layout-option';
            btn.dataset.layout = `${layout.cols}x${layout.rows}`;
            btn.title = layout.title;

            // Create grid icon
            const icon = document.createElement('div');
            icon.className = 'layout-option-icon';

            for (let i = 0; i < layout.cols * layout.rows; i++) {
                const cell = document.createElement('div');
                cell.className = 'layout-cell';
                icon.appendChild(cell);
            }

            // Set grid style
            icon.style.gridTemplateColumns = `repeat(${layout.cols}, 8px)`;
            icon.style.gridTemplateRows = `repeat(${layout.rows}, 8px)`;

            btn.appendChild(icon);

            // Click handler
            btn.addEventListener('click', () => {
                this._selectLayout(layout.preset, layout.cols, layout.rows);
            });

            selector.appendChild(btn);
        });

        // Set initial active state
        selector.querySelector('[data-layout="1x1"]')?.classList.add(CSSClasses.ACTIVE);

        return selector;
    }

    /**
     * Build sync section with button and label
     * @returns {HTMLElement} Sync section element
     * @private
     */
    _buildSyncSection() {
        const section = document.createElement('div');
        section.style.display = 'flex';
        section.style.alignItems = 'center';
        section.style.gap = '8px';

        // Label
        const label = document.createElement('span');
        label.className = 'sync-label';
        label.textContent = 'Synchroniser';

        // Button
        this.syncButton = document.createElement('button');
        this.syncButton.className = CSSClasses.SYNC_BUTTON;
        this.syncButton.title = 'Activer/d\u00e9sactiver la synchronisation';
        this.syncButton.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
        `;

        this.syncButton.addEventListener('click', () => {
            this._toggleSync();
        });

        section.appendChild(label);
        section.appendChild(this.syncButton);

        return section;
    }

    /**
     * Build sync mode selector with toggle buttons
     * @returns {HTMLElement} Sync mode selector element
     * @private
     */
    _buildSyncModeSelector() {
        const section = document.createElement('div');
        section.className = 'sync-mode-selector';

        const modes = [
            { mode: SyncConfig.MODES.FULL, label: 'Complet', title: 'Synchronisation complete (S)' },
            { mode: SyncConfig.MODES.PAN_ONLY, label: 'Pan', title: 'Pan seulement (S)' },
            { mode: SyncConfig.MODES.ZOOM_ONLY, label: 'Zoom', title: 'Zoom seulement (S)' },
        ];

        modes.forEach(({ mode, label, title }) => {
            const btn = document.createElement('button');
            btn.className = 'sync-mode-btn';
            btn.dataset.syncMode = mode;
            btn.title = title;
            btn.textContent = label;

            if (mode === this.syncMode) {
                btn.classList.add(CSSClasses.ACTIVE);
            }

            btn.addEventListener('click', () => {
                this._selectSyncMode(mode);
            });

            section.appendChild(btn);
        });

        this.syncModeSelector = section;
        return section;
    }

    /**
     * Select a sync mode
     * @param {string} mode - Sync mode
     * @private
     */
    _selectSyncMode(mode) {
        if (!Object.values(SyncConfig.MODES).includes(mode)) {
            return;
        }

        this.syncMode = mode;

        // Update button active states
        const buttons = this.syncModeSelector.querySelectorAll('.sync-mode-btn');
        buttons.forEach(btn => {
            btn.classList.toggle(CSSClasses.ACTIVE, btn.dataset.syncMode === mode);
        });

        // Update status text
        this._updateSyncUI();

        // Callback
        if (this.options.onSyncModeChange) {
            this.options.onSyncModeChange(mode);
        }

        console.warn(`[SyncControls] Sync mode selected: ${mode}`);
    }

    /**
     * Cycle through sync modes via keyboard shortcut
     * @private
     */
    _cycleSyncMode() {
        const modeValues = Object.values(SyncConfig.MODES);
        const currentIndex = modeValues.indexOf(this.syncMode);
        const nextIndex = (currentIndex + 1) % modeValues.length;
        this._selectSyncMode(modeValues[nextIndex]);
    }

    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} e
     * @private
     */
    _handleKeyDown(e) {
        // 'S' key to cycle sync modes (when not typing in an input)
        if (e.key === 's' || e.key === 'S') {
            const tag = e.target.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
                return;
            }
            if (this.syncEnabled) {
                e.preventDefault();
                this._cycleSyncMode();
            }
        }
    }

    /**
     * Select a layout
     * @param {string} preset - Layout preset name
     * @param {number} cols - Columns
     * @param {number} rows - Rows
     * @private
     */
    _selectLayout(preset, cols, rows) {
        // Update active state
        const buttons = this.element.querySelectorAll('.layout-option');
        buttons.forEach(btn => btn.classList.remove(CSSClasses.ACTIVE));

        const activeBtn = this.element.querySelector(`[data-layout="${cols}x${rows}"]`);
        if (activeBtn) {
            activeBtn.classList.add(CSSClasses.ACTIVE);
        }

        // Update current layout
        this.currentLayout = { columns: cols, rows };

        // Callback
        if (this.options.onLayoutChange) {
            this.options.onLayoutChange(preset);
        }

        console.warn(`[SyncControls] Layout selected: ${preset}`);
    }

    /**
     * Toggle sync state
     * @private
     */
    _toggleSync() {
        this.syncEnabled = !this.syncEnabled;
        this._updateSyncUI();

        if (this.options.onSyncToggle) {
            this.options.onSyncToggle(this.syncEnabled);
        }

        console.warn(`[SyncControls] Sync toggled: ${this.syncEnabled}`);
    }

    /**
     * Update sync UI state
     * @private
     */
    _updateSyncUI() {
        const modeLabels = {
            [SyncConfig.MODES.FULL]: 'Complet',
            [SyncConfig.MODES.PAN_ONLY]: 'Pan',
            [SyncConfig.MODES.ZOOM_ONLY]: 'Zoom',
        };

        if (this.syncEnabled) {
            this.syncButton.classList.add(CSSClasses.ACTIVE);
            const modeLabel = modeLabels[this.syncMode] || this.syncMode;
            this.element.querySelector('#sync-status').textContent = `Sync : ${modeLabel}`;
        } else {
            this.syncButton.classList.remove(CSSClasses.ACTIVE);
            this.element.querySelector('#sync-status').textContent = 'Sync : Off';
        }

        // Show/hide mode selector based on sync state
        if (this.syncModeSelector) {
            this.syncModeSelector.style.display = this.syncEnabled ? 'flex' : 'none';
        }
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    /**
     * Set sync state
     * @param {boolean} enabled - Sync enabled state
     */
    setSyncState(enabled) {
        this.syncEnabled = enabled;
        this._updateSyncUI();
    }

    /**
     * Get sync state
     * @returns {boolean} Sync enabled state
     */
    getSyncState() {
        return this.syncEnabled;
    }

    /**
     * Get current sync mode
     * @returns {string} Current sync mode
     */
    getSyncMode() {
        return this.syncMode;
    }

    /**
     * Set sync mode
     * @param {string} mode - Sync mode
     */
    setSyncMode(mode) {
        this._selectSyncMode(mode);
    }

    /**
     * Update layout display
     * @param {number} cols - Columns
     * @param {number} rows - Rows
     */
    updateLayout(cols, rows) {
        this.currentLayout = { columns: cols, rows };

        // Update active button
        const buttons = this.element.querySelectorAll('.layout-option');
        buttons.forEach(btn => {
            const isActive = btn.dataset.layout === `${cols}x${rows}`;
            btn.classList.toggle(CSSClasses.ACTIVE, isActive);
        });
    }

    /**
     * Show controls
     */
    show() {
        this.element.style.display = 'flex';
    }

    /**
     * Hide controls
     */
    hide() {
        this.element.style.display = 'none';
    }

    /**
     * Destroy controls
     */
    destroy() {
        document.removeEventListener('keydown', this._boundKeyHandler);

        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }

        this.element = null;
        this.syncButton = null;
        this.syncModeSelector = null;
        this.container = null;
    }
}

export { SyncControls };
export default SyncControls;
