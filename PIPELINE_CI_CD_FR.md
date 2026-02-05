# Pipeline CI/CD - VarunaPoC

Pipeline automatisé pour garantir la qualité, sécurité et déploiement fiable de VarunaPoC.

---

## Résumé Exécutif

Le pipeline CI/CD de VarunaPoC automatise:

1. **Qualité du code** - Linting Python (Ruff) et JavaScript (ESLint)
2. **Tests automatisés** - pytest avec coverage pour backend
3. **Builds Docker** - Images backend et frontend
4. **Sécurité** - Scans de vulnérabilités (Trivy, CodeQL, Bandit)
5. **Déploiement** - Publication automatique vers GitHub Container Registry
6. **Compliance** - Vérifications HIPAA/GDPR (données médicales)

**Temps total:** ~5-7 minutes par PR

---

## Architecture du Pipeline

```
Developer Push
      │
      ▼
┌─────────────────┐
│   CI Pipeline   │  → Lint + Tests + Build Docker
│   (~5-7 min)    │  → Status requis pour merge
└─────────────────┘
      │
   Merge PR
      │
      ▼
┌─────────────────┐
│   CD Pipeline   │  → Build images Docker
│   (~8-12 min)   │  → Push vers ghcr.io
└─────────────────┘  → Release GitHub
      │
      ▼
┌─────────────────┐
│ Security Scan   │  → Trivy, CodeQL, Bandit
│ (quotidien)     │  → HIPAA/GDPR checks
└─────────────────┘  → Gitleaks (secrets)
```

---

## Workflows GitHub Actions

### 1. CI - Continuous Integration

**Fichier:** `.github/workflows/ci.yml`

**Déclencheurs:**
- Pull Requests vers `main` ou `develop`
- Push vers `main` ou `develop`

**Jobs exécutés:**

| Composant | Vérifications | Temps |
|-----------|--------------|-------|
| **Backend** | Ruff lint, pytest, Docker build | ~3-4min |
| **Frontend** | ESLint, Vite build, Docker build | ~2-3min |
| **Integration** | Test backend ↔ frontend | ~1min |

**Status requis pour merge:** ✅ CI Status

---

### 2. CD - Continuous Deployment

**Fichier:** `.github/workflows/cd.yml`

**Déclencheurs:**
- Push vers `main` (après merge PR)
- Tags Git `v*.*.*` (releases)

**Actions:**

1. **Build and Push Images**
   - Build Docker backend + frontend
   - Push vers `ghcr.io/<owner>/varunapoc/backend:latest`
   - Tags: `latest`, `v1.2.3`, `main-abc1234`

2. **Create Release** (si tag Git)
   - Génère changelog automatique
   - Crée GitHub Release
   - Attache images Docker

3. **Update Manifest**
   - Met à jour `Scripts/Deployment/docker-compose.yml`
   - Commit automatique

---

### 3. Security Scanning

**Fichier:** `.github/workflows/security.yml`

**Déclencheurs:**
- Pull Requests
- Push vers main/develop
- Quotidien à 2 AM UTC
- Manuel (`workflow_dispatch`)

**Scans exécutés:**

| Type | Outil | Cible |
|------|-------|-------|
| Vulnérabilités deps | Trivy | requirements.txt, package.json |
| Python security | Bandit, Safety | Code Python |
| JavaScript security | npm audit | Code JavaScript |
| Docker images | Trivy | Images finales |
| SAST | CodeQL | Python + JavaScript |
| Secrets | Gitleaks | Historique Git |
| HIPAA/GDPR | Custom | Patterns PHI/PII |

**Important:** Projet médical donc sécurité maximale.

---

## Configuration des Outils

### Backend (Python)

**Linters installés:**

```bash
pip install ruff black isort pytest pytest-cov
```

**Configuration:** `backend/ruff.toml`, `backend/pyproject.toml`

**Vérification locale:**

```bash
cd backend
ruff check .              # Lint
black --check .           # Format check
pytest -m unit            # Tests rapides
```

**Auto-fix:**

```bash
ruff check --fix .
black .
isort .
```

