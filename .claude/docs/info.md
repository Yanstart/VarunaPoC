# .claude/docs

## But
Documentation de contexte projet pour les agents Claude Code.

## Pourquoi
Fournit aux agents une vue synthetique de l'architecture, des patterns, des contrats entre modules et de l'etat du code. Evite de relire le code source a chaque session.

## Comment
Fichiers Markdown maintenu manuellement ou par les agents apres des changements significatifs. Charges automatiquement dans le contexte des agents.

## Structure
```
docs/
  ARCHITECTURE.md       # Architecture globale du systeme
  ARCHITECTURE_V3.md    # Evolution architecture v3
  CONTEXT.md            # Contexte projet (CHU, pathologie, stack)
  FILES.md              # Index des fichiers importants
  MODULE_CONTRACTS.md   # Contrats d'interface entre modules
  PATTERNS.md           # Design patterns utilises
  QUICK_START.md        # Demarrage rapide
  README.md             # Vue d'ensemble des docs
  REFACTORING_PLAN.md   # Plan de refactoring
  VISION_V3.md          # Vision produit v3
```
