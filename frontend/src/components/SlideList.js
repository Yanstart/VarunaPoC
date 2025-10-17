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
 * Crée liste de lames interactive.
 *
 * @param {Array} slides - Liste des lames (depuis API)
 * @param {Function} onClick - Callback appelé au clic: onClick(slide)
 * @returns {HTMLElement} Container avec liste <ul>
 *
 * Technical Notes:
 *   - Génère <ul> avec <li> pour chaque lame
 *   - Active state géré via classe CSS .active
 *   - Format badge coloré selon type (MRXS, BIF, TIF)
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
        item.innerHTML = `
            <div class="slide-name">${slide.name}</div>
            <span class="slide-format">${slide.format.toUpperCase()}</span>
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