---

### Frontend (JavaScript)

**Linters installés:**

```bash
cd frontend
npm install
```

**Configuration:** `frontend/.eslintrc.json`

**Vérification locale:**

```bash
cd frontend
npm run lint              # Lint
npm run build             # Build production
```

**Auto-fix:**

```bash
npm run lint:fix
```

---

## Tests

### Backend Tests

**Structure:**

```
backend/tests/
├── __init__.py
├── conftest.py              # Fixtures (client, mock_slides)
├── test_health.py           # 7 tests unitaires
└── test_slides_api.py       # 6 tests (3 skippés)
```

**Exécution:**

```bash
cd backend
pytest                       # Tous tests
pytest -m unit              # Unitaires uniquement
pytest --cov=.              # Avec coverage
```

**Coverage actuel:** ~45% (objectif: 60%+)

---

## Workflow Développeur

### 1. Développement Local

```bash
# Créer branche feature
git checkout -b feature/ma-fonctionnalite

# Coder...

# Check local AVANT push
cd backend
ruff check . && pytest -m unit

cd ../frontend
npm run lint && npm run build

# Commit et push
git add .
git commit -m "feat: Nouvelle fonctionnalité"
git push origin feature/ma-fonctionnalite
```

### 2. Pull Request

1. Créer PR sur GitHub
2. CI démarre automatiquement (~5-7min)
3. Vérifier que CI passe (✅ CI Status)
4. Demander review
5. Merger si approuvé

### 3. Merge vers Main

- CD démarre automatiquement
- Images Docker publiées sur ghcr.io
- Prêt pour déploiement

### 4. Release (optionnel)

```bash
# Bump version
# - backend/main.py: version="1.8.0"
# - frontend/package.json: "version": "1.8.0"

git commit -m "chore: Bump version to 1.8.0"
git push origin main

# Tag release
git tag -a v1.8.0 -m "Release v1.8.0"
git push origin v1.8.0

# → CD crée GitHub Release automatiquement
```

---

## Déploiement Production

### Docker Compose (Recommandé Phase 1)

```bash
# Pull latest images
cd Scripts/Deployment
docker-compose pull

# Restart services
docker-compose up -d

# Vérifier santé
curl http://localhost:8000/api/health
curl http://localhost/
```

### Script Automatisé

```bash
./Scripts/Deployment/deploy-phase1.sh
```

---

## Vérification du Setup

### Script de vérification automatique

```bash
./Scripts/verify-ci-setup.sh
```

**Vérifie:**
- Workflows GitHub Actions
- Configuration backend/frontend
- Tests
- Git configuration
- Documentation
- Linters locaux

### Vérification manuelle

```bash
# 1. Workflows existent
ls .github/workflows/
# → ci.yml, cd.yml, security.yml

# 2. Linters fonctionnent
cd backend && ruff check .
cd ../frontend && npm run lint

# 3. Tests passent
cd backend && pytest -m unit
```

---

## Pre-commit Hooks

**Installation:**

```bash
pip install pre-commit
pre-commit install
```

**Usage:**

```bash
git commit
# → Hooks s'exécutent automatiquement
# → Ruff, Black, isort, detect-secrets, etc.
```

**Test manuel:**

```bash
pre-commit run --all-files
```

---

## Sécurité - Considérations Médicales

### Compliance HIPAA/GDPR

Le workflow Security inclut des vérifications spécifiques:

```bash
# Pas de données patient (PHI) dans le code
! grep -r "SSN|patient.?id|medical.?record"

# Pas de secrets hardcodés
! grep -r "password.*=.*['\"]"

# HTTPS uniquement (sauf localhost)
! grep -r "http://(?!localhost)"
```

### Best Practices

1. **Jamais logger de données patient**
   ```python
   # ❌ MAUVAIS
   logger.info(f"Slide for patient {patient_id}")

   # ✅ BON
   logger.info(f"Slide {slide_id} loaded")
   ```

2. **Toujours chiffrer en transit**
   - TLS/HTTPS en production
   - Pas de HTTP en dehors de localhost

