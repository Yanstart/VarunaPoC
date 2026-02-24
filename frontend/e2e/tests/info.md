# tests

## But
Contenir les fichiers de specs Playwright couvrant chaque fonctionnalite de l'application VarunaPoC.

## Pourquoi
Organiser les tests E2E par domaine fonctionnel, numerotes pour un ordre d'execution logique allant du plus fondamental au plus avance.

## Structure
- `01-health.spec.js` — Verification de sante backend et chargement frontend.
- `02-navigation.spec.js` — Navigation par dossiers, fil d'Ariane, recherche.
- `03-viewer.spec.js` — Chargement du viewer OpenSeadragon, canvas, metadonnees.
- `04-compare.spec.js` — Mode comparaison multi-viewers.
- `05-annotations.spec.js` — Creation, edition et suppression d'annotations.
- `06-ml.spec.js` — Panneau d'analyse IA et inference.
- `07-quality.spec.js` — Panneau de controle qualite des lames.
- `08-pacs.spec.js` — Integration PACS/DICOM.
- `09-auth.spec.js` — Flux d'authentification OIDC.
- `10-accessibility.spec.js` — Tests d'accessibilite (ARIA, clavier).
- `12-auto-tag.spec.js` — Etiquetage automatique des lames.
- `13-focus-assist.spec.js` — Assistance a la mise au point.
- `14-case-navigation.spec.js` — Navigation par cas cliniques.
- `15-cell-counting.spec.js` — Comptage cellulaire.
- `16-clustering.spec.js` — Regroupement de regions similaires.
- `17-quality-badge.spec.js` — Badge qualite des lames.
- `18-worklist-history.spec.js` — Historique de la liste de travail.
- `19-waves1-2-features.spec.js` — Tests de regression des fonctionnalites waves 1 et 2.
