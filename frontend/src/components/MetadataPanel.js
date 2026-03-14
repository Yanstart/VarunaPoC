/**
 * MetadataPanel - Detailed slide metadata display
 *
 * Fetches from /slides/{id}/info + /slides/{id}/tags.
 * Displays in collapsible section with copy button.
 *
 * @module components/MetadataPanel
 */

import { apiService } from '../services/ApiService.js';
import { i18nService } from '../services/I18nService.js';
import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';

export class MetadataPanel {
    constructor(container, options = {}) {
        this.container = container;
        this.slideId = null;
        this._metadata = null;
        this._tags = null;

        this._unsubscribers = [];

        this.element = document.createElement('div');
        this.element.className = 'metadata-panel';
        this.container.appendChild(this.element);

        this._unsubscribers.push(
            eventBus.on(Events.LOCALE_CHANGED, () => this._render()),
        );
    }

    async setSlide(slideId) {
        this.slideId = slideId;
        this._metadata = null;
        this._tags = null;
        this._render();

        if (!slideId) return;

        try {
            const [info, tags] = await Promise.all([
                apiService.getSlideInfo(slideId),
                apiService.getSlideTags(slideId).catch(() => []),
            ]);
            this._metadata = info;
            this._tags = tags;
            this._render();
        } catch {
            // Info panel already shows basic data from Router
        }
    }

    _render() {
        this.element.textContent = '';
        const _t = (k, p) => i18nService.t(k, p);

        // Header
        const header = document.createElement('div');
        header.className = 'metadata-panel__header';
        header.textContent = _t('metadata.title');
        this.element.appendChild(header);

        if (!this._metadata) return;

        const body = document.createElement('dl');
        body.className = 'metadata-panel__body';

        const m = this._metadata;
        const [w, h] = m.dimensions || [0, 0];
        const mpp = m.mpp_x || m.properties?.['openslide.mpp-x'];
        const scanner = m.properties?.['openslide.vendor'] || null;
        const objective = m.properties?.['openslide.objective-power'] || null;

        this._addRow(body, _t('metadata.format'), m.format || '\u2014');
        this._addRow(body, _t('metadata.dimensions'),
            `${w.toLocaleString()} x ${h.toLocaleString()} px`);

        if (mpp) {
            const mmW = ((w * parseFloat(mpp)) / 1000).toFixed(1);
            const mmH = ((h * parseFloat(mpp)) / 1000).toFixed(1);
            this._addRow(body, '', `${mmW} x ${mmH} mm`);
            this._addRow(body, _t('metadata.mpp'), `${parseFloat(mpp).toFixed(3)} um/px`);
        }

        if (scanner) this._addRow(body, _t('metadata.scanner'), scanner);

        // Stain from tags
        const stainTag = Array.isArray(this._tags)
            ? this._tags.find(t => t.key === 'stain')
            : null;
        if (stainTag) this._addRow(body, _t('metadata.stain'), stainTag.value);

        if (objective) this._addRow(body, _t('metadata.objective'), `${objective}x`);

        this.element.appendChild(body);

        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'metadata-panel__copy';
        copyBtn.textContent = _t('metadata.copy');
        copyBtn.addEventListener('click', () => this._copyToClipboard());
        this.element.appendChild(copyBtn);
    }

    _addRow(dl, label, value) {
        if (label) {
            const dt = document.createElement('dt');
            dt.textContent = label;
            dl.appendChild(dt);
        }
        const dd = document.createElement('dd');
        dd.textContent = value;
        dl.appendChild(dd);
    }

    _copyToClipboard() {
        const rows = this.element.querySelectorAll('dt, dd');
        const text = Array.from(rows).map(el => el.textContent).join('\n');
        navigator.clipboard.writeText(text).then(() => {
            eventBus.emit(Events.TOAST_SHOW, {
                type: 'success',
                message: i18nService.t('metadata.copied'),
                duration: 2000,
            });
        }).catch(() => {
            // Clipboard API not available (non-HTTPS or unsupported)
        });
    }

    destroy() {
        this._unsubscribers.forEach(fn => fn());
        this._unsubscribers = [];
        if (this.element.parentNode) this.element.parentNode.removeChild(this.element);
    }
}
