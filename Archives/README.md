# Archives

Ce dossier contient les documents et fichiers qui ne sont pas essentiels pour le PoC Phase 1 mais qui doivent etre conserves pour reference future.

## Structure

```
Archives/
├── Backups/              <- Sauvegardes de fichiers .env et docker-compose
├── Build-Docs/           <- Documentation des variantes de build
├── Phase2-Deployment/    <- Guides de deploiement Phase 2+
├── Phase2-Refactoring/   <- Plans de refactoring backend/frontend
├── Phase3-Planning/      <- Documentation planification future
│   ├── Infrastructure/   <- Architecture infrastructure
│   ├── MLOps/           <- Plateforme MLOps
│   └── Security/        <- Framework securite
├── Research/            <- Articles et materiaux de recherche
└── TFE/                 <- Documents lies au TFE (these)
```

## Pourquoi ces fichiers sont archives

### Phase2-Deployment/
Documents specifiques au deploiement en reseau CHU (Phase 2.1, 2.2).
Seront reactives quand le deploiement reseau sera prioritaire.

### Phase2-Refactoring/
Plans de refactoring du code backend/frontend.
Non essentiels pour le PoC fonctionnel actuel.

### Phase3-Planning/
- **MLOps**: Integration IA/ML pour analyse automatique (Phase 3+)
- **Security**: Framework de securite complet HIPAA/GDPR (Phase 3+)
- **Infrastructure**: Architecture multi-site et scalabilite (Phase 3+)

### Research/
Articles academiques et documentation de reference.
Utiles pour comprendre le contexte mais pas pour le developpement quotidien.

### TFE/
Documents lies au Travail de Fin d'Etudes.
Reference academique, pas necessaire pour le code.

### Backups/
Anciennes versions de fichiers de configuration (.env, docker-compose).
Gardes par precaution mais normalement obsoletes.

### Build-Docs/
Documentation des differences entre variantes de build.
Reference technique pour debugging.

## Reactivation

Pour reactiver un document archive:
1. Deplacer le fichier vers son emplacement original
2. Mettre a jour la documentation concernee
3. Commiter avec un message expliquant la reactivation

## Date d'archivage

- 2025-02-02: Restructuration initiale du repository
