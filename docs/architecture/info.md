# docs/architecture

## But
Documentation architecturale technique. Diagrammes C4, contrats entre modules, plan de refactoring.

## Doc canonique
`MODULAR_ARCHITECTURE.md` — table de wirage des Protocols, sprints livrés, métriques.
À lire en premier avant tout refactor backend.

## Structure
```
architecture/
  README.md                    # Index + statut courant + roadmap
  MODULAR_ARCHITECTURE.md      # ★ CANONIQUE : 6 Protocols + Strangler Fig + sprint log
  ARCHITECTURE_V3.md           # Vision systeme V3 (diagrammes C4)
  SYSTEM_PATTERNS.md           # Patterns utilises (Factory, Strategy, Singleton, EventBus)
  MODULE_CONTRACTS.md          # Contrats API entre modules (interfaces, schemas)
  REFACTORING_PLAN.md          # Plan migration Clean Architecture
  READER_SELECTION_SYSTEM.md   # Logique de selection des lecteurs de lames
  QUICK_START_MODULAR.md       # Guide demarrage rapide architecture modulaire
  QUICK_START.md               # Guide demarrage rapide (legacy, ARCHITECTURE_V3)
  IMPLEMENTATION_REPORT.md     # Rapport implementation pour management
  IMPLEMENTATION_SUMMARY.md    # Resume implementation par phase
  INTEGRATION_SUMMARY.md       # Resume integrations (Slideflow, FHIR, DICOM)
  info.md                      # Ce fichier
```

Note : `cornerstone3d-evaluation.md` a été déplacé vers `Archives/Research/` (decision NO-GO post-évaluation).
