# Quick Start - Architecture V3

**Pour démarrer rapidement avec la nouvelle architecture.**

---

## En 5 Minutes

### 1. Comprendre la Vision

```
VarunaPoC v1.7.0 (Actuel)                    VarunaPoC v2.x (Cible)
┌────────────────────────────┐          ┌────────────────────────────┐
│  Plateforme WSI Phase 2    │          │  Plateforme Quality-First  │
│  - 10 formats (94 lames)  │    →     │  - Auth RBAC + JWT         │
│  - Annotations PostGIS    │          │  - PACS Telemis            │
│  - ML Slideflow+Phikon-v2 │          │  - Quality metrics IAA     │
│  - Compare mode           │          │  - Audit trail             │
│  - 94 tests, CI/CD        │          │  - Tests E2E               │
└────────────────────────────┘          └────────────────────────────┘
```

**Changement clé:** Modularité maximale, couplage minimal.

---

### 2. Lire les Docs

**Ordre de lecture recommandé:**

1. **README.md** (ce dossier) - Vue d'ensemble
2. **ARCHITECTURE_V3.md** - Architecture complète (30min)
3. **MODULE_CONTRACTS.md** - Interfaces entre modules (20min)
4. **REFACTORING_PLAN.md** - Plan de migration (15min)

---

### 3. Comprendre les Modules

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│  - Viewer (multi-panel, annotations, heatmaps)          │
│  - State Management (ViewerStore, AnnotationStore)      │
│  - WebSocket (collaboration temps réel)                 │
└──────────────────┬──────────────────────────────────────┘
                   │ API Gateway (Kong/Traefik)
         ┌─────────┼──────────┬──────────┬────────────┐
         │         │          │          │            │
    ┌────▼───┐ ┌──▼──────┐ ┌─▼─────┐ ┌─▼────────┐   │
    │ Viewer │ │   ML    │ │ PACS  │ │ Storage  │   │
    │Service │ │ Service │ │Plugin │ │ (MinIO)  │   │
    └────────┘ └─────────┘ └───────┘ └──────────┘   │
         │         │                                 │
         └─────────┴────────── OpenSlide ────────────┘
```

**Principe:** Chaque module peut évoluer indépendamment.

---

### 4. Premiers Pas Développement

#### Setup Backend (Phase 2.0)

```bash
cd backend

# Créer venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer deps
pip install -r requirements.txt

# Copier config
cp .env.example .env
# Éditer .env (SLIDES_ROOT, etc.)

# Lancer tests
pytest --cov=services --cov-report=term

# Lancer serveur
uvicorn main:app --reload
```

#### Setup Frontend (Phase 2.0)

```bash
cd frontend

# Installer deps
npm install

# Copier config
cp .env.example .env.development
# Éditer .env.development (VITE_API_BASE_URL, etc.)

# Lancer dev server
npm run dev

# Lancer tests
npm run test
```

---

### 5. Contribuer

**Workflow Git:**

```bash
# Créer branche feature
git checkout -b feature/storage-abstraction

# Développer, tester
# ...

# Commit
git add .
git commit -m "feat(storage): Add StorageProvider abstraction

- Created base interface StorageProvider
- Implemented FilesystemStorageProvider
- Added unit tests (coverage 85%)
- Backward compatible with Phase 1

Closes #123"

# Push
git push origin feature/storage-abstraction

# Créer PR sur GitHub
# CI/CD automatique: tests, coverage, linting
```

**Conventions:**

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` Nouvelle fonctionnalité
  - `fix:` Bug fix
  - `refactor:` Refactoring (pas de changement comportement)
  - `test:` Ajout tests
  - `docs:` Documentation

- **Branches:**
  - `main` - Production (protégée)
  - `develop` - Intégration (branche par défaut)
  - `feature/xxx` - Nouvelles fonctionnalités
  - `bugfix/xxx` - Corrections bugs
  - `release/vX.Y.Z` - Préparation releases

---

## Checklist Développeur

### Avant de Coder

- [ ] Lire ARCHITECTURE_V3.md (comprendre vision)
- [ ] Lire MODULE_CONTRACTS.md (comprendre interfaces)
- [ ] Identifier module concerné (Viewer, ML, PACS, etc.)
- [ ] Vérifier contrat interface à respecter
- [ ] Créer branche feature

### Pendant Développement

- [ ] Tests unitaires AVANT implémentation (TDD si possible)
- [ ] Code coverage >80%
- [ ] Docstrings/JSDoc complets
- [ ] Pas de config hardcodée (utiliser Settings)
- [ ] Logs structurés (JSON si possible)
- [ ] Gestion erreurs (try/except, raise HTTP exceptions)

### Avant Commit

- [ ] Tests passent localement (`pytest`, `npm run test`)
- [ ] Linter passent (`pylint`, `eslint`)
- [ ] Documentation mise à jour (README, docstrings)
- [ ] Pas de secrets dans code (vérifier .env)
- [ ] Commit message clair (Conventional Commits)

### Avant Merge

- [ ] CI/CD vert (tests, coverage, linting)
- [ ] Code review approuvé (au moins 1 reviewer)
- [ ] Documentation mise à jour (si nécessaire)
- [ ] Pas de régression (regression tests passent)
- [ ] Branch à jour avec `develop` (rebase si nécessaire)

---

## FAQ Rapide

### Q: Par où commencer pour Phase 2.0?

