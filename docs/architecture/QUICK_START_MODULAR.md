# Quick Start - Architecture Modulaire

**Pour développeurs pressés qui veulent comprendre rapidement.**

---

## 1. Concept en 30 secondes

**Avant (Phase 1 - Monolithique):**
```python
# tile_server.py - TOUT couplé
def get_tile(slide_path, level, col, row):
    slide = openslide.OpenSlide(slide_path)  # ← Couplé à OpenSlide
    region = slide.read_region(...)           # ← Couplé à filesystem
    return region                             # ← Pas de cache
```

**Après (Phase 2 - Modulaire):**
```python
# tile_server.py - Interfaces injectées
def __init__(self, storage: StorageProvider, loader: SlideLoader, cache: TileCache):
    self.storage = storage  # ← Interface (peut être filesystem, S3, PACS)
    self.loader = loader    # ← Interface (peut être OpenSlide, Bio-Formats, custom)
    self.cache = cache      # ← Interface (peut être Redis, NoOp, CDN)

async def get_tile(self, slide_id, level, col, row):
    cached = await self.cache.get_tile(...)  # Check cache
    if cached:
        return cached

    path = await self.storage.get_slide_path(slide_id)  # Abstraction storage
    tile = self.loader.read_region(path, ...)            # Abstraction loader
    await self.cache.set_tile(..., tile)                 # Set cache

    return tile
```

**Bénéfices:**
- Swap `storage` sans changer `tile_server`
- Tests avec mocks (pas besoin Redis/S3 réel)
- Ajout fonctionnalités (ML, PACS) sans réé criture

---

## 2. Structures de Dossiers (5 minutes)

```
backend/
├── core/                       # ← NOUVEAU
│   ├── interfaces/             # Protocols (abstractions)
│   │   ├── auth.py             # AuthProvider interface
│   │   ├── storage.py          # StorageProvider interface
│   │   ├── slide_loader.py     # SlideLoader interface
│   │   ├── tile_cache.py       # TileCache interface
│   │   └── workflow.py         # WorkflowHook interface
│   ├── exceptions/             # Exceptions custom
│   └── config/                 # Configuration centralisée
│
├── implementations/            # ← FUTUR (Phase 2+)
│   ├── auth/
│   │   ├── noop_auth.py        # Dev (pas d'auth)
│   │   ├── ldap_auth.py        # CHU UCL
│   │   └── keycloak_auth.py    # SSO moderne
│   ├── storage/
│   │   ├── filesystem_storage.py  # Phase 1 (actuel)
│   │   ├── s3_storage.py          # Cloud
│   │   └── pacs_storage.py        # DICOM
│   └── cache/
│       ├── noop_cache.py       # Phase 1 (pas de cache)
│       └── redis_cache.py      # Phase 2
│
├── routes/                     # API endpoints (existant)
├── services/                   # Business logic (existant)
└── tests/
    ├── conftest.py             # Fixtures (mocks)
    ├── unit/                   # Tests rapides (mocks)
    └── integration/            # Tests lents (vrais services)
```

---

## 3. Les 5 Interfaces Clés

### 3.1 AuthProvider (Authentification)

**Pourquoi?** Chaque hôpital a son système (LDAP, AD, SSO, PACS).

**Interface:**
```python
class AuthProvider(Protocol):
    async def authenticate(self, credentials) -> Optional[User]: ...
    async def authorize(self, user, resource, action) -> bool: ...
    async def validate_token(self, token) -> Optional[User]: ...
```

**Implémentations:**
- `NoOpAuthProvider` - Pas d'auth (dev)
- `LDAPAuthProvider` - LDAP CHU UCL
- `KeycloakAuthProvider` - SSO moderne

### 3.2 StorageProvider (Stockage slides)

**Pourquoi?** Support filesystem, S3, PACS.

**Interface:**
```python
class StorageProvider(Protocol):
    async def list_slides(self, path="/") -> List[SlideMetadata]: ...
    async def get_slide_path(self, slide_id) -> Path: ...
    async def store_slide(self, file, metadata) -> str: ...
```

**Implémentations:**
- `FilesystemStorageProvider` - Phase 1 (actuel)
- `S3StorageProvider` - Cloud
- `PacsStorageProvider` - DICOM integration

### 3.3 SlideLoader (Chargement slides)

**Pourquoi?** Support multi-formats, loaders optimisés.

