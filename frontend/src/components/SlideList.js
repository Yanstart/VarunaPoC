/**
 * SlideList Component
 *
 * Affiche liste des lames avec sélection au clic.
 *
 * Design Pattern:
 *   - Component pattern simple (pas de framework)
 *   - Retourne DOM element prêt à insérer
 *   - Callback onClick pour gestion parent
 */

/**
 * Crée liste de lames interactive avec métadonnées enrichies.
 *
 * @param {Array} slides - Liste des lames (depuis API avec Phase 1.5 enrichments)
 * @param {Function} onClick - Callback appelé au clic: onClick(slide)
 * @returns {HTMLElement} Container avec liste <ul>
 *
 * Technical Notes:
 *   - Génère <ul> avec <li> pour chaque lame
 *   - Active state géré via classe CSS .active
 *   - Format badge coloré selon type (MRXS, BIF, TIF)
 *   - Phase 1.5: Affiche structure_type, fichiers joints, companion dirs
 */
export function createSlideList(slides, onClick) {
    const container = document.createElement('div');

    if (slides.length === 0) {
        container.innerHTML = '<p class="empty">No slides found in /Slides directory</p>';
        return container;
    }

    const list = document.createElement('ul');
    list.className = 'slide-list';

    slides.forEach(slide => {
        const item = document.createElement('li');
        item.className = 'slide-item';

        // Add unsupported class if slide is not supported
        if (slide.is_supported === false) {
            item.classList.add('slide-unsupported');
        }

        // Structure type icon
        const structureIcon = getStructureIcon(slide.structure_type);

        // Format badge with structure type
        const formatBadgeClass = slide.is_supported === false ? 'slide-format unsupported' : 'slide-format';
        const formatInfo = `
            <div class="slide-format-info">
                <span class="${formatBadgeClass}" title="${slide.is_supported === false ? 'Format détecté mais non supporté par cette version OpenSlide' : slide.format}">
                    ${slide.format}
                    ${slide.is_supported === false ? ' ⚠️' : ''}
                </span>
                <span class="slide-structure" title="${slide.structure_type}">
                    ${structureIcon}
                </span>
            </div>
        `;

        // File structure details
        let fileDetails = '';
        if (slide.has_joint_files) {
            fileDetails += `<span class="file-detail joint-files" title="Fichiers joints">📎 ${slide.joint_files_count}</span>`;
        }
        if (slide.has_companion_dirs) {
            fileDetails += `<span class="file-detail companion-dirs" title="Companion directories">📁 ${slide.companion_dirs_count}</span>`;
        }

        // Add unsupported notice
        if (slide.is_supported === false) {
            fileDetails += `<span class="file-detail unsupported-notice" title="${slide.notes}">⚠️ Non supporté</span>`;
        }

        // Build metadata section
        let metaInfo = '';
        if (slide.format_string) {
            metaInfo = `
                <div class="slide-body">
                    <div class="slide-meta">
                        <span class="slide-meta-label">Format:</span>
                        <span class="slide-meta-value"><code>${slide.format_string}</code></span>

                        <span class="slide-meta-label">Structure:</span>
                        <span class="slide-meta-value">${getStructureLabel(slide.structure_type)}</span>

                        ${slide.path ? `
                            <span class="slide-meta-label">Chemin:</span>
                            <span class="slide-meta-value" style="word-break: break-all; font-size: 10px;">${slide.path.replace(/\\/g, '/')}</span>
                        ` : ''}
                    </div>
                    ${fileDetails ? `<div class="slide-details">${fileDetails}</div>` : ''}
                </div>
            `;
        }

        item.innerHTML = `
            <div class="slide-header">
                <div class="slide-name" title="${slide.path}">${slide.name}</div>
                ${formatInfo}
            </div>
            ${metaInfo}
        `;

        // Click handler
        item.addEventListener('click', () => {
            // Remove active from all items
            document.querySelectorAll('.slide-item').forEach(el =>
                el.classList.remove('active'));

            // Add active to clicked item
            item.classList.add('active');

            // Trigger callback
            onClick(slide);
        });

        list.appendChild(item);
    });

    container.appendChild(list);
    return container;
}

/**
 * Retourne icône pour type de structure.
 *
 * @param {string} structureType - "single-file", "multi-file", "with-companion-dir"
 * @returns {string} Emoji représentant la structure
 */
function getStructureIcon(structureType) {
    switch (structureType) {
        case 'single-file':
            return '📄';
        case 'multi-file':
            return '📚';
        case 'with-companion-dir':
            return '🗂️';
        default:
            return '❓';
    }
}

/**
 * Retourne label descriptif pour type de structure.
 *
 * @param {string} structureType - "single-file", "multi-file", "with-companion-dir"
 * @returns {string} Label descriptif
 */
function getStructureLabel(structureType) {
    switch (structureType) {
        case 'single-file':
            return 'Fichier unique';
        case 'multi-file':
            return 'Multi-fichiers';
        case 'with-companion-dir':
            return 'Avec dossier companion';
        default:
            return 'Inconnu';
    }
}
