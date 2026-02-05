# CI/CD Pipeline Documentation

Pipeline automatisé pour VarunaPoC - Digital Pathology Slide Viewer.

## Vue d'ensemble

Trois workflows GitHub Actions garantissent la qualité et la sécurité du code médical:

1. **CI - Continuous Integration** (`.github/workflows/ci.yml`)
2. **CD - Continuous Deployment** (`.github/workflows/cd.yml`)
3. **Security Scanning** (`.github/workflows/security.yml`)

## Workflow 1: CI - Continuous Integration

**Déclencheurs:**
- Pull Requests vers `main` ou `develop`
- Push vers `main` ou `develop`

**Jobs exécutés:**

### Backend

| Job | Description | Durée estimée |
|-----|-------------|---------------|
| `backend-lint` | Ruff + Black + isort | ~30s |
| `backend-test` | pytest avec coverage | ~1-2min |
| `backend-docker` | Build et test image Docker | ~2-3min |

**Outils de linting:**
- **Ruff**: Linter ultra-rapide (100x plus rapide que Flake8)
- **Black**: Formatage automatique du code Python
- **isort**: Tri des imports

**Tests:**
- Pytest avec couverture de code
- Tests unitaires (rapides, pas de dépendances)
- Tests d'intégration (OpenSlide, skippés si pas de slides)
- Upload coverage vers Codecov (optionnel)

### Frontend

| Job | Description | Durée estimée |
|-----|-------------|---------------|
| `frontend-lint` | ESLint | ~20s |
| `frontend-build` | Vite build production | ~1min |
| `frontend-docker` | Build et test image Docker | ~2min |

**Linting:**
- ESLint avec règles strictes
- Pas de console.log en prod
- Pas de debugger statements

### Intégration

| Job | Description | Durée estimée |
|-----|-------------|---------------|
| `integration` | Test backend ↔ frontend | ~2min |

**Tests:**
- Lance backend et frontend dans Docker
- Vérifie communication API
- Health checks

**Temps total:** ~5-7 minutes par PR

---

## Workflow 2: CD - Continuous Deployment

**Déclencheurs:**
- Push vers `main` (automatique après merge)
- Tags `v*.*.*` (releases)

**Jobs exécutés:**

### 1. Build and Push

**Actions:**
- Build images Docker backend et frontend
- Push vers GitHub Container Registry (ghcr.io)
- Tags automatiques:
  - `latest` (branch main)
  - `v1.2.3` (si tag Git)
  - `main-abc1234` (Git SHA)

**Registry:**
```bash
ghcr.io/<owner>/varunapoc/backend:latest
ghcr.io/<owner>/varunapoc/frontend:latest
```

**Attestation de build:**
- Signature cryptographique des images (SLSA provenance)
- Vérifiable avec `gh attestation verify`

### 2. Create Release (tags uniquement)

**Actions:**
- Génère changelog automatique depuis PRs
- Crée GitHub Release avec notes de version
- Attache les images Docker

### 3. Update Manifest

**Actions:**
- Met à jour `Scripts/Deployment/docker-compose.yml`
- Commit automatique avec nouveau tag d'image
- Prêt pour GitOps deployment

**Temps total:** ~8-12 minutes

---

## Workflow 3: Security Scanning

**Déclencheurs:**
- Pull Requests
- Push vers main/develop
- Schedule quotidien (2 AM UTC)
- Manuel (`workflow_dispatch`)

**Jobs exécutés:**

### 1. Dependency Vulnerability Scan

**Outil:** Trivy (Aqua Security)

**Scanne:**
- `requirements.txt` (Python)
- `package.json` (JavaScript)

**Sévérités:** CRITICAL, HIGH, MEDIUM

**Résultats:**
- Upload vers GitHub Security tab (SARIF format)
- Pas de fail automatique (just warnings)

### 2. Python Security

**Outils:**
- **Bandit**: Détection de vulnérabilités Python (SQL injection, etc.)
- **Safety**: Vérification des dépendances Python
- **pip-audit**: Audit OSV (Open Source Vulnerabilities)

### 3. JavaScript Security

**Outil:** `npm audit`

**Détecte:**
- Dépendances vulnérables
- Conflits de versions

### 4. Docker Image Scan

**Outil:** Trivy

**Scanne:**
- Images Docker finales
- OS vulnerabilities (Debian/Alpine)
- Librairies système (OpenSlide, Nginx)

### 5. CodeQL Analysis

**Outil:** GitHub CodeQL (SAST)

**Analyse:**
- Code Python et JavaScript
- Patterns de sécurité (OWASP)
- Queries extended security

### 6. Secret Scanning

**Outil:** Gitleaks

**Détecte:**
- API keys hardcodées
- Passwords dans le code
- Tokens dans l'historique Git

### 7. HIPAA/GDPR Compliance

**Checks custom:**

```bash
# Pas de données patient (PHI) dans le code
! grep -r "SSN|patient.?id|medical.?record"

# Pas de secrets hardcodés
! grep -r "password.*=.*['\"]"

# Pas de HTTP non-sécurisé (require HTTPS)
! grep -r "http://(?!localhost)"
```

**Important pour contexte médical:**
- Toute manipulation de données HIPAA/GDPR doit être logged
- Encryption at rest et in transit obligatoire
- Pas de logging de données patient