**Interface:**
```python
class SlideLoader(Protocol):
    def can_open(self, file_path) -> bool: ...
    def get_metadata(self, file_path) -> Dict: ...
    def read_region(self, file_path, location, level, size) -> Image: ...
```

**Implémentations:**
- `OpenSlideLoader` - Phase 1 (actuel)
- `VIPSLoader` - Plus rapide pour certains formats
- `GPULoader` - Accélération GPU

### 3.4 TileCache (Cache tuiles)

**Pourquoi?** Performance (éviter extraire même tuile 100x).

**Interface:**
```python
class TileCache(Protocol):
    async def get_tile(self, slide_id, level, col, row) -> Optional[bytes]: ...
    async def set_tile(self, slide_id, level, col, row, data) -> bool: ...
    async def delete_tile(self, slide_id) -> bool: ...
```

**Implémentations:**
- `NoOpCache` - Phase 1 (pas de cache)
- `RedisCache` - In-memory (rapide)
- `HybridCache` - L1 (Redis) + L2 (filesystem)

### 3.5 WorkflowHook (Intégration PACS/RIS/LIS)

**Pourquoi?** Notifier systèmes externes d'événements.

**Interface:**
```python
class WorkflowHook(Protocol):
    async def on_event(self, event: WorkflowEvent) -> bool: ...
    async def query_worklist(self, filters) -> List[Dict]: ...
    async def send_result(self, accession_number, result) -> bool: ...
```

