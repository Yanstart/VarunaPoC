# VarunaPoC Backend Tests

Suite de tests pour le backend FastAPI + OpenSlide.

## Structure

```
backend/tests/
├── README.md                # Ce fichier
├── __init__.py              # Module initialization
├── conftest.py              # Shared pytest fixtures
├── test_health.py           # Health checks & basic endpoints (7 tests)
└── test_slides_api.py       # Slides API endpoints (6 tests)
```

## Exécution

### Tous les tests

```bash
cd backend
pytest
```

**Résultat attendu:**
```
==================== test session starts ====================
collected 13 items

tests/test_health.py ........                          [61%]
tests/test_slides_api.py .....sss                      [100%]

============= 10 passed, 3 skipped in 2.34s ================
```

### Tests unitaires uniquement (rapides)

```bash
pytest -m unit
```

**Durée:** ~2-3 secondes

**Tests unitaires:**
- Pas de dépendances externes (OpenSlide, fichiers slides)
- Mock des services
- Test de la logique FastAPI

### Tests d'intégration

```bash
pytest -m integration
```

**Durée:** ~10-30 secondes (dépend des slides)

**Requirements:**
- OpenSlide installé sur le système
- Slides de test dans `/Slides` ou `mock_slides_dir`

**Par défaut:** Skippés en CI (pas de slides disponibles)

### Avec coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

**Résultats:**
- Terminal: Résumé avec lignes manquantes
- HTML: `htmlcov/index.html` (détaillé)

**Coverage actuel:** Baseline ~40-50% (à améliorer progressivement)

**Objectif:** 60%+ pour Phase 2

---

## Markers Pytest

### `@pytest.mark.unit`

Tests rapides sans dépendances externes.

**Usage:**
```python
@pytest.mark.unit
def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
```

**Quand utiliser:**
- Health checks
- Validation de schémas
- Logique métier pure
- Tests de FastAPI routing

### `@pytest.mark.integration`

Tests nécessitant OpenSlide ou slides réelles.

**Usage:**
```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires test slides")
def test_slide_info(client):
    response = client.get("/api/slides/test_001/info")
    assert response.status_code == 200
```

**Quand utiliser:**
- Chargement de slides
- Génération de tiles
- Tests avec OpenSlide
- Tests de performance

### `@pytest.mark.slow`

Tests longs (> 10 secondes).

**Usage:**
```python
@pytest.mark.slow
def test_large_slide_full_scan():
    # Scan complet d'une lame de 10GB
    ...
```

**Exécution:**
```bash
pytest -m "not slow"  # Exclure tests lents
pytest -m slow        # Uniquement tests lents
```

---

## Fixtures

Définies dans `conftest.py`, disponibles automatiquement dans tous les tests.

### `client`

FastAPI test client.

**Type:** `TestClient`

**Usage:**
```python
def test_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Documentation:** https://fastapi.tiangolo.com/tutorial/testing/

### `mock_slides_dir`

Répertoire temporaire pour slides de test.

**Type:** `pathlib.Path`

**Structure créée:**
```
tmp_path/Slides/
├── 3Dhistec/      # Mock folder
└── ROCHE/         # Mock folder
```

**Usage:**
```python
def test_scanner_service(mock_slides_dir):
    scanner = SlideScanner(slides_dir=mock_slides_dir)
    folders = scanner.scan()
    assert len(folders) == 2
```

### `sample_slide_metadata`

Métadonnées de slide de test (format OpenSlide).

**Type:** `dict`

**Contenu:**
```python
{
    "slide_id": "test_slide_001",
    "format": "mrxs",
    "vendor": "3DHistech",
    "dimensions": {"width": 100000, "height": 80000},
    "level_count": 9,
    "mpp_x": 0.25,
    "mpp_y": 0.25,
    "objective_power": 40,
}
```

**Usage:**
```python
def test_metadata_validation(sample_slide_metadata):
    assert sample_slide_metadata["vendor"] == "3DHistech"
    assert sample_slide_metadata["level_count"] == 9
```

---

## Tests Actuels

### `test_health.py` - Health Checks (7 tests unitaires)

| Test | Description | Durée |
|------|-------------|-------|
| `test_root_endpoint` | GET / → Service info | ~10ms |
| `test_health_endpoint` | GET /api/health → Status | ~5ms |
| `test_docs_endpoint` | GET /docs → Swagger UI | ~20ms |
| `test_openapi_endpoint` | GET /openapi.json → Schema | ~15ms |
| `test_metrics_endpoint_when_monitoring_enabled` | GET /metrics → Prometheus | ~10ms |
| `test_cors_headers` | OPTIONS → CORS preflight | ~10ms |

**Total:** ~70ms

**Coverage:** 100% des endpoints health

### `test_slides_api.py` - Slides API (6 tests)

| Test | Description | Status | Durée |
|------|-------------|--------|-------|
| `test_browse_endpoint_requires_path` | GET /api/slides/browse sans path | ✅ | ~10ms |
| `test_slides_list_endpoint` | GET /api/slides/ | ✅ | ~50ms |
| `test_browse_endpoint_with_valid_path` | GET /api/slides/browse?path=/Slides | ⏭️ Skipped | - |
| `test_slide_info_endpoint` | GET /api/slides/{id}/info | ⏭️ Skipped | - |
| `test_slide_overview_endpoint` | GET /api/slides/{id}/overview | ⏭️ Skipped | - |
| `test_invalid_slide_id` | GET /api/slides/nonexistent/info → 404 | ✅ | ~10ms |
| `test_api_version_consistency` | Version cohérente partout | ✅ | ~20ms |

**Skipped tests:** Nécessitent slides de test (Phase 2)

---

## Ajouter de nouveaux tests

### 1. Tests unitaires (recommandé pour démarrer)

```python
# backend/tests/test_new_feature.py

