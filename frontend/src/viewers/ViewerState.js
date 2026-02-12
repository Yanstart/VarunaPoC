/**
 * ViewerState - State Pattern implementation for viewer lifecycle
 *
 * Defines all possible states a viewer can be in and provides
 * validation for state transitions.
 *
 * @module viewers/ViewerState
 */

import { ViewerStates } from '../core/Constants.js';

/**
 * Valid state transitions map
 * Defines which states can transition to which other states
 * @type {Map<string, Set<string>>}
 */
const validTransitions = new Map([
    [ViewerStates.IDLE, new Set([ViewerStates.LOADING, ViewerStates.DESTROYING])],
    [ViewerStates.LOADING, new Set([ViewerStates.READY, ViewerStates.ERROR, ViewerStates.DESTROYING])],
    [ViewerStates.READY, new Set([ViewerStates.LOADING, ViewerStates.DESTROYING])],
    [ViewerStates.ERROR, new Set([ViewerStates.LOADING, ViewerStates.IDLE, ViewerStates.DESTROYING])],
    [ViewerStates.DESTROYING, new Set([])], // Terminal state
]);

/**
 * ViewerState class - manages state machine for a viewer
 *
 * @example
 * const state = new ViewerState();
 * state.onTransition((oldState, newState) => {
 *     console.log(`State changed: ${oldState} -> ${newState}`);
 * });
 * state.transitionTo(ViewerStates.LOADING);
 */
class ViewerState {
    /**
     * Create a new ViewerState instance
     * @param {string} [initialState=ViewerStates.IDLE] - Starting state
     */
    constructor(initialState = ViewerStates.IDLE) {
        /**
         * Current state
         * @type {string}
         * @private
         */
        this._currentState = initialState;

        /**
         * Previous state (for reference)
         * @type {string|null}
         * @private
         */
        this._previousState = null;

        /**
         * Transition callbacks
         * @type {Set<Function>}
         * @private
         */
        this._transitionCallbacks = new Set();

        /**
         * State entry callbacks (called when entering a specific state)
         * @type {Map<string, Set<Function>>}
         * @private
         */
        this._entryCallbacks = new Map();

        /**
         * State exit callbacks (called when leaving a specific state)
         * @type {Map<string, Set<Function>>}
         * @private
         */
        this._exitCallbacks = new Map();

        /**
         * Error information (when in ERROR state)
         * @type {Error|null}
         */
        this.error = null;

        /**
         * Timestamp of last state change
         * @type {number}
         */
        this.lastTransitionTime = Date.now();
    }

    /**
     * Get the current state
     * @returns {string} Current state value
     */
    get current() {
        return this._currentState;
    }

    /**
     * Get the previous state
     * @returns {string|null} Previous state value or null if no transition occurred
     */
    get previous() {
        return this._previousState;
    }

    /**
     * Check if viewer is in a specific state
     * @param {string} state - State to check
     * @returns {boolean} True if current state matches
     */
    is(state) {
        return this._currentState === state;
    }

    /**
     * Check if viewer is idle
     * @returns {boolean}
     */
    get isIdle() {
        return this.is(ViewerStates.IDLE);
    }

    /**
     * Check if viewer is loading
     * @returns {boolean}
     */
    get isLoading() {
        return this.is(ViewerStates.LOADING);
    }

    /**
     * Check if viewer is ready
     * @returns {boolean}
     */
    get isReady() {
        return this.is(ViewerStates.READY);
    }

    /**
     * Check if viewer has an error
     * @returns {boolean}
     */
    get isError() {
        return this.is(ViewerStates.ERROR);
    }

    /**
     * Check if viewer is being destroyed
     * @returns {boolean}
     */
    get isDestroying() {
        return this.is(ViewerStates.DESTROYING);
    }

    /**
     * Check if a transition to the given state is valid
     * @param {string} targetState - State to transition to
     * @returns {boolean} True if transition is valid
     */
    canTransitionTo(targetState) {
        const allowed = validTransitions.get(this._currentState);
        return allowed ? allowed.has(targetState) : false;
    }