**Temps total:** ~10-15 minutes

---

## Configuration Requise

### Secrets GitHub

| Secret | Usage | Requis |
|--------|-------|--------|
| `GITHUB_TOKEN` | CI/CD, GHCR push | Auto (fourni par GitHub) |
| `CODECOV_TOKEN` | Upload coverage | Optionnel |
| `PROJECT_TOKEN` | Update GitHub Project | Optionnel (existe déjà) |

### Branch Protection Rules

Recommandé pour `main`:

```yaml
Require status checks to pass:
  - CI Status
  - backend-lint
  - backend-test
  - frontend-lint
  - frontend-build
  - integration

Require review from Code Owners: true
Require linear history: true
Include administrators: false
```

---

## Utilisation

### Pour les Développeurs

**Pull Request:**

```bash
# Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# Coder...
# Committer...

# Pousser
git push origin feature/nouvelle-fonctionnalite

# Créer PR sur GitHub
# → CI démarre automatiquement
# → Reviewer le code
# → Merger si CI passe
```

**Check local avant push:**

```bash
# Backend lint
cd backend
ruff check .
black --check .
isort --check .

# Backend tests
pytest

# Frontend lint
cd frontend
npm run lint

# Frontend build
npm run build
```

### Release Process

**Créer une nouvelle version:**

```bash
# 1. Update version dans:
#    - backend/main.py (version="1.8.0")
#    - frontend/package.json (version: "1.8.0")

# 2. Commit et push vers main
git commit -m "chore: Bump version to 1.8.0"
git push origin main

# 3. Créer tag Git
git tag -a v1.8.0 -m "Release v1.8.0"
git push origin v1.8.0

# → CD démarre automatiquement
# → Images taguées avec v1.8.0
# → GitHub Release créée
```

### Déployer en Production

**Option 1: Docker Compose (recommandé Phase 1)**

```bash
# Pull latest images
docker-compose -f Scripts/Deployment/docker-compose.yml pull

# Restart services
docker-compose -f Scripts/Deployment/docker-compose.yml up -d
```

**Option 2: Kubernetes (Phase 3)**

```bash
# Update Helm values
helm upgrade varuna ./helm/varuna \
  --set backend.image.tag=v1.8.0 \
  --set frontend.image.tag=v1.8.0

# Verify rollout
kubectl rollout status deployment/varuna-backend
```

---

## Monitoring

### GitHub Actions UI

- **Actions tab:** https://github.com/<owner>/<repo>/actions
- **Security tab:** https://github.com/<owner>/<repo>/security

### Métriques CI/CD

**Temps de build:**
- CI complet: ~5-7 min
- CD complet: ~8-12 min
- Security scan: ~10-15 min

**Taux de succès attendu:** >95%

**Échecs communs:**

| Échec | Cause | Solution |
|-------|-------|----------|
| Ruff lint fail | Code non formaté | `black . && isort .` |
| ESLint fail | console.log en prod | Retirer ou utiliser console.warn |
| Docker build timeout | Cache invalidé | Re-run workflow |
| pytest fail | Test cassé | Fix test ou code |

---

## Optimisations

### Caching

**Layers Docker:**
- Cache GitHub Actions (type=gha)
- Partagé entre workflows
- Réduit temps de build de 80%

**Dependencies:**
- pip cache (Python)
- npm cache (JavaScript)
- Restored automatiquement par `actions/setup-python` et `actions/setup-node`

### Parallélisation

**CI:**
- Backend et frontend en parallèle
- Lint et tests séparés
- Total ~5min au lieu de 15min séquentiel

**CD:**
- Backend et frontend builds en parallèle (matrix strategy)

---

## Troubleshooting

### CI échoue sur "OpenSlide not found"

**Problème:** Tests nécessitent OpenSlide système.

**Solution:** Déjà installé dans CI:
```yaml
- name: Install OpenSlide
  run: sudo apt-get install -y openslide-tools libopenslide0
```

### CD échoue sur "permission denied" GHCR

**Problème:** Pas de permission d'écriture sur GitHub Container Registry.

**Solution:** Vérifier permissions workflow:
```yaml
permissions:
  contents: read
  packages: write
```

### Security scan trouve des vulnérabilités

**Problème:** Dépendances obsolètes ou vulnérables.

**Solution:**
```bash
# Backend
pip install --upgrade <package>
pip freeze > requirements.txt

# Frontend
npm update <package>
```

---

## Best Practices

1. **Toujours run tests localement avant push**
2. **Pas de `--no-verify` sur git commit** (bypass pre-commit hooks)
3. **Semantic commit messages:** `feat:`, `fix:`, `docs:`, `chore:`
4. **Pas de force push sur main/develop**
5. **Review security tab régulièrement**

---

## Ressources

### Documentation Officielle

- **GitHub Actions:** https://docs.github.com/en/actions
- **Docker Build Push:** https://github.com/docker/build-push-action
- **Trivy:** https://aquasecurity.github.io/trivy/
- **CodeQL:** https://codeql.github.com/docs/

### Outils

- **Ruff:** https://docs.astral.sh/ruff/
- **Black:** https://black.readthedocs.io/
- **ESLint:** https://eslint.org/
- **pytest:** https://docs.pytest.org/

---

**Dernière mise à jour:** 2026-02-05
**Version pipeline:** 1.0.0
