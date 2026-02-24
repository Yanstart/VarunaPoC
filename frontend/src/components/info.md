# components

## But
Regrouper tous les composants d'interface utilisateur de l'application VarunaPoC (pages, panneaux, outils).

## Pourquoi
Separer la logique de presentation du coeur applicatif (core, viewers, services) pour faciliter la maintenance et l'evolution de l'interface.

## Structure
- `index.js` — Point d'entree : re-exporte les composants principaux (CompareLayout, ViewerPanel, SyncControls, FolderBrowser, Viewer legacy).
- `Home.js` — Page d'accueil avec liste des lames, recherche et statistiques.
- `LoginPage.js` — Page de connexion OIDC.
- `FolderBrowser.js` — Navigation hierarchique dans les dossiers de lames.
- `CaseBrowser.js` — Navigation par cas cliniques.
- `CaseSidebar.js` — Barre laterale d'un cas (lames, metadonnees).
- `Viewer.js` — Wrapper legacy pour compatibilite avec l'ancienne API du viewer.
- `ViewerPanel.js` — Panneau viewer complet avec barre d'outils et metadonnees.
- `CompareLayout.js` — Disposition grille CSS pour comparaison multi-viewers.
- `SyncControls.js` — Controles de synchronisation pan/zoom entre viewers.
- `AnnotationLayer.js` — Couche de rendu des annotations sur le viewer.
- `DrawingTools.js` — Outils de dessin (rectangle, polygone, point, main levee).
- `LayerManager.js` — Gestionnaire de couches visuelles (annotations, heatmaps).
- `DetectionPanel.js` — Panneau de detection d'objets par IA.
- `MLPanel.js` — Panneau d'analyse par modeles de machine learning.
- `QualityPanel.js` — Panneau de controle qualite des lames.
- `QualityBadge.js` — Badge indicateur de qualite.
- `CountingPanel.js` — Panneau de comptage manuel.
- `CellCountingPanel.js` — Panneau de comptage cellulaire automatise.
- `ClusteringPanel.js` — Panneau de regroupement par similarite.
- `ClusteringOverlay.js` — Superposition visuelle des clusters sur le viewer.
- `SimilarityPanel.js` — Panneau de recherche de lames similaires.
- `HeatmapOverlay.js` — Superposition de heatmap sur le viewer.
- `FocusAssistPanel.js` — Panneau d'assistance a la mise au point.
- `DriftDashboard.js` — Tableau de bord de derive des modeles.
- `AutoTagBadge.js` — Badge d'etiquetage automatique.
- `MagnificationBar.js` — Barre de grossissement.
- `SlideList.js` — Liste de lames avec apercu.
- `RecentCases.js` — Affichage des cas recents.
- `WorklistView.js` — Vue de la liste de travail (en attente, en cours, termine).
- `UserMenu.js` — Menu utilisateur (profil, deconnexion, langue).