    /**
     * Transition to a new state
     * @param {string} newState - Target state
     * @param {Object} [options={}] - Transition options
     * @param {Error} [options.error] - Error object (when transitioning to ERROR)
     * @param {boolean} [options.force=false] - Force transition even if invalid
     * @returns {boolean} True if transition succeeded
     * @throws {Error} If transition is invalid and not forced
     */
    transitionTo(newState, options = {}) {
        const { error = null, force = false } = options;

        // Check if transition is valid
        if (!force && !this.canTransitionTo(newState)) {
            const msg = `Invalid state transition: ${this._currentState} -> ${newState}`;
            console.error(`[ViewerState] ${msg}`);
            throw new Error(msg);
        }

        // Store previous state
        this._previousState = this._currentState;
        const oldState = this._currentState;

        // Call exit callbacks for current state
        this._invokeExitCallbacks(oldState);

        // Update state
        this._currentState = newState;
        this.lastTransitionTime = Date.now();

        // Handle error state
        if (newState === ViewerStates.ERROR) {
            this.error = error;
        } else {
            this.error = null;
        }

        // Call entry callbacks for new state
        this._invokeEntryCallbacks(newState);

        // Notify transition listeners
        this._transitionCallbacks.forEach(callback => {
            try {
                callback(oldState, newState, { error: this.error });
            } catch (e) {
                console.error('[ViewerState] Error in transition callback:', e);
            }
        });

        return true;
    }

    /**
     * Register a callback for any state transition
     * @param {Function} callback - Called with (oldState, newState, context)
     * @returns {Function} Unsubscribe function
     */
    onTransition(callback) {
        this._transitionCallbacks.add(callback);
        return () => this._transitionCallbacks.delete(callback);
    }

    /**
     * Register a callback for entering a specific state
     * @param {string} state - State to listen for
     * @param {Function} callback - Called when entering the state
     * @returns {Function} Unsubscribe function
     */
    onEnter(state, callback) {
        if (!this._entryCallbacks.has(state)) {
            this._entryCallbacks.set(state, new Set());
        }
        this._entryCallbacks.get(state).add(callback);
        return () => this._entryCallbacks.get(state)?.delete(callback);
    }

    /**
     * Register a callback for leaving a specific state
     * @param {string} state - State to listen for
     * @param {Function} callback - Called when leaving the state
     * @returns {Function} Unsubscribe function
     */
    onExit(state, callback) {
        if (!this._exitCallbacks.has(state)) {
            this._exitCallbacks.set(state, new Set());
        }
        this._exitCallbacks.get(state).add(callback);
        return () => this._exitCallbacks.get(state)?.delete(callback);
    }

    /**
     * Reset state to IDLE
     */
    reset() {
        if (this._currentState !== ViewerStates.IDLE) {
            this.transitionTo(ViewerStates.IDLE, { force: true });
        }
        this.error = null;
    }

    /**
     * Get state information as object
     * @returns {Object} State info
     */
    toJSON() {
        return {
            current: this._currentState,
            previous: this._previousState,
            isReady: this.isReady,
            hasError: this.isError,
            error: this.error ? this.error.message : null,
            lastTransitionTime: this.lastTransitionTime,
        };
    }

    /**
     * Invoke exit callbacks for a state
     * @param {string} state - State being exited
     * @private
     */
    _invokeExitCallbacks(state) {
        const callbacks = this._exitCallbacks.get(state);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(state);
                } catch (e) {
                    console.error(`[ViewerState] Error in exit callback for ${state}:`, e);
                }
            });
        }
    }

    /**
     * Invoke entry callbacks for a state
     * @param {string} state - State being entered
     * @private
     */
    _invokeEntryCallbacks(state) {
        const callbacks = this._entryCallbacks.get(state);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(state);
                } catch (e) {
                    console.error(`[ViewerState] Error in entry callback for ${state}:`, e);
                }
            });
        }
    }
}

export { ViewerState, ViewerStates };
export default ViewerState;
