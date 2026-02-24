# CI/CD Pipeline Guide

Pipeline automatisé pour VarunaPoC garantissant qualité, sécurité et déploiement fiable.

## TL;DR - Quick Start

```bash
# 1. Créer une PR
git checkout -b feature/ma-fonctionnalite
# ... coder ...
git push origin feature/ma-fonctionnalite

# 2. GitHub Actions démarre automatiquement:
#    - Lint (Ruff, ESLint)
#    - Tests (pytest)
#    - Build Docker
#    - Security scans

# 3. Merger PR → CD automatique:
#    - Build images Docker
#    - Push vers ghcr.io
#    - Prêt pour déploiement
```

## Workflows

### 1. CI - Continuous Integration

**Fichier:** `.github/workflows/ci.yml`

**Déclencheurs:**
- Pull Requests vers `main` ou `develop`
- Push vers `main` ou `develop`

**Vérifications:**

| Composant | Check | Temps |
|-----------|-------|-------|
| **Backend** | Ruff linting | ~30s |
| | Black formatting | ~20s |
| | pytest + coverage | ~1-2min |
| | Docker build | ~2-3min |
| **Frontend** | ESLint | ~20s |
| | Vite build | ~1min |
| | Docker build | ~2min |
| **Integration** | Backend ↔ Frontend | ~2min |

**Total:** ~5-7 minutes

**Status requis pour merge:** CI Status (combiné)

---

### 2. CD - Continuous Deployment

**Fichier:** `.github/workflows/cd.yml`

**Déclencheurs:**
- Push vers `main` (après merge PR)
- Tags `v*.*.*` (releases officielles)

**Actions:**

1. **Build and Push**
   - Build images Docker backend et frontend
   - Push vers GitHub Container Registry (ghcr.io)
   - Tags: `latest`, `v1.2.3`, `main-abc1234`

2. **Create Release** (si tag Git)
   - Génère changelog automatique
   - Crée GitHub Release
   - Attache images Docker

3. **Update Manifest**
   - Met à jour `Scripts/Deployment/docker-compose.yml`
   - Commit automatique avec nouveau tag

**Total:** ~8-12 minutes

---

### 3. Security Scanning

**Fichier:** `.github/workflows/security.yml`

**Déclencheurs:**
- Pull Requests
- Push vers main/develop
- Quotidien à 2 AM UTC
- Manuel (`workflow_dispatch`)

**Scans:**

| Type | Outil | Cible |
|------|-------|-------|
| **Dependency Vulnerabilities** | Trivy | requirements.txt, package.json |
| **Python Security** | Bandit, Safety, pip-audit | Code Python |
| **JavaScript Security** | npm audit | Code JavaScript |
| **Docker Images** | Trivy | Images finales |
| **Code Analysis (SAST)** | CodeQL | Python + JavaScript |
| **Secret Detection** | Gitleaks | Historique Git |
| **HIPAA/GDPR Compliance** | Custom checks | PHI/PII patterns |

**Total:** ~10-15 minutes

**Important:** Projet médical donc sécurité = priorité absolue.

---

## Configuration des Linters

### Backend (Python)

**Ruff** - Linter ultra-rapide (Rust-based)
```toml
# backend/ruff.toml
target-version = "py311"
line-length = 100
select = ["E", "F", "I", "B", "PL", ...]
```

**Black** - Formatage automatique
```toml
# backend/pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**Usage:**
```bash
cd backend
ruff check .              # Vérifier
ruff check --fix .        # Corriger automatiquement
black .                   # Formatter
isort .                   # Trier imports
```

### Frontend (JavaScript)

**ESLint**
```json
// frontend/.eslintrc.json
{
  "extends": ["eslint:recommended"],
  "rules": {
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "no-debugger": "error",
    "prefer-const": "error"
  }
}
```

**Usage:**
```bash
cd frontend
npm run lint              # Vérifier
npm run lint:fix          # Corriger automatiquement
```

---

## Tests

### Backend Tests

**Structure:**
```
backend/tests/
├── __init__.py
├── conftest.py              # Fixtures partagées
├── test_health.py           # Health checks (unitaires)
└── test_slides_api.py       # API slides (intégration)
```

**Exécution:**
```bash
cd backend

# Tous les tests
pytest

# Tests unitaires uniquement (rapides)
pytest -m unit

# Tests d'intégration (require OpenSlide)
pytest -m integration

# Avec coverage
pytest --cov=. --cov-report=html
# → Ouvrir htmlcov/index.html
```

**Markers:**
- `@pytest.mark.unit` - Tests rapides, pas de dépendances
- `@pytest.mark.integration` - Require OpenSlide + slides test
- `@pytest.mark.slow` - Tests avec vraies lames (> 10s)

**Current coverage:** Baseline établi, à améliorer progressivement.

---

## Images Docker

### Registry: GitHub Container Registry (ghcr.io)

**Pull images:**
```bash
# Latest (main branch)
docker pull ghcr.io/<owner>/varunapoc/backend:latest
docker pull ghcr.io/<owner>/varunapoc/frontend:latest

# Version spécifique
docker pull ghcr.io/<owner>/varunapoc/backend:v1.7.0
docker pull ghcr.io/<owner>/varunapoc/frontend:v1.7.0
```

**Vérifier authenticité (SLSA provenance):**
```bash
gh attestation verify oci://ghcr.io/<owner>/varunapoc/backend:latest \
  --owner <owner>
```

---

## Workflow Développeur

### 1. Développement Local

```bash
# Créer branche feature
git checkout -b feature/nouvelle-fonctionnalite

# Coder...

# Check local AVANT push
cd backend
ruff check .
black --check .
pytest

