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

### Architecture post-v0.1.0 — Strangler Fig migration (in progress)

Six **Protocols** (PEP 544) abstract the seams between routes and infrastructure.
Each Protocol has at least one concrete implementer; routes consume them via
FastAPI `Depends`.

| Protocol | Implementer(s) | Status |
|---|---|---|
| `AuthProvider` | `OIDCAuthProvider` | available; legacy `dependencies.py` still primary |
| `StorageProvider` | `FilesystemStorageProvider` | wired in `routes/ml.py`, `routes/slides.py` |
| `SlideReader` | `OpenSlideReader`, `BioFormatsReader`, `OMETIFFReader`, `OMEZarrReader` | wired transitively via `services/tile_server.py` |
| `TileCache` | `TwoLevelTileCache` (L1 mem + L2 Redis) | wired in `routes/slides.py:get_tile` |
| `WorkflowHook` | `FHIRWorkflowHook`, `PACSWorkflowHook`, `WebSocketWorkflowHook`, `CompositeWorkflowHook`, `NoOpWorkflowHook` | wired in `routes/exports.py`, `routes/annotations.py` |
| `MLWorkerProvider` | `MLWorkerProxy` (subprocess), `InProcessMLWorker` (ONNX/OpenVINO), `TritonClientMLWorker` (stub) | wired in `routes/ml.py` (sprint 12) |

Sprint 15 added a WebSocket broadcaster: `WebSocketWorkflowHook` + `WorkflowEventBroadcaster`
publish workflow events to clients connected on `GET /api/v1/ws/events`. The frontend
`WorkflowEventService` subscribes on app boot and re-emits events on the `EventBus`.

Canonical doc: `docs/architecture/MODULAR_ARCHITECTURE.md`. Conformance is locked in
by `tests/unit/test_protocol_conformance.py`.

### Dev infrastructure (`docker-compose.yml --profile dev`)

| Service | Port | Purpose | Required for |
|---|---|---|---|
| `postgres` (PostGIS) | 5433 | Annotations, audit, sessions, quality | most features |
| `keycloak` | 8180 | OIDC dev | `AUTH_ENABLED=true` |
| `redis` | 6380 | TileCache L2 | `TILE_CACHE_L2_ENABLED=true` |
| `hapi-fhir` | 8090 | FHIR R4 sandbox | `FHIR_ENABLED=true` |
| `orthanc` | 4242 (DICOM) / 8042 (HTTP) | PACS sandbox | `PACS_ENABLED=true` |

All four optional services degrade gracefully when their flag is off.

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
    main.py              # App entry point (feature-flagged imports + Protocol singletons)
    core/interfaces/     # 6 Protocols (Strangler Fig seams)
    routes/              # API endpoints (~15 routers, ws.py for WebSocket)
    services/            # Business logic; concrete Protocol implementers live here
      cache/             # TwoLevelTileCache (L1 mem + L2 Redis)
      readers/           # SlideReader implementers
      storage/           # FilesystemStorageProvider
      workflow/          # FHIR / PACS / WebSocket hooks + Composite + EventBroadcaster
      ml/                # MLWorkerProvider + 3 backends (subprocess/inprocess/triton)
    models/              # SQLAlchemy ORM (Annotation, Label, QualityReport...)
    alembic/             # DB migrations (PostgreSQL + PostGIS)
    auth/                # OIDC + RBAC + OIDCAuthProvider (optional, AUTH_ENABLED)
    fhir/                # FHIR R4 + FHIRWorkflowHook (optional, FHIR_ENABLED)
    quality/             # Inter-annotator agreement (optional, QUALITY_ENABLED)
  frontend/              # Vanilla JS + Vite + OpenSeadragon
    src/core/            # EventBus, Constants
    src/services/        # ApiService, AuthService, WorkflowEventService (WS), I18nService
    src/viewers/         # ViewerManager, ViewerInstance, SyncController
    src/components/      # 31 UI components (DrawingTools, MLPanel, CompareLayout...)
    e2e/                 # Playwright tests (18 suites)
  nginx/                 # Reverse proxy + tile cache (10 GB) — L3 above the L1+L2 in backend
  monitoring/            # Prometheus + Grafana + alertes
  Slides/                # Test data (~60 GB, gitignored)
  docs/                  # Architecture, deployment, manual, standards
                         # plans/ contains active plans only; closed plans live in Archives/plans-historiques/
  Archives/              # Historical docs + closed plans + future-phase research
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
docker compose --profile dev up -d --build            # dev
docker compose --profile prod --profile monitoring up -d --build     # prod
```

---

## VALIDATION CHECKLIST

Before closing any issue:

- [ ] Backend tests pass: `cd backend && pytest`
- [ ] Frontend lint clean: `cd frontend && npm run lint`
- [ ] E2E tests pass (if UI change): `cd frontend && npx playwright test`
- [ ] Docker build works: `docker compose --profile dev build`
- [ ] Issue acceptance criteria met
- [ ] Commit message follows rules
- [ ] PR created and linked to issue
