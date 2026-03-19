/**
 * AnnotationNotes - Popover showing metadata and notes for a selected annotation
 *
 * Appears in the bottom-left of the viewer area when an annotation is
 * selected. Displays type badge, confidence, status, label, authorship,
 * and a textarea for free-text notes.  Validate / Reject buttons are
 * shown only when the annotation status is "pending".
 *
 * All DOM creation uses safe methods (createElement / textContent).
 * innerHTML is never used.
 *
 * @module components/AnnotationNotes
 */

import { eventBus } from '../core/EventBus.js';
import { Events } from '../core/Constants.js';
import { annotationStore } from '../services/AnnotationStore.js';
import { i18nService } from '../services/I18nService.js';

export class AnnotationNotes {
    /**
     * @param {HTMLElement} container - Parent element (viewer-area)
     */
    constructor(container) {
        /** @type {HTMLElement} */
        this.container = container;

        /** @type {string|null} */
        this._currentId = null;

        /** @type {HTMLElement|null} */
        this.el = null;

        /** @type {Function[]} */
        this._unsubscribers = [];

        /** @type {boolean} Used to avoid redundant save on blur after Ctrl+Enter */
        this._saving = false;

        this._build();
        this._setupEventListeners();
    }

    // ==========================================
    // BUILD
    // ==========================================