cd ../frontend
npm run lint
npm run build

# Commit
git add .
git commit -m "feat: Ajouter nouvelle fonctionnalité"

# Push
git push origin feature/nouvelle-fonctionnalite
```

### 2. Pull Request

```bash
# Créer PR sur GitHub
# → CI démarre automatiquement
# → Attendre résultat CI (~5-7min)
# → Reviewer code
# → Merger si CI passe
```

**CI checks:**
- ✅ Backend lint
- ✅ Backend tests
- ✅ Backend Docker build
- ✅ Frontend lint
- ✅ Frontend build
- ✅ Frontend Docker build
- ✅ Integration test

**Status:** CI Status (global)

### 3. Merge vers Main

```bash
# Merger PR sur GitHub
# → CD démarre automatiquement
# → Images Docker publiées sur ghcr.io
# → docker-compose.yml mis à jour
```

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

### Option 1: Docker Compose (Phase 1 - Recommandé)

```bash
# 1. Pull latest images
cd Scripts/Deployment
docker-compose pull

# 2. Restart services
docker-compose up -d

# 3. Vérifier santé
curl http://localhost:8000/api/health
curl http://localhost/
```

### Option 2: Script automatisé

```bash
./Scripts/Deployment/deploy-phase1.sh
```

### Option 3: Kubernetes (Phase 3 - Future)

```bash
helm upgrade --install varuna ./helm/varuna \
  --set backend.image.tag=v1.8.0 \
  --set frontend.image.tag=v1.8.0 \
  --namespace production

kubectl rollout status deployment/varuna-backend -n production
```

---

## Monitoring CI/CD

### GitHub Actions UI

**Actions tab:** https://github.com/<owner>/varunapoc/actions

**Security tab:** https://github.com/<owner>/varunapoc/security
- Dependabot alerts
- Code scanning alerts (CodeQL)
- Secret scanning alerts

### Métriques

**Temps de build moyens:**
- CI: ~5-7 min
- CD: ~8-12 min
- Security: ~10-15 min

**Taux de succès attendu:** >95%

**Échecs fréquents:**
- Ruff lint fail → Formatter avec `black . && isort .`
- ESLint fail → `npm run lint:fix`
- pytest fail → Fix test ou code
- Docker build timeout → Re-run workflow (cache invalidé)

---

## Secrets et Configuration

### Secrets GitHub

| Secret | Usage | Requis |
|--------|-------|--------|
| `GITHUB_TOKEN` | CI/CD, GHCR push | ✅ Auto |
| `CODECOV_TOKEN` | Upload coverage | Optionnel |
| `PROJECT_TOKEN` | Update GitHub Project | ✅ Existe |

**GITHUB_TOKEN** est fourni automatiquement par GitHub Actions.

### Variables d'environnement

**Backend:**
- `CORS_ORIGINS` - Origins autorisées (default: localhost)
- `SLIDES_DIR` - Répertoire des lames (default: /Slides)

**Frontend:**
- `VITE_API_URL` - URL backend (build-time)

---

## Sécurité - HIPAA/GDPR

### Compliance Checks

Le workflow Security inclut des checks spécifiques médicaux:

```bash
# Pas de PHI dans le code
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

4. **Pas de secrets dans code**
   - Utiliser variables d'environnement
   - Secrets GitHub pour CI/CD

---

## Troubleshooting

### CI échoue sur "OpenSlide not found"

**Solution:** Déjà installé dans workflow CI:
```yaml
- name: Install OpenSlide
  run: sudo apt-get install -y openslide-tools libopenslide0
```

Si problème persiste → Vérifier `config_openslide.py`

### CD échoue sur "permission denied" GHCR

**Solution:** Vérifier permissions:
```yaml
permissions:
  contents: read
  packages: write  # ← Requis pour GHCR push
```

### Security scan trouve vulnérabilités

**Solution:** Update dépendances
```bash
# Backend
pip install --upgrade <package>
pip freeze > requirements.txt

# Frontend
npm update <package>
```

### Tests pytest échouent en CI mais pas localement

**Causes possibles:**
1. Dépendances manquantes dans requirements.txt
2. Chemins absolus hardcodés (utiliser `Path(__file__).parent`)
3. Timezone differences (utiliser UTC)

---

## Ressources

### Documentation

- **Workflows détaillés:** `.github/workflows/README.md`
- **Tests backend:** `backend/tests/README.md` (à créer)
- **Docker deployment:** `DOCKER_DEPLOYMENT_CHECKLIST.md`

### Outils

- **Ruff:** https://docs.astral.sh/ruff/
- **Black:** https://black.readthedocs.io/
- **ESLint:** https://eslint.org/
- **pytest:** https://docs.pytest.org/
- **Trivy:** https://aquasecurity.github.io/trivy/
- **CodeQL:** https://codeql.github.com/

### GitHub Actions

- **Actions docs:** https://docs.github.com/en/actions
- **Workflow syntax:** https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions

---

## Prochaines Étapes

### Phase 1 (Actuel)
- [x] CI/CD pipeline de base
- [x] Tests unitaires
- [ ] Augmenter coverage à 60%+
- [ ] Pre-commit hooks locaux

### Phase 2
- [ ] Tests d'intégration avec vraies lames
- [ ] Performance benchmarking (tile load time)
- [ ] Staging environment automatique

### Phase 3
- [ ] Kubernetes deployment
- [ ] Blue-green deployments
- [ ] Canary releases
- [ ] Production monitoring (Prometheus/Grafana)

---

**Dernière mise à jour:** 2026-02-05
**Version:** 1.0.0
**Contact:** VarunaPoC Team
