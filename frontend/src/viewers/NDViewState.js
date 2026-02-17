/**
 * NDViewState — N-dimensional view state for multi-dimensional imaging.
 * Supports Z-stacks, multi-channel fluorescence, and time-lapse.
 */
export class NDViewState {
    constructor(options = {}) {
        this._state = {
            x: options.x || 0,
            y: options.y || 0,
            z: options.z || 0,           // Z-stack slice
            c: options.c || 0,           // Channel index
            t: options.t || 0,           // Timepoint
            level: options.level || 0,   // Pyramid level
            zoom: options.zoom || 1.0,
        };

        this._dimensions = {
            z_max: options.z_max || 1,
            c_max: options.c_max || 1,
            t_max: options.t_max || 1,
            level_max: options.level_max || 1,
        };

        this._listeners = new Map();
    }

    // Getters
    get x() { return this._state.x; }
    get y() { return this._state.y; }
    get z() { return this._state.z; }
    get c() { return this._state.c; }
    get t() { return this._state.t; }
    get level() { return this._state.level; }
    get zoom() { return this._state.zoom; }

    // Navigation
    setZ(z) { this._update('z', Math.max(0, Math.min(z, this._dimensions.z_max - 1))); }
    setChannel(c) { this._update('c', Math.max(0, Math.min(c, this._dimensions.c_max - 1))); }
    setTimepoint(t) { this._update('t', Math.max(0, Math.min(t, this._dimensions.t_max - 1))); }
    setLevel(level) { this._update('level', Math.max(0, Math.min(level, this._dimensions.level_max - 1))); }
    setPosition(x, y) {
        this._state.x = x;
        this._state.y = y;
        this._emit('position', { x, y });
    }

    // Dimensions info
    getDimensions() { return { ...this._dimensions }; }

    // Serialization
    toJSON() { return { ...this._state }; }
    static fromJSON(json) { return new NDViewState(json); }

    // Events
    on(event, callback) {
        if (!this._listeners.has(event)) this._listeners.set(event, new Set());
        this._listeners.get(event).add(callback);
    }

    off(event, callback) {
        this._listeners.get(event)?.delete(callback);
    }

    _update(key, value) {
        const old = this._state[key];
        if (old === value) return;
        this._state[key] = value;
        this._emit(key, { old, new: value, state: this.toJSON() });
    }

    _emit(event, data) {
        this._listeners.get(event)?.forEach(cb => {
            try { cb(data); } catch (e) { console.error('NDViewState listener error:', e); }
        });
        // Also emit generic 'change' for any update
        if (event !== 'change') {
            this._listeners.get('change')?.forEach(cb => {
                try { cb({ dimension: event, ...data }); } catch (e) { /* */ }
            });
        }
    }

    destroy() {
        this._listeners.clear();
    }
}