    _build() {
        this.el = document.createElement('div');
        this.el.className = 'annotation-notes';
        this.el.setAttribute('role', 'complementary');
        this.el.setAttribute('aria-label', i18nService.t('panel.annotations'));

        // --- Header row (type badge + confidence + status) ---
        this._headerRow = document.createElement('div');
        this._headerRow.className = 'annotation-notes__header';

        this._typeBadge = document.createElement('span');
        this._typeBadge.className = 'annotation-notes__badge';

        this._confidenceEl = document.createElement('span');
        this._confidenceEl.className = 'annotation-notes__confidence';

        this._statusBadge = document.createElement('span');
        this._statusBadge.className = 'annotation-notes__status';

        this._headerRow.appendChild(this._typeBadge);
        this._headerRow.appendChild(this._confidenceEl);
        this._headerRow.appendChild(this._statusBadge);
        this.el.appendChild(this._headerRow);

        // --- Label row (color swatch + label name) ---
        this._labelRow = document.createElement('div');
        this._labelRow.className = 'annotation-notes__label';

        this._labelColor = document.createElement('span');
        this._labelColor.className = 'annotation-notes__label-color';

        this._labelName = document.createElement('span');
        this._labelName.className = 'annotation-notes__label-name';

        this._labelRow.appendChild(this._labelColor);
        this._labelRow.appendChild(this._labelName);
        this.el.appendChild(this._labelRow);

        // --- Info line (author / date / validator) ---
        this._infoEl = document.createElement('div');
        this._infoEl.className = 'annotation-notes__info';
        this.el.appendChild(this._infoEl);

        // --- Notes textarea ---
        this._textarea = document.createElement('textarea');
        this._textarea.className = 'annotation-notes__input';
        this._textarea.rows = 3;
        this._textarea.placeholder = i18nService.t('annotation.notesPlaceholder') || 'Notes...';
        this._textarea.setAttribute('aria-label', 'Notes');
        this.el.appendChild(this._textarea);

        // --- Action buttons (validate / reject) ---
        this._actionsRow = document.createElement('div');
        this._actionsRow.className = 'annotation-notes__actions';

        this._validateBtn = document.createElement('button');
        this._validateBtn.className = 'annotation-notes__btn annotation-notes__btn--validate';
        this._validateBtn.type = 'button';
        this._validateBtn.textContent = i18nService.t('btn.validate') || 'Valider';

        this._rejectBtn = document.createElement('button');
        this._rejectBtn.className = 'annotation-notes__btn annotation-notes__btn--reject';
        this._rejectBtn.type = 'button';
        this._rejectBtn.textContent = i18nService.t('btn.reject') || 'Rejeter';

        this._actionsRow.appendChild(this._validateBtn);
        this._actionsRow.appendChild(this._rejectBtn);
        this.el.appendChild(this._actionsRow);

        // Wire button and textarea interactions
        this._validateBtn.addEventListener('click', () => this._onValidate());
        this._rejectBtn.addEventListener('click', () => this._onReject());

        this._textarea.addEventListener('blur', () => this._onNotesSave());
        this._textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                this._onNotesSave();
            }
        });

        this.container.appendChild(this.el);
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

    _setupEventListeners() {
        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_SELECTED, ({ annotationId, annotation }) => {
                if (!annotationId || !annotation) {
                    this._hide();
                    return;
                }
                this._currentId = annotationId;
                this._render(annotation);
                this._show();
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.ANNOTATION_UPDATED, ({ annotation }) => {
                if (annotation && annotation.id === this._currentId) {
                    this._render(annotation);
                }
            }),
        );

        this._unsubscribers.push(
            eventBus.on(Events.LOCALE_CHANGED, () => {
                this._textarea.placeholder = i18nService.t('annotation.notesPlaceholder') || 'Notes...';
                this._validateBtn.textContent = i18nService.t('btn.validate') || 'Valider';
                this._rejectBtn.textContent = i18nService.t('btn.reject') || 'Rejeter';
                // Re-render current annotation if one is selected
                if (this._currentId) {
                    const annotation = annotationStore.annotations.get(this._currentId);
                    if (annotation) {
                        this._render(annotation);
                    }
                }
            }),
        );
    }

    // ==========================================
    // RENDER
    // ==========================================

    /**
     * Populate all fields from the annotation object.
     * @param {Object} annotation
     * @private
     */
    _render(annotation) {
        this._renderTypeBadge(annotation);
        this._renderConfidence(annotation);
        this._renderStatus(annotation);
        this._renderLabel(annotation);
        this._renderInfo(annotation);
        this._renderNotes(annotation);
        this._renderActions(annotation);
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderTypeBadge(annotation) {
        const type = annotation.annotation_type || 'manual';
        let label;
        let modClass;

        if (type === 'auto_ai_plus' || type === 'ai_plus') {
            label = 'AI+';
            modClass = 'annotation-notes__badge--ai-plus';
        } else if (type.startsWith('auto') || type === 'ai') {
            label = 'AI';
            modClass = 'annotation-notes__badge--ai';
        } else {
            label = i18nService.t('annotation.typeManual') || 'Manuel';
            modClass = 'annotation-notes__badge--manual';
        }

        this._typeBadge.textContent = label;
        this._typeBadge.className = `annotation-notes__badge ${modClass}`;
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderConfidence(annotation) {
        if (annotation.confidence !== null && annotation.confidence !== undefined) {
            const pct = Math.round(annotation.confidence * 100);
            this._confidenceEl.textContent = `${pct}%`;
            this._confidenceEl.style.display = '';
        } else {
            this._confidenceEl.textContent = '';
            this._confidenceEl.style.display = 'none';
        }
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderStatus(annotation) {
        const status = annotation.status || 'pending';
        let statusLabel;

        if (status === 'validated') {
            statusLabel = i18nService.t('annotation.statusValidated') || 'Valide';
        } else if (status === 'rejected') {
            statusLabel = i18nService.t('annotation.statusRejected') || 'Rejete';
        } else {
            statusLabel = i18nService.t('annotation.statusPending') || 'En attente';
        }

        this._statusBadge.textContent = statusLabel;
        this._statusBadge.className = `annotation-notes__status annotation-notes__status--${status}`;
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderLabel(annotation) {
        const label = annotation.label;
        if (label) {
            this._labelColor.style.background = label.color || '#888';
            this._labelName.textContent = label.name;
            this._labelRow.style.display = '';
        } else {
            this._labelRow.style.display = 'none';
        }
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderInfo(annotation) {
        // Build info text safely from parts — no user content concatenated into markup
        const parts = [];

        if (annotation.created_by) {
            parts.push(annotation.created_by);
        }

        if (annotation.created_at) {
            const date = new Date(annotation.created_at);
            const formatted = date.toLocaleDateString(undefined, {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
            });
            parts.push(formatted);
        }

        if (annotation.validated_by) {
            const prefix = i18nService.t('annotation.validatedBy') || 'Val. par';
            parts.push(`${prefix}: ${annotation.validated_by}`);
        }

        // Clear previous content
        while (this._infoEl.firstChild) {
            this._infoEl.removeChild(this._infoEl.firstChild);
        }

        const text = document.createTextNode(parts.join(' · '));
        this._infoEl.appendChild(text);
    }

    /**
     * @param {Object} annotation
     * @private
     */
    _renderNotes(annotation) {
        this._textarea.value = annotation.notes || '';
    }

    /**
     * Show validate/reject buttons only when status is pending.
     * @param {Object} annotation
     * @private
     */
    _renderActions(annotation) {
        const isPending = !annotation.status || annotation.status === 'pending';
        this._actionsRow.style.display = isPending ? '' : 'none';
    }

    // ==========================================
    // VISIBILITY
    // ==========================================

    _show() {
        this.el.classList.add('annotation-notes--visible');
    }

    _hide() {
        this.el.classList.remove('annotation-notes--visible');
        this._currentId = null;
    }

    // ==========================================
    // ACTIONS
    // ==========================================

    async _onValidate() {
        if (!this._currentId) {return;}
        const notes = this._textarea?.value?.trim() || null;
        await annotationStore.validateAnnotation(this._currentId, notes);
    }

    async _onReject() {
        if (!this._currentId) {return;}
        const notes = this._textarea?.value?.trim() || null;
        await annotationStore.rejectAnnotation(this._currentId, notes);
    }

    async _onNotesSave() {
        if (this._saving) {return;}
        await this._saveNotes();
    }

    /**
     * Persist the current textarea value to the backend.
     * @private
     */
    async _saveNotes() {
        if (!this._currentId) {return;}
        this._saving = true;
        try {
            const notes = this._textarea.value;
            await annotationStore.updateAnnotation(this._currentId, { notes });
        } finally {
            this._saving = false;
        }
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    destroy() {
        for (const unsub of this._unsubscribers) {
            if (typeof unsub === 'function') {unsub();}
        }
        this._unsubscribers = [];

        if (this.el && this.el.parentNode) {
            this.el.parentNode.removeChild(this.el);
        }
        this.el = null;
        this._currentId = null;
    }
}
