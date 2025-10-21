# VarunaPoC - Architecture CSS Modulaire

Ce dossier contient les styles CSS organisés par responsabilité.

## Structure des fichiers

### `base.css`
Styles fondamentaux et utilitaires :
- Reset CSS
- Styles de base (body, #app)
- Scrollbar customisée
- Classes utilitaires (.loading, .error, .note, .empty)
- Animations (pulse)

### `home.css`
Styles de la page d'accueil :
- Layout page Home (.home-page, .home-header, .home-main)
- Toolbar avec recherche et bouton upload
- Stats et badges
- Section headers

### `slide-tiles.css`
Layout en tuiles pour la liste des lames :
- Grille responsive (grid auto-fill)
- Tuiles individuelles (.slide-item)
- Header des tuiles (nom, format, structure)
- Corps des tuiles (métadonnées détaillées)
- Badges et détails fichiers
- États (hover, active, unsupported)
- Responsive breakpoints

### `viewer.css`
Styles de la page de visualisation :
- Layout page Viewer (.viewer-page, .viewer-header, .viewer-main)
- Bouton retour
- Zone OpenSeadragon
- Panneau d'informations latéral

### `openseadragon.css`
Customisation OpenSeadragon :
- Style du navigator (mini-map)
- Boutons de contrôle
- Effets hover

## Import

Les fichiers sont importés dans `style.css` dans l'ordre suivant :
1. `base.css` - Fondations
2. `home.css` - Page d'accueil
3. `slide-tiles.css` - Tuiles de lames
4. `viewer.css` - Page viewer
5. `openseadragon.css` - Customisation OpenSeadragon

## Thème

- **Background principal**: `#000` (noir pur)
- **Background secondaire**: `#1a1a1a` (gris très foncé)
- **Background tertiaire**: `#2a2a2a` (gris foncé)
- **Bordures**: `#333` (gris moyen)
- **Texte principal**: `#e0e0e0` (gris clair)
- **Texte secondaire**: `#888` (gris)
- **Accent primaire**: `#4a9eff` (bleu)
- **Accent warning**: `#ff6b6b` (rouge)
- **Accent companion**: `#ffb800` (orange)

## Responsive

Les tuiles s'adaptent automatiquement :
- Mobile (< 768px): 1 colonne
- Desktop (default): grid auto-fill avec min 320px
- Large desktop (> 1400px): grid auto-fill avec min 350px

## Animations

- **pulse**: Animation de pulsation pour .loading (1.5s)
- **transitions**: 0.2s - 0.3s pour les effets hover
- **transform**: translateY pour les effets de levée des tuiles