import pytest

@pytest.mark.unit
def test_new_endpoint(client):
    """
    Test du nouvel endpoint GET /api/new-feature.

    Vérifie que l'endpoint retourne le bon format.
    """
    response = client.get("/api/new-feature")

    assert response.status_code == 200

    data = response.json()
    assert "result" in data
    assert data["result"] == "expected_value"
```

### 2. Tests d'intégration (avec slides réelles)

```python
# backend/tests/test_integration.py

import pytest

@pytest.mark.integration
def test_load_real_slide(client):
    """
    Test chargement d'une vraie lame MRXS.

    Requires: Slide de test dans /Slides/test_slide.mrxs
    """
    response = client.get("/api/slides/test_slide/info")

    assert response.status_code == 200

    data = response.json()
    assert data["format"] == "mrxs"
    assert data["vendor"] == "3DHistech"
```

### 3. Tests avec fixtures custom

```python
# backend/tests/conftest.py (ajouter nouvelle fixture)

@pytest.fixture
def mock_openslide_instance():
    """Mock d'une instance OpenSlide pour tests."""
    class MockOpenSlide:
        level_count = 9
        dimensions = (100000, 80000)

        def get_thumbnail(self, size):
            # Retourner une image PIL mock
            from PIL import Image
            return Image.new("RGB", size, color="red")

    return MockOpenSlide()
```

---

## Best Practices

### 1. Noms de tests descriptifs

```python
# ❌ MAUVAIS
def test_1():
    ...

# ✅ BON
def test_health_endpoint_returns_healthy_status():
    ...
```

### 2. AAA Pattern (Arrange-Act-Assert)

```python
def test_slide_info_endpoint(client):
    # Arrange
    slide_id = "test_slide_001"

    # Act
    response = client.get(f"/api/slides/{slide_id}/info")

    # Assert
    assert response.status_code == 200
    assert response.json()["slide_id"] == slide_id
```

### 3. Un test = une assertion principale

```python
# ❌ MAUVAIS (trop d'assertions)
def test_everything(client):
    assert client.get("/").status_code == 200
    assert client.get("/api/health").status_code == 200
    assert client.get("/docs").status_code == 200

# ✅ BON (tests séparés)
def test_root_endpoint(client):
    assert client.get("/").status_code == 200

def test_health_endpoint(client):
    assert client.get("/api/health").status_code == 200
```

### 4. Skip tests d'intégration avec raison claire

```python
@pytest.mark.integration
@pytest.mark.skip(reason="Requires /Slides directory with test slides")
def test_slides_browse():
    ...
```

### 5. Documenter les tests

```python
def test_complex_scenario(client):
    """
    Test scénario complexe de navigation.

    Steps:
    1. Browse root folder
    2. Navigate to subfolder
    3. Load slide info
    4. Verify metadata

    Expected: All steps succeed without errors
    """
    ...
```

---

## Troubleshooting

### Erreur: "ModuleNotFoundError: No module named 'main'"

**Cause:** Tests exécutés depuis mauvais répertoire.

**Solution:**
```bash
cd backend  # ← IMPORTANT
pytest
```

### Erreur: "OpenSlide not found"

**Cause:** OpenSlide non installé sur le système.

**Solution:**
```bash
# Linux
sudo apt-get install openslide-tools libopenslide0

# macOS
brew install openslide

# Windows
# Télécharger depuis https://openslide.org/download/
```

### Erreur: "ImportError: cannot import name 'app'"

**Cause:** Problème de configuration OpenSlide (config_openslide.py).

**Solution:** Vérifier que `config_openslide.py` fonctionne avant import de `main.py`.

### Tests skippés en CI

**Cause:** Normal si tests marqués `@pytest.mark.skip`.

**Solution:** Pour exécuter quand même:
```bash
pytest --run-skipped
```

---

## CI/CD Integration

### GitHub Actions

Les tests sont exécutés automatiquement dans `.github/workflows/ci.yml`:

```yaml
- name: Run pytest
  run: |
    cd backend
    pytest --cov=. --cov-report=xml --cov-report=term-missing --verbose
```

**Coverage uploadé vers Codecov** (optionnel).

### Pre-commit Hooks

Pas de tests dans pre-commit (trop lent).

Uniquement linting (ruff, black, isort).

---

## Prochaines Étapes

### Phase 1 (Actuel)

- [x] Tests health checks (7 tests)
- [x] Tests API basiques (3 tests passants)
- [ ] Augmenter coverage à 60%+
- [ ] Ajouter tests pour services (SlideScanner, SlideLoader)

### Phase 2

- [ ] Tests d'intégration avec vraies lames
- [ ] Tests de performance (tile load time < 100ms)
- [ ] Tests de régression (non-régression formats)

### Phase 3

- [ ] Tests E2E avec Playwright
- [ ] Load testing (k6 ou Locust)
- [ ] Chaos engineering (failures handling)

---

## Ressources

### Documentation

- **pytest:** https://docs.pytest.org/
- **FastAPI Testing:** https://fastapi.tiangolo.com/tutorial/testing/
- **pytest-cov:** https://pytest-cov.readthedocs.io/

### Exemples

- **FastAPI Tests:** https://github.com/tiangolo/fastapi/tree/master/tests
- **OpenSlide Tests:** https://github.com/openslide/openslide-python/tree/main/tests

---

**Dernière mise à jour:** 2026-02-05
**Coverage actuel:** ~45%
**Objectif:** 60%+