**Implémentations:**
- `NoOpHook` - Phase 1 (pas d'intégration)
- `PACSHook` - DICOM C-FIND/C-MOVE/C-STORE
- `TelemisHook` - Spécifique Telemis PACS (CHU UCL)

---

## 4. Exemple Complet (10 minutes)

### Scénario: Ajouter cache Redis sans casser code existant

**Étape 1: Créer implémentation RedisCache**

```python
# implementations/cache/redis_cache.py

import redis.asyncio as redis
from core.interfaces import TileCache

class RedisCache:
    def __init__(self, host="localhost", port=6379, ttl=3600):
        self.redis = redis.Redis(host=host, port=port)
        self.ttl = ttl

    async def get_tile(self, slide_id, level, col, row, tile_size=256):
        key = f"tile:{slide_id}:{level}:{col}_{row}:{tile_size}"
        return await self.redis.get(key)  # bytes ou None

    async def set_tile(self, slide_id, level, col, row, tile_size, data, ttl=None):
        key = f"tile:{slide_id}:{level}:{col}_{row}:{tile_size}"
        await self.redis.set(key, data, ex=ttl or self.ttl)
        return True

    async def delete_tile(self, slide_id, level=None, col=None, row=None):
        pattern = f"tile:{slide_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        return True

    async def get_stats(self):
        info = await self.redis.info("stats")
        return {
            "hit_rate": float(info.get("keyspace_hits", 0)) / (float(info.get("keyspace_hits", 0)) + float(info.get("keyspace_misses", 1))),
            "cache_size_bytes": await self.redis.dbsize()
        }

    async def clear(self):
        await self.redis.flushdb()
        return True
```

**Étape 2: Configuration (.env)**

```env
# Cache configuration
CACHE_PROVIDER=redis  # ou "noop" pour désactiver
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TTL=3600
```

**Étape 3: Factory (main.py)**

```python
# main.py

from pydantic_settings import BaseSettings
from implementations.cache.noop_cache import NoOpCache
from implementations.cache.redis_cache import RedisCache

class Settings(BaseSettings):
    cache_provider: str = "noop"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl: int = 3600

    class Config:
        env_file = ".env"

settings = Settings()

def create_cache():
    if settings.cache_provider == "noop":
        return NoOpCache()
    elif settings.cache_provider == "redis":
        return RedisCache(
            host=settings.redis_host,
            port=settings.redis_port,
            ttl=settings.redis_ttl
        )
    else:
        raise ValueError(f"Unknown cache provider: {settings.cache_provider}")

cache = create_cache()
```

**Étape 4: Injection dans TileServer**

```python
# services/tile_server.py (refactoré)

from core.interfaces import TileCache

class TileServer:
    def __init__(self, cache: TileCache):
        self.cache = cache
        self._slide_cache = {}  # Cache slides OpenSlide (existant)

    async def get_tile(self, slide_id, level, col, row, tile_size=256):
        # 1. Check cache
        cached = await self.cache.get_tile(slide_id, level, col, row, tile_size)
        if cached:
            return cached  # Cache hit

        # 2. Extract tile (code existant)
        slide_path = get_slide_path_by_id(slide_id)
        slide = self._get_or_open_slide(slide_path)

        # ... extraction tile ...
        tile_bytes = ...

        # 3. Store in cache (fire-and-forget)
        await self.cache.set_tile(slide_id, level, col, row, tile_size, tile_bytes)

        return tile_bytes

# main.py
tile_server = TileServer(cache=cache)  # Injection
```

**Étape 5: Tests**

```python
# tests/unit/test_tile_server.py

import pytest
from services.tile_server import TileServer

@pytest.mark.asyncio
async def test_tile_server_with_cache(mock_tile_cache):
    # Mock cache (in-memory dict, pas besoin Redis réel)
    tile_server = TileServer(cache=mock_tile_cache)

    # Premier appel: cache miss
    tile1 = await tile_server.get_tile("abc123", 0, 0, 0)

    # Deuxième appel: cache hit
    tile2 = await tile_server.get_tile("abc123", 0, 0, 0)

    assert tile1 == tile2  # Même tuile
    assert mock_tile_cache._storage  # Cache a des entrées
```

**Résultat:**
- ✅ Cache Redis activable via `.env`
- ✅ Code existant fonctionne (NoOpCache par défaut)
- ✅ Tests sans Redis réel (mocks)
- ✅ Pas de modifications API

---

## 5. Tests Pytest (5 minutes)

### Structure

```
tests/
├── conftest.py              # Fixtures (mocks auto)
├── unit/                    # Rapides (mocks)
│   ├── test_auth_interface.py
│   ├── test_storage_interface.py
│   └── test_tile_cache.py
└── integration/             # Lents (vrais services)
    ├── test_redis_cache.py        # Nécessite Redis
    └── test_filesystem_storage.py
```

### Markers

```bash
# Tous tests
pytest

# Seulement tests unitaires (rapides)
pytest -m unit

# Seulement tests auth module
pytest -m auth

# Tous SAUF tests nécessitant Redis
pytest -m "not requires_redis"

# Tests storage module SANS Redis
pytest -m "storage and not requires_redis"

# Coverage
pytest --cov=backend --cov-report=html
```

### Fixtures Disponibles

```python
# Définies dans conftest.py (auto-importées)

@pytest.mark.asyncio
async def test_example(
    mock_user,            # User fictif
    mock_auth_provider,   # AuthProvider mock
    mock_storage_provider,  # StorageProvider mock
    mock_slide_loader,    # SlideLoader mock
    mock_tile_cache,      # TileCache mock
    mock_workflow_hook,   # WorkflowHook mock
    temp_slides_dir       # Temp directory
):
    # Fixtures déjà configurées avec comportement par défaut
    user = mock_user
    assert user.username == "test_pathologist"

    slides = await mock_storage_provider.list_slides("/")
    assert len(slides) > 0
```

---

## 6. Commandes Utiles

### Installation

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Dépendances tests
pip install pytest pytest-asyncio pytest-cov

# Dépendances optionnelles (Phase 2)
pip install redis python-ldap python-keycloak boto3
```

### Tests

```bash
# Tests rapides (unit seulement)
pytest -m unit -v

# Tests complets (avec intégration)
pytest -v

# Tests avec coverage
pytest --cov=backend --cov-report=term-missing

# Tests spécifiques
pytest tests/unit/test_auth_interface.py -v
pytest tests/unit/test_storage_interface.py::test_list_slides -v

# Tests parallèles (plus rapide)
pip install pytest-xdist
pytest -n auto
```

### Linting

```bash
# Installer ruff (linter moderne)
pip install ruff

# Check code
ruff check backend/

# Auto-fix
ruff check --fix backend/

# Format code
ruff format backend/
```

---

## 7. Checklist Ajout Nouveau Provider

**Exemple: Ajouter support S3 storage**

- [ ] Créer `implementations/storage/s3_storage.py`
- [ ] Implémenter toutes méthodes `StorageProvider` interface
- [ ] Ajouter config dans `settings.py` (S3_BUCKET, S3_REGION, etc.)
- [ ] Ajouter dans factory `create_storage_provider()`
- [ ] Écrire tests unitaires avec mocks (`tests/unit/test_s3_storage.py`)
- [ ] Écrire tests intégration avec vrai S3 (`tests/integration/test_s3_storage.py`)
- [ ] Documenter dans `docs/architecture/STORAGE_PROVIDERS.md`
- [ ] Ajouter exemple `.env` dans `backend/.env.example`
- [ ] Tester migration filesystem → S3 (script)

---

## 8. Patterns de Code Courants

### 8.1 Dependency Injection (DI)

```python
# ❌ MAUVAIS: Créer dépendances dans le constructeur
class SlideService:
    def __init__(self):
        self.storage = FilesystemStorage("/slides")  # ← Hard-coded

# ✅ BON: Injecter dépendances
class SlideService:
    def __init__(self, storage: StorageProvider):  # ← Interface
        self.storage = storage

# Configuration (main.py)
storage = FilesystemStorage("/slides")
service = SlideService(storage=storage)  # Injection
```

### 8.2 Factory Pattern

```python
# main.py

def create_auth_provider(settings):
    if settings.auth_provider == "noop":
        return NoOpAuthProvider()
    elif settings.auth_provider == "ldap":
        return LDAPAuthProvider(
            server=settings.ldap_server,
            base_dn=settings.ldap_base_dn
        )
    elif settings.auth_provider == "keycloak":
        return KeycloakAuthProvider(...)
    else:
        raise ValueError(f"Unknown auth provider: {settings.auth_provider}")

auth = create_auth_provider(settings)
```

### 8.3 Strategy Pattern

```python
# Sélection à runtime
if phase == 1:
    cache = NoOpCache()
elif phase == 2:
    cache = RedisCache(host="localhost")
else:
    cache = HybridCache(l1=RedisCache(), l2=FilesystemCache())

# Même interface, comportements différents
tile_server = TileServer(cache=cache)
```

---

## 9. Erreurs Courantes

### Erreur 1: Oublier `await` avec async

```python
# ❌ MAUVAIS
tile = cache.get_tile("abc123", 0, 0, 0)  # Retourne coroutine, pas bytes

# ✅ BON
tile = await cache.get_tile("abc123", 0, 0, 0)  # Retourne bytes
```

### Erreur 2: Dépendance à implémentation concrète

```python
# ❌ MAUVAIS
from implementations.storage.filesystem_storage import FilesystemStorage

class TileServer:
    def __init__(self):
        self.storage = FilesystemStorage("/slides")  # Couplage

# ✅ BON
from core.interfaces import StorageProvider

class TileServer:
    def __init__(self, storage: StorageProvider):  # Interface
        self.storage = storage
```

### Erreur 3: Ne pas gérer exceptions

```python
# ❌ MAUVAIS
async def get_tile(self, slide_id, ...):
    path = await self.storage.get_slide_path(slide_id)  # Peut raise
    return self.loader.read_region(path, ...)

# ✅ BON
from core.exceptions import SlideNotFoundError

async def get_tile(self, slide_id, ...):
    try:
        path = await self.storage.get_slide_path(slide_id)
    except SlideNotFoundError as e:
        raise HTTPException(404, f"Slide not found: {slide_id}")

    return self.loader.read_region(path, ...)
```

---

## 10. Ressources

**Documentation:**
- `docs/architecture/MODULAR_ARCHITECTURE.md` - Guide complet
- `backend/core/interfaces/` - Définitions interfaces
- `backend/tests/conftest.py` - Fixtures disponibles

**Code Examples:**
- `backend/tests/unit/test_auth_interface.py` - Tests auth
- `backend/tests/unit/test_storage_interface.py` - Tests storage

**Références Externes:**
- Python Protocols: https://peps.python.org/pep-0544/
- Dependency Injection: https://python-dependency-injector.ets-labs.org/
- pytest: https://docs.pytest.org/

---

## Next Steps

1. **Lire** `docs/architecture/MODULAR_ARCHITECTURE.md` (guide détaillé)
2. **Explorer** `backend/core/interfaces/` (interfaces)
3. **Tester** fixtures: `pytest tests/unit/ -v`
4. **Implémenter** votre premier provider (ex: RedisCache)
5. **Documenter** dans `docs/architecture/`

---

**Questions?** Consulter FAQ dans `MODULAR_ARCHITECTURE.md` ou demander au Lead Architecte.

**Dernière mise à jour:** 2025-02-05
