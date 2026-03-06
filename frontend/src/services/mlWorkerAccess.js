/**
 * ML Worker Access Control
 *
 * Manages access to the single ML worker like an OS scheduler:
 * - Tracks what's currently running (named jobs)
 * - When a new job is requested while worker is busy,
 *   offers the user a choice: cancel current + run new, or abort
 *
 * @module services/mlWorkerAccess
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { apiService } from './ApiService.js';

/** Current job label (null when idle) */
let currentJobLabel = null;

/** Whether the worker is busy */
let workerBusy = false;

// Track state from BUSY/FREE events
eventBus.on(Events.ML_WORKER_BUSY, (data) => {
    workerBusy = true;
    currentJobLabel = data?.label || 'Analyse IA';
});

eventBus.on(Events.ML_WORKER_FREE, () => {
    workerBusy = false;
    currentJobLabel = null;
});

/**
 * Request access to the ML worker before starting a new job.
 *
 * If the worker is free, returns true immediately.
 * If the worker is busy, shows a confirm dialog naming the current job
 * and offering to cancel it. If the user confirms, cancels the current
 * job and returns true. Otherwise returns false.
 *
 * @param {string} newJobLabel - Human-readable name for the new job
 * @returns {Promise<boolean>} true if the caller can proceed
 */
export async function requestMLWorkerAccess(newJobLabel) {
    if (!workerBusy) return true;

    const current = currentJobLabel || 'Analyse IA';

    const shouldCancel = confirm(
        `"${current}" est en cours.\n\nVoulez-vous l'annuler pour lancer "${newJobLabel}" ?`,
    );

    if (!shouldCancel) return false;

    try {
        await apiService.cancelML();
    } catch (e) {
        console.warn('[mlWorkerAccess] Cancel failed:', e);
    }

    eventBus.emit(Events.ML_WORKER_FREE);

    // Brief delay for worker restart
    await new Promise(resolve => setTimeout(resolve, 500));
    return true;
}

/**
 * Check if the ML worker is currently busy.
 * @returns {boolean}
 */
export function isMLWorkerBusy() {
    return workerBusy;
}

/**
 * Get the label of the currently running job.
 * @returns {string|null}
 */
export function getCurrentJobLabel() {
    return currentJobLabel;
}
