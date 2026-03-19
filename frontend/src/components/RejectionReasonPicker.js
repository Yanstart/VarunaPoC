/**
 * RejectionReasonPicker - Inline micro-selector for rejection reasons
 *
 * Shows 4 predefined reason buttons + cancel. Used by DetectionPanel (Shift+X)
 * and AnnotationNotes (Reject button). Calls back with the selected reason.
 *
 * @module components/RejectionReasonPicker
 */

const REASONS = [
    { id: 'false_positive_artifact', label: 'Artefact', icon: '\u2702' },
    { id: 'false_positive_inflammation', label: 'Inflammation', icon: '\u2622' },
    { id: 'imprecise_contour', label: 'Contour', icon: '\u25EF' },
    { id: 'other', label: 'Autre', icon: '\u2026' },
];

/**
 * Show a rejection reason picker near a target element.
 * Returns a Promise that resolves with the selected reason or null (cancel).
 *
 * @param {HTMLElement} anchor - Element to position near
 * @param {Object} [options]
 * @param {string} [options.position='below'] - 'below' or 'above'
 * @returns {Promise<string|null>} Selected reason ID or null
 */
export function showRejectionReasonPicker(anchor, options = {}) {
    return new Promise((resolve) => {
        const el = document.createElement('div');
        el.className = 'rejection-picker';

        const cleanup = () => {
            el.remove();
            document.removeEventListener('keydown', onKey);
        };

        const onKey = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopPropagation();
                cleanup();
                resolve(null);
            }
        };
        document.addEventListener('keydown', onKey);

        for (const reason of REASONS) {
            const btn = document.createElement('button');
            btn.className = 'rejection-picker__btn';
            btn.title = reason.label;
            btn.type = 'button';

            const icon = document.createElement('span');
            icon.className = 'rejection-picker__icon';
            icon.textContent = reason.icon;
            btn.appendChild(icon);

            const label = document.createElement('span');
            label.className = 'rejection-picker__label';
            label.textContent = reason.label;
            btn.appendChild(label);

            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                cleanup();
                resolve(reason.id);
            });

            el.appendChild(btn);
        }

        // Position near anchor
        const rect = anchor.getBoundingClientRect();
        const topOrBottom = options.position === 'above'
            ? `bottom: ${window.innerHeight - rect.top + 4}px;`
            : `top: ${rect.bottom + 4}px;`;
        el.style.cssText = `position:fixed;z-index:500;left:${rect.left}px;${topOrBottom}`;

        document.body.appendChild(el);

        // Auto-close on outside click (delayed to avoid the triggering click)
        setTimeout(() => {
            const outsideClick = (e) => {
                if (!el.contains(e.target)) {
                    document.removeEventListener('click', outsideClick);
                    cleanup();
                    resolve(null);
                }
            };
            document.addEventListener('click', outsideClick);
        }, 50);
    });
}

export { REASONS };