3. **Audit logging**
   - Toutes actions sur slides loggées
   - Timestamp, user, action, slide_id

---

## Monitoring

### GitHub Actions UI

**Actions tab:** https://github.com/<owner>/varunapoc/actions

**Security tab:** https://github.com/<owner>/varunapoc/security

### Métriques

- **CI:** ~5-7 min (parallélisé)
- **CD:** ~8-12 min
- **Security:** ~10-15 min
- **Taux de succès attendu:** >95%

---

## Troubleshooting

### CI échoue sur "OpenSlide not found"

**Solution:** Déjà installé dans CI. Si problème persiste, vérifier `config_openslide.py`.

### CD échoue sur "permission denied" GHCR

**Solution:** Vérifier permissions dans workflow:

```yaml
permissions:
  contents: read
  packages: write  # ← Requis pour GHCR push
```

### Security scan trouve des vulnérabilités

**Solution:** Update dépendances

```bash
# Backend
pip install --upgrade <package>
pip freeze > requirements.txt

# Frontend
npm update <package>
```

---

## Fichiers Créés

### GitHub Actions (4 fichiers)

- `.github/workflows/ci.yml` - Pipeline CI
- `.github/workflows/cd.yml` - Pipeline CD
- `.github/workflows/security.yml` - Scans sécurité
- `.github/workflows/README.md` - Documentation workflows

### Backend (7 fichiers)

- `backend/ruff.toml` - Config Ruff
- `backend/pyproject.toml` - Config Black, isort, pytest
- `backend/tests/__init__.py` - Module tests
- `backend/tests/conftest.py` - Fixtures pytest
- `backend/tests/test_health.py` - Tests health checks (7 tests)
- `backend/tests/test_slides_api.py` - Tests API (6 tests)
- `backend/tests/README.md` - Documentation tests

### Frontend (1 fichier + 1 modifié)

- `frontend/.eslintrc.json` - Config ESLint
- `frontend/package.json` - Ajout scripts lint + dep ESLint

### Git (2 modifiés)

- `.gitignore` - Ajout patterns CI/CD
- `.pre-commit-config.yaml` - Activation hooks Python

### Documentation (3 fichiers)

- `CI_CD_GUIDE.md` - Guide complet CI/CD
- `CI_CD_FILES_SUMMARY.md` - Résumé fichiers créés
- `PIPELINE_CI_CD_FR.md` - Ce fichier (version française)

### Scripts (1 fichier)

- `Scripts/verify-ci-setup.sh` - Script de vérification

**Total:** 19 fichiers créés/modifiés

---

## Prochaines Étapes

### Immédiat

- [ ] Vérifier setup: `./Scripts/verify-ci-setup.sh`
- [ ] Installer pre-commit: `pre-commit install`
- [ ] Créer PR de test pour valider CI

### Phase 1 (1-2 semaines)

- [ ] Augmenter coverage tests à 60%+
- [ ] Configurer Codecov (optionnel)
- [ ] Ajouter tests d'intégration avec slides de test

### Phase 2 (1-2 mois)

- [ ] Staging environment automatique
- [ ] Performance benchmarking (tile load time)
- [ ] Tests E2E avec Playwright

### Phase 3 (Production)

- [ ] Kubernetes deployment automation
- [ ] Blue-green deployments
- [ ] Production monitoring (Prometheus + Grafana)

---

## Documentation Complète

- **Guide rapide:** `CI_CD_GUIDE.md`
- **Workflows détaillés:** `.github/workflows/README.md`
- **Tests backend:** `backend/tests/README.md`
- **Fichiers créés:** `CI_CD_FILES_SUMMARY.md`
- **Déploiement Docker:** `DOCKER_DEPLOYMENT_CHECKLIST.md`

---

## Support

**Questions:** GitHub Issues avec label `ci/cd`

**Documentation:** Voir fichiers listés ci-dessus

---

**Auteur:** Infrastructure Architect Agent
**Date:** 2026-02-05
**Version:** 1.0.0
**Projet:** VarunaPoC - Digital Pathology Slide Viewer
