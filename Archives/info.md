# Archives

## But
Documents historiques et plans futurs non encore actifs. Referentiel pour les decisions passees et les roadmaps a venir.

## Pourquoi
Separer les documents actifs (dans `docs/`) des documents de reference/planification pour garder le projet navigable.

## Structure
```
Archives/
  Build-Docs/       # Notes de build cross-platform + anciens docker-compose
  Phase2-Deployment/ # Guide de deploiement Phase 1/2 (CHU, decembre 2025)
  Phase2-Refactoring/ # Plan Clean Architecture backend (37h, Strangler Pattern)
  Phase3-Planning/
    Infrastructure/  # Spec Phase 2.5 (Docker, Nginx, Redis, monitoring)
    MLOps/           # Architecture ML Phase 3.4-3.5 (tag extraction, routing, retraining)
    Security/        # Roadmap securite HIPAA/GDPR (4 phases, URGENT Phase 1)
  Research/          # Articles academiques (digital pathology, WSI, AI)
  TFE/               # Memoire de fin d'etudes + proposition + vision.pdf
```

## Notes
- `Phase2-Refactoring/` = plan approuve, pret a implementer en Phase 3
- `Phase3-Planning/Security/` = bloquant pour production (compliance HIPAA/GDPR)
- `TFE/` = documents officiels a conserver indefiniment
