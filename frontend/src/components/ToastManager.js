/**
 * ToastManager - Global toast notification system
 *
 * Displays non-blocking notifications for ML errors, success events,
 * and programmatic TOAST_SHOW requests. Positioned bottom-right,
 * max 3 visible at a time.
 *
 * Singleton via getToastManager().
 *
 * @module components/ToastManager
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { userFriendlyMLError } from '../services/mlErrors.js';

// ---------------------------------------------------------------------------
// SVG icon constants (static strings, no user data — safe for innerHTML)
// Same pattern as MLTabsContainer, DetectionPanel, ClusteringPanel, etc.
// ---------------------------------------------------------------------------

const ICON_ERROR = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';

const ICON_WARNING = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';

const ICON_SUCCESS = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

const ICONS = {
    error: ICON_ERROR,
    warning: ICON_WARNING,
    success: ICON_SUCCESS,
};

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

const MAX_VISIBLE = 3;

const DEFAULT_DURATIONS = {
    success: 3000,
    warning: 5000,
    error: 0, // sticky — manual dismiss only
};

// ---------------------------------------------------------------------------
// ToastManager
// ---------------------------------------------------------------------------

let _instance = null;

class ToastManager {
    constructor() {
        /** @type {Map<number, {el: HTMLElement, timer: number|null}>} */
        this._toasts = new Map();
        this._nextId = 1;
        this._subs = [];

        // Build container
        this._container = document.createElement('div');
        this._container.className = 'toast-container';
        document.body.appendChild(this._container);

        this._setupEventListeners();
    }

    // ----- Event wiring -----

    _setupEventListeners() {
        // Direct TOAST_SHOW requests
        this._subs.push(
            eventBus.on(Events.TOAST_SHOW, (payload) => this.show(payload)),
        );

        // ML error events — translate via userFriendlyMLError
        const errorEvents = [
            Events.ML_PREDICTION_ERROR,
            Events.ML_HEATMAP_ERROR,
            Events.DETECTION_ERROR,
            Events.CELL_COUNTING_ERROR,
            Events.CLUSTERING_ERROR,
            Events.QUALITY_ERROR,
            Events.DRIFT_ERROR,
        ];

        for (const evt of errorEvents) {
            this._subs.push(
                eventBus.on(evt, (data) => {
                    const raw = data?.error || data?.message || evt;
                    this.show({ type: 'error', message: userFriendlyMLError(raw) });
                }),
            );
        }

        // Success events
        this._subs.push(
            eventBus.on(Events.ML_PREDICTION_COMPLETE, () => {
                this.show({ type: 'success', message: 'Analyse ML terminee' });
            }),
        );

        this._subs.push(
            eventBus.on(Events.DETECTION_COMPLETE, (data) => {
                const n = data?.numRegions ?? 0;
                this.show({
                    type: 'success',
                    message: `Detection terminee \u2014 ${n} region(s)`,
                });
            }),
        );
    }

    // ----- Public API -----

    /**
     * Show a toast notification.
     * @param {Object} opts
     * @param {'error'|'warning'|'success'} opts.type
     * @param {string} opts.message
     * @param {number} [opts.duration] - ms, 0 = sticky
     */
    show({ type = 'success', message = '', duration } = {}) {
        const id = this._nextId++;

        const effectiveDuration = duration ?? DEFAULT_DURATIONS[type] ?? 3000;

        // Evict oldest if at capacity
        while (this._toasts.size >= MAX_VISIBLE) {
            const oldestId = this._toasts.keys().next().value;
            this._dismiss(oldestId);
        }

        // Build toast element
        const el = document.createElement('div');
        el.className = `toast toast--${type}`;
        el.setAttribute('role', 'alert');

        // Icon — static SVG constant, no user data (same pattern as MLTabsContainer line 115)
        const iconSpan = document.createElement('span');
        iconSpan.className = 'toast__icon';
        const iconSvg = ICONS[type] || ICONS.success;
        iconSpan.innerHTML = iconSvg; // Safe: static SVG constant, no user data
        el.appendChild(iconSpan);

        // Message
        const msgSpan = document.createElement('span');
        msgSpan.className = 'toast__message';
        msgSpan.textContent = message;
        el.appendChild(msgSpan);

        // Dismiss button
        const btn = document.createElement('button');
        btn.className = 'toast__dismiss';
        btn.setAttribute('aria-label', 'Fermer');
        btn.textContent = '\u00d7';
        btn.addEventListener('click', () => this._dismiss(id));
        el.appendChild(btn);

        this._container.appendChild(el);

        // Trigger enter animation on next frame
        requestAnimationFrame(() => {
            el.classList.add('toast--visible');
        });

        // Auto-dismiss timer
        let timer = null;
        if (effectiveDuration > 0) {
            timer = setTimeout(() => this._dismiss(id), effectiveDuration);
        }

        this._toasts.set(id, { el, timer });
    }

    // ----- Internal -----

    /**
     * Dismiss a toast by id with exit animation.
     * @param {number} id
     */
    _dismiss(id) {
        const entry = this._toasts.get(id);
        if (!entry) {
            return;
        }

        if (entry.timer) {
            clearTimeout(entry.timer);
        }

        this._toasts.delete(id);

        const { el } = entry;
        el.classList.remove('toast--visible');
        el.classList.add('toast--exit');

        const removeFromDOM = () => {
            el.remove();
        };

        el.addEventListener('transitionend', removeFromDOM, { once: true });

        // Fallback: remove after 400ms in case transitionend doesn't fire
        setTimeout(removeFromDOM, 400);
    }

    // ----- Lifecycle -----

    destroy() {
        // Unsubscribe all events
        for (const unsub of this._subs) {
            if (typeof unsub === 'function') {
                unsub();
            }
        }
        this._subs = [];

        // Clear all timers
        for (const [, entry] of this._toasts) {
            if (entry.timer) {
                clearTimeout(entry.timer);
            }
        }
        this._toasts.clear();

        // Remove DOM
        if (this._container && this._container.parentNode) {
            this._container.remove();
        }

        _instance = null;
    }
}

/**
 * Get (or create) the singleton ToastManager instance.
 * @returns {ToastManager}
 */
export function getToastManager() {
    if (!_instance) {
        _instance = new ToastManager();
    }
    return _instance;
}
