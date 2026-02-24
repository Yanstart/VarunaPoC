# Phase2-Refactoring

## But
Plans de refactoring du backend et du frontend pour preparer VarunaPoC a l'integration MLOps (tags, feedback, modeles ML).

## Pourquoi
Le backend monolithique initial devait etre restructure en Clean Architecture pour permettre la modularite, la testabilite et l'ajout de fonctionnalites ML sans casser l'existant.

## Structure
- `BACKEND_REFACTORING.md` - Plan d'action complet pour le refactoring backend vers une architecture hexagonale MLOps-ready.
- `BACKEND_REFACTORING_SUMMARY.md` - Resume executif du probleme de couplage et de la strategie de refactoring.
- `BACKEND_REFACTORING_STEP1_EXAMPLE.md` - Exemple pratique de la premiere etape : centralisation de la configuration avec Pydantic Settings.
- `BACKEND_ARCHITECTURE_DIAGRAM.md` - Diagrammes d'architecture du backend en couches (Presentation, Service, Domain, Infrastructure).
- `FRONTEND_REFACTORING.md` - Plan de refactoring frontend V3 avec fonctionnalites IA (overlay, state management, performance).
- `INFRASTRUCTURE_ARCHITECTURE.md` - Architecture infrastructure cible : cache multi-niveaux, load balancing, CI/CD, monitoring.