**A:** Lire [REFACTORING_PLAN.md](./REFACTORING_PLAN.md), section Phase 2.0.

**Tâches prioritaires:**
1. Tâche 2.0.1: Abstraire Storage (3 jours)
2. Tâche 2.0.2: Configuration Management (2 jours)
3. Tâche 2.0.3: Versioning API (2 jours)

---

### Q: Comment tester localement l'architecture modulaire?

**A:** Utiliser Docker Compose pour lancer tous services.

```yaml
# docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.4
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_DB=varuna
      - POSTGRES_USER=varuna
      - POSTGRES_PASSWORD=varuna_dev
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://varuna:varuna_dev@postgres:5432/varuna
      - SLIDES_ROOT=/slides
    volumes:
      - ./Slides:/slides
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000

volumes:
  pgdata:
```

Lancer: `docker compose --profile dev up -d`

---

### Q: Comment migrer code existant sans casser?

**A:** Strangler Fig Pattern (remplacement progressif).

**Exemple:**

```python
# Avant (Phase 1)
from services.slide_scanner import scan_slides_directory

slides = scan_slides_directory()

# Pendant transition (Phase 2.0)
from services.storage.filesystem import FilesystemStorageProvider
from config.settings import settings

if settings.storage_provider == "filesystem":
    # Nouveau code
    provider = FilesystemStorageProvider(settings.slides_root)
    slides = await provider.list_slides()
else:
    # Fallback ancien code (deprecated)
    from services.slide_scanner import scan_slides_directory
    slides = scan_slides_directory()

# Après migration (Phase 2.1+)
# Supprimer ancien code, garder seulement nouveau
```

---

### Q: Comment documenter nouveau module?

**A:** Suivre template documentation.

**Structure README module:**

```markdown
# [Module Name]

## Purpose

What does this module do and why?

## Architecture

High-level diagram of module internals.

## API Contracts

Links to MODULE_CONTRACTS.md sections.

## Usage

Examples of using the module.

## Configuration

Environment variables, settings.

## Testing

How to run tests, coverage requirements.

## Deployment

How to deploy this module.

## Technical Notes

Important implementation details.

## Changelog

Version history.
```

**Placer dans:** `backend/[module-name]/README.md`

---

### Q: Quelle version API utiliser (v1 ou v2)?

**A:**

- **v1:** Phase 1 compatible, deprecated, sera supprimé v3.0.0
- **v2:** Nouveau format, recommandé pour nouveau code

**Frontend:** Configurer via env var `VITE_API_VERSION`.

**Backend:** Configurer via env var `API_VERSION`.

---

### Q: Comment ajouter nouveau StorageProvider (ex: S3)?

**A:**

1. Creer `backend/services/storage/s3.py`
2. Implémenter interface `StorageProvider` (voir `base.py`)
3. Ajouter tests unitaires (`test_storage_s3.py`)
4. Ajouter config dans `settings.py` (S3_ENDPOINT, etc.)
5. Update factory:

```python
# backend/services/storage/__init__.py

from .base import StorageProvider
from .filesystem import FilesystemStorageProvider
from .s3 import S3StorageProvider

def create_storage_provider(provider_type: str, config) -> StorageProvider:
    if provider_type == "filesystem":
        return FilesystemStorageProvider(config.slides_root)
    elif provider_type == "s3":
        return S3StorageProvider(
            endpoint=config.s3_endpoint,
            bucket=config.s3_bucket,
            access_key=config.s3_access_key,
            secret_key=config.s3_secret_key
        )
    else:
        raise ValueError(f"Unknown storage provider: {provider_type}")
```

6. Tester avec `STORAGE_PROVIDER=s3` dans `.env`

---

### Q: Comment contribuer à la documentation?

**A:**

**Documentation code:**
- Docstrings Python (Google style)
- JSDoc JavaScript
- Auto-générée avec Sphinx (backend) ou JSDoc (frontend)

**Documentation utilisateur:**
- Markdown dans `docs/Manuel/`
- Suivre template (voir CLAUDE.md, section Manual Update Protocol)

**Documentation architecture:**
- Markdown dans `.claude/docs/`
- Mettre à jour après changements majeurs

---

## Ressources

### Liens Utiles

- **Architecture V3:** [ARCHITECTURE_V3.md](./ARCHITECTURE_V3.md)
- **Contrats Modules:** [MODULE_CONTRACTS.md](./MODULE_CONTRACTS.md)
- **Plan Refactoring:** [REFACTORING_PLAN.md](./REFACTORING_PLAN.md)
- **CLAUDE.md:** Instructions globales projet
- **OpenSlide Docs:** https://openslide.org/
- **FastAPI Tutorial:** https://fastapi.tiangolo.com/
- **MLflow Docs:** https://mlflow.org/docs/

### Outils Recommandés

**IDE:**
- VS Code + extensions: Python, Pylance, ESLint, Vite
- PyCharm Professional (Python)
- WebStorm (JavaScript)

**Database:**
- pgAdmin (PostgreSQL GUI)
- Redis Commander (Redis GUI)

**API Testing:**
- Thunder Client (VS Code extension)
- Postman
- curl / httpie

**Monitoring:**
- Grafana (dashboards)
- Prometheus (metrics)
- Kibana (logs)

---

**Derniere mise a jour:** 2026-02-08
**Prochaine revision:** Apres Phase 3
