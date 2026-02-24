# Contributing to VarunaPoC

## Git Workflow

**Trunk-Based Development** — `main` is the only permanent branch. Always deployable.

### Branches

| Type | Pattern | Exemple |
|------|---------|---------|
| Feature | `feat/issue-{N}-{desc}` | `feat/issue-6-throughput` |
| Fix | `fix/issue-{N}-{desc}` | `fix/issue-14-clippy` |
| Chore | `chore/{desc}` | `chore/update-deps` |

Branches are short-lived (hours to days). Deleted automatically after merge.

### Workflow

```bash
# 1. Pick an issue
gh issue view {N}

# 2. Create branch from main
git checkout main && git pull
git checkout -b feat/issue-{N}-short-description

# 3. Code, test, commit
cargo test                    # or: pytest, npm test
git add <files>
git commit -m "feat(scope): description

Fixes #{N}"

# 4. Push and create PR
git push -u origin feat/issue-{N}-short-description
gh pr create --title "feat(scope): description" --body "Fixes #{N}"

# 5. CI passes -> merge -> branch auto-deleted
```

### Commits

Format: `type(scope): description`

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `chore` | Maintenance (deps, CI, config) |

Rules:
- NO `Co-Authored-By: Claude ...` or `Generated with Claude Code`
- NO emojis
- Reference issue: `Fixes #N` in commit body
- Keep subject line under 72 characters

### Tags & Releases

Tags follow milestones:

| Milestone | Tag |
|-----------|-----|
| M0 - Fondations | `v0.1.0` |
| M1 - Coeur fonctionnel | `v0.2.0` |
| M2 - Stabilite et performance | `v0.3.0` |
| M3 - Service et deploiement | `v0.4.0` |
| M4 - Plugins v1 | `v0.5.0` |
| Hotfix on published milestone | `v0.X.1` |

Create a release:
```bash
git tag -a v0.1.0 -m "M0 - Fondations complete"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0 - M0 Fondations" --generate-notes
```

### Branch Protection (main)

- Pull request required (no direct push)
- CI status checks must pass before merge
- Branches auto-deleted after merge

### What NOT to do

- Do not push directly to `main` — use a PR
- Do not create `develop`, `release/*`, or `staging` branches
- Do not force-push to `main`
- Do not merge PRs with failing CI
- Do not commit secrets (`.env`, credentials, keys)

---

## Development Setup

### Backend (FastAPI + OpenSlide)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (Vite + OpenSeadragon)
```bash
cd frontend
npm ci
npm run dev    # http://localhost:5173
```

### Docker (full stack)
```bash
# Dev
docker compose -f docker-compose.dev.yml up -d --build

# Production
cp .env.production.example .env.production
docker compose -f docker-compose.production.yml up -d --build
```

### Tests
```bash
# Backend
cd backend && pytest

# Frontend E2E
cd frontend && npx playwright test

# Lint
cd backend && ruff check .
cd frontend && npm run lint
```

---

## Project Structure

Every folder contains an `info.md` with: purpose, why it exists, how it works, and file structure.

```
VarunaPoC/
  backend/       # FastAPI API (tiles, annotations, ML, FHIR, DICOM)
  frontend/      # Vanilla JS + Vite + OpenSeadragon viewer
  nginx/         # Reverse proxy + tile cache
  monitoring/    # Prometheus + Grafana
  Scripts/       # Deployment + fork management scripts
  docs/          # Technical docs, user manual, standards
  Slides/        # Test data (~60 GB, gitignored)
```

See `info.md` at root for the full map.
