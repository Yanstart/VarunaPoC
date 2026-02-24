# Claude Code Configuration - VarunaPoC

## CONTEXT

**Project**: Viewer web de lames histologiques pour le CHU UCL Namur
**Stack**: FastAPI + OpenSlide (backend) / Vanilla JS + Vite + OpenSeadragon (frontend)
**Repo**: `Yanstart/VarunaPoC` (private)
**Docs**: `docs/PROPOSAL_VARUNA_v2.md` (vision), `CONTRIBUTING.md` (workflow git)

---

## PROJECT STATE

### Milestones (GitHub)

| Milestone | Issues | Status |
|-----------|--------|--------|
| Wave 1 — Le viewer qui parle pathologiste | 11/11 closed | DONE |
| Wave 2 — L'IA qui assiste | 10/10 closed | DONE |
| Wave 3 — Le cas, pas le fichier | 8/8 closed | DONE |
| Wave 4 — L'ecosysteme intelligent | 11/11 closed | DONE |
| Standards (no milestone) | #103-#124, all closed | DONE |

**All 62 issues closed. 0 open issues.**

### Current tag: `v0.1.0` — baseline stable (Waves 1-4 + standards + CI/CD)

---

## GIT WORKFLOW

**Trunk-Based Development** — see `CONTRIBUTING.md` for full details.

- `main` = only permanent branch, always deployable
- Feature branches: `feat/issue-{N}-{desc}` or `fix/issue-{N}-{desc}`
- PR required (branch protection active)
- CI must pass before merge
- Branches auto-deleted after merge
- Tags: semver per milestone

---

## COMMIT RULES (STRICT)

- **NO** `Co-Authored-By: Claude ...`
- **NO** `Generated with Claude Code`
- **NO** emojis
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
- Reference issues: `Fixes #N` in commit body

---

## CODE LOCATIONS

```text
VarunaPoC/
  backend/               # FastAPI: tiles, annotations, ML, FHIR, DICOM
    main.py              # App entry point (feature-flagged imports)
    routes/              # API endpoints (~15 routers)
    services/            # Business logic (tile_server, format_detector, ML, standards)
    models/              # SQLAlchemy ORM (Annotation, Label, QualityReport...)
    alembic/             # DB migrations (PostgreSQL + PostGIS)
    auth/                # OIDC + RBAC (optional, AUTH_ENABLED)
    fhir/                # FHIR R4 (optional, FHIR_ENABLED)
    quality/             # Inter-annotator agreement (optional, QUALITY_ENABLED)
  frontend/              # Vanilla JS + Vite + OpenSeadragon
    src/core/            # EventBus, Constants
    src/services/        # ApiService, AuthService, AnnotationStore, I18nService
    src/viewers/         # ViewerManager, ViewerInstance, SyncController
    src/components/      # 31 UI components (DrawingTools, MLPanel, CompareLayout...)
    e2e/                 # Playwright tests (18 suites)
  nginx/                 # Reverse proxy + tile cache (10 GB)
  monitoring/            # Prometheus + Grafana + alertes
  Slides/                # Test data (~60 GB, gitignored)
  docs/                  # Architecture, deployment, manual, standards, plans
  Archives/              # Historical docs + future plans (MLOps, security, refactoring)
```

Every folder has an `info.md` with: But, Pourquoi, Comment, Structure.

---

## BUILD & TEST

```bash
# Backend
cd backend
pip install -r requirements.txt
pytest
ruff check .

# Frontend
cd frontend
npm ci
npm run dev          # http://localhost:5173
npm run lint
npx playwright test  # E2E

# Docker
docker compose -f docker-compose.dev.yml up -d --build            # dev
docker compose -f docker-compose.production.yml up -d --build     # prod
```

---

## VALIDATION CHECKLIST

Before closing any issue:

- [ ] Backend tests pass: `cd backend && pytest`
- [ ] Frontend lint clean: `cd frontend && npm run lint`
- [ ] E2E tests pass (if UI change): `cd frontend && npx playwright test`
- [ ] Docker build works: `docker compose -f docker-compose.dev.yml build`
- [ ] Issue acceptance criteria met
- [ ] Commit message follows rules
- [ ] PR created and linked to issue
