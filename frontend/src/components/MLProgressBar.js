/**
 * MLProgressBar - Global ML operation progress indicator
 *
 * Thin animated bar at top of viewer area. Subscribes to
 * ML_WORKER_BUSY/FREE events and shows indeterminate progress
 * when any ML operation is running.
 *
 * @module components/MLProgressBar
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

export class MLProgressBar {
    /**
     * @param {HTMLElement} container - Parent element (viewer-area)
     */
    constructor(container) {
        this.container = container;
        this._activeCount = 0;
        this._hideTimer = null;
        this._unsubscribers = [];

        this._build();
        this._setupEventListeners();
    }

    _build() {
        this.el = document.createElement('div');
        this.el.className = 'ml-progress-bar';
        this.el.setAttribute('role', 'progressbar');
        this.el.setAttribute('aria-label', 'ML analysis progress');

        this._track = document.createElement('div');
        this._track.className = 'ml-progress-bar__track';
        this.el.appendChild(this._track);

        this._label = document.createElement('span');
        this._label.className = 'ml-progress-bar__label';
        this.el.appendChild(this._label);

        this.container.appendChild(this.el);
    }

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ML_WORKER_BUSY, () => {
                this._activeCount++;
                this._update();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ML_WORKER_FREE, () => {
                this._activeCount = Math.max(0, this._activeCount - 1);
                this._update();
            }),
        );
    }

    _update() {
        if (this._hideTimer) {
            clearTimeout(this._hideTimer);
            this._hideTimer = null;
        }

        if (this._activeCount > 0) {
            this.el.classList.remove('ml-progress-bar--done');
            this.el.classList.add('ml-progress-bar--active');
            const plural = this._activeCount > 1 ? 's' : '';
            this._label.textContent = `${this._activeCount} analyse${plural} en cours`;
        } else {
            // Brief green flash then hide
            this.el.classList.remove('ml-progress-bar--active');
            this.el.classList.add('ml-progress-bar--done');
            this._hideTimer = setTimeout(() => {
                this.el.classList.remove('ml-progress-bar--done');
                this._hideTimer = null;
            }, 800);
        }
    }

    destroy() {
        for (const unsub of this._unsubscribers) {
            if (typeof unsub === 'function') {
                unsub();
            }
        }
        this._unsubscribers = [];

        if (this._hideTimer) {
            clearTimeout(this._hideTimer);
            this._hideTimer = null;
        }

        if (this.el && this.el.parentNode) {
            this.el.parentNode.removeChild(this.el);
        }
        this.el = null;
    }
}
