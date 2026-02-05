# Architecture Modulaire VarunaPoC

**Version:** 2.0.0
**Date:** 2025-02-05
**Auteur:** Lead Architecte VarunaPoC
**Statut:** Architecture cible pour intégration progressive

---

## Table des Matières

1. [Vision](#1-vision)
2. [Principes Architecturaux](#2-principes-architecturaux)
3. [Structure des Interfaces](#3-structure-des-interfaces)
4. [Modules et Implémentations](#4-modules-et-implémentations)
5. [Guide d'Implémentation](#5-guide-dimplémentation)
6. [Tests Modulaires](#6-tests-modulaires)
7. [Exemples de Code](#7-exemples-de-code)
8. [Migration Progressive](#8-migration-progressive)
9. [FAQ](#9-faq)

---

## 1. Vision

### 1.1 Le Problème

**Architecture actuelle (Phase 1):**
- **Monolithique**: Viewer, tile server, format detection couplés
- **Rigide**: Difficile d'ajouter de nouvelles fonctionnalités (ML, PACS, cache)
- **Vendor lock-in**: Diffic

ile de changer de storage (filesystem → S3 → PACS)
- **Tests limités**: Pas de mocks, pas de tests unitaires modulaires

**Exemple concret du problème:**
```python
# tile_server.py (actuel) - Couplage fort avec OpenSlide et filesystem
class TileServer:
    def get_tile(self, slide_path: str, level: int, col: int, row: int):
        # PROBLÈME 1: Couplé à OpenSlide (impossible d'ajouter autre loader)
        slide = openslide.OpenSlide(slide_path)

        # PROBLÈME 2: Couplé à filesystem (impossible S3/PACS)
        # slide_path doit être local

        # PROBLÈME 3: Pas de cache (même tuile extraite N fois)
        region = slide.read_region(...)

        # PROBLÈME 4: Impossible d'injecter ML processing
        return region
```

### 1.2 La Solution: Architecture Modulaire avec Interfaces

**Principe clé: Dépendre d'abstractions, pas d'implémentations**

```
┌─────────────────────────────────────────────────────────────┐
│                     VIEWER SERVICE                          │
│  (Logique métier: affichage, navigation, annotations)       │
└─────────────────────────────────────────────────────────────┘
                           ↓ Dépend de
┌─────────────────────────────────────────────────────────────┐
│                      INTERFACES                             │
│  (Abstractions Python Protocols - pas d'implémentation)     │
│                                                             │
│  - AuthProvider       (authentification pluggable)          │
│  - StorageProvider    (filesystem, S3, PACS)                │
│  - SlideLoader        (OpenSlide, Bio-Formats, custom)      │
│  - TileCache          (Redis, filesystem, CDN)              │
│  - WorkflowHook       (PACS, RIS, LIS integration)          │
└─────────────────────────────────────────────────────────────┘
                           ↑ Implémentent
┌───────────────┬──────────────────┬─────────────────┬────────┐
│ IMPLÉMENTATION│  IMPLÉMENTATION  │ IMPLÉMENTATION  │  ...   │
│    Phase 1    │     Phase 2      │    Phase 3      │        │
│               │                  │                 │        │
│ - NoOpAuth    │ - LDAPAuth       │ - KeycloakSSO   │        │
│ - Filesystem  │ - S3Storage      │ - PACSStorage   │        │
│ - OpenSlide   │ - VIPSLoader     │ - GPULoader     │        │
│ - NoOpCache   │ - RedisCache     │ - CDNCache      │        │
│ - NoOpHook    │ - PACSHook       │ - TelemisHook   │        │
└───────────────┴──────────────────┴─────────────────┴────────┘
```

**Avantages:**
1. **Swap sans casser**: Changer `FilesystemStorage` → `S3Storage` sans toucher au viewer
2. **Tests isolés**: Mocker facilement les interfaces (pas besoin OpenSlide réel)
3. **Extensibilité**: Ajouter nouveaux providers sans modifier code existant
4. **Zero vendor lock-in**: Support LDAP CHU UCL, KeyClo ak Université, etc. via interface unique

---

## 2. Principes Architecturaux

### 2.1 SOLID Principles

#### 2.1.1 Single Responsibility Principle (SRP)
**Principe**: Chaque classe/module a UNE responsabilité.

```python
# ❌ MAUVAIS: SlideService fait TOUT
class SlideService:
    def get_slide(self, slide_id):
        # Responsabilité 1: Storage
        path = self._find_in_filesystem(slide_id)

        # Responsabilité 2: Loading
        slide = openslide.OpenSlide(path)

        # Responsabilité 3: Caching
        if not in_cache:
            cache.set(slide)

        # Responsabilité 4: Auth
        if not user.can_access(slide):
            raise Forbidden

        # TOO MANY RESPONSIBILITIES!
```

```python
# ✅ BON: Séparation des responsabilités
class SlideService:
    def __init__(
        self,
        storage: StorageProvider,  # Responsabilité déléguée
        loader: SlideLoader,       # Responsabilité déléguée
        cache: TileCache,          # Responsabilité déléguée
        auth: AuthProvider         # Responsabilité déléguée
    ):
        self.storage = storage
        self.loader = loader
        self.cache = cache
        self.auth = auth

    def get_slide(self, slide_id, user):
        # Orchestration uniquement (responsabilité unique)
        if not await self.auth.authorize(user, f"slide:{slide_id}", "read"):
            raise Forbidden

        path = await self.storage.get_slide_path(slide_id)
        metadata = self.loader.get_metadata(path)
        return metadata
```

#### 2.1.2 Open/Closed Principle (OCP)
**Principe**: Ouvert à l'extension, fermé à la modification.

```python
# ❌ MAUVAIS: Modifier tile_server.py pour ajouter S3
class TileServer:
    def get_tile(self, slide_id, ...):
        if USE_S3:  # ← Modification du code existant
            path = download_from_s3(slide_id)
        else:
            path = get_from_filesystem(slide_id)
        # ...

# ✅ BON: Ajouter S3StorageProvider sans toucher TileServer
class TileServer:
    def __init__(self, storage: StorageProvider):  # ← Injection
        self.storage = storage

    def get_tile(self, slide_id, ...):
        path = await self.storage.get_slide_path(slide_id)  # ← Abstraction
        # Fonctionne avec Filesystem, S3, PACS sans modification
```

#### 2.1.3 Liskov Substitution Principle (LSP)
**Principe**: Les implémentations doivent être interchangeables.

```python
# Toutes les implémentations de StorageProvider DOIVENT être interchangeables
storage: StorageProvider

# Ces 3 lignes doivent fonctionner identiquement, peu importe l'implémentation
storage = FilesystemStorageProvider("/slides")
storage = S3StorageProvider(bucket="wsi-slides")
storage = PacsStorageProvider(server="dicom.chu-ucl.be")

# Le code métier ne change PAS
path = await storage.get_slide_path("abc123")
```

#### 2.1.4 Interface Segregation Principle (ISP)
**Principe**: Interfaces petites et spécifiques (pas monolithiques).

```python
# ❌ MAUVAIS: Interface monolithique
class StorageProvider(Protocol):
    async def list_slides(self, ...): ...
    async def get_slide_path(self, ...): ...
    async def store_slide(self, ...): ...
    async def delete_slide(self, ...): ...
    async def cache_slide(self, ...): ...  # ← Pas toutes implémentations ont cache
    async def invalidate_cache(self, ...): ...  # ← Pas toutes ont cache
    # TOO FAT INTERFACE

# ✅ BON: Interfaces séparées
class StorageProvider(Protocol):
    # Interface de base (minimum requis)
    async def list_slides(self, ...): ...
    async def get_slide_path(self, ...): ...
    async def store_slide(self, ...): ...

class CachedStorageProvider(StorageProvider, Protocol):
    # Extension optionnelle (seulement si cache)
    async def cache_slide(self, ...): ...
    async def invalidate_cache(self, ...): ...
```

#### 2.1.5 Dependency Inversion Principle (DIP)
**Principe**: Dépendre d'abstractions (interfaces), pas de concrétions.

```python
# ❌ MAUVAIS: Dépendance à implémentation concrète
from services.filesystem_storage import FilesystemStorage

class SlideService:
    def __init__(self):
        self.storage = FilesystemStorage("/slides")  # ← Couplage fort

# ✅ BON: Dépendance à abstraction
from core.interfaces import StorageProvider

class SlideService:
    def __init__(self, storage: StorageProvider):  # ← Injection
        self.storage = storage

# Configuration (main.py ou DI container)
if config.storage_type == "filesystem":
    storage = FilesystemStorage("/slides")
elif config.storage_type == "s3":
    storage = S3Storage(bucket="wsi-slides")

service = SlideService(storage=storage)  # Injection de dépendance
```

### 2.2 Design Patterns Utilisés

#### 2.2.1 Strategy Pattern
**Problème**: Choisir algorithme/comportement à runtime.
**Solution**: Interface avec multiples implémentations.

```python
# Interface Strategy
class TileCache(Protocol):
    async def get_tile(self, ...): ...
    async def set_tile(self, ...): ...

# Stratégies concrètes
class RedisCache: ...  # Stratégie 1
class FilesystemCache: ...  # Stratégie 2
class NoOpCache: ...  # Stratégie 3 (pas de cache)

# Sélection à runtime
if phase == 1:
    cache = NoOpCache()
elif phase == 2:
    cache = RedisCache(host="localhost")
else:
    cache = HybridCache(l1=RedisCache(), l2=FilesystemCache())
```

#### 2.2.2 Adapter Pattern
**Problème**: Intégrer système externe avec interface incompatible.
**Solution**: Adapter qui traduit appels.

```python
# Interface VarunaPoC
class StorageProvider(Protocol):
    async def get_slide_path(self, slide_id: str) -> Path: ...

# Système externe (PACS Telemis) avec API incompatible
class TelemisAPI:
    def retrieve_study(self, accession_number: str) -> bytes: ...

# Adapter
class PacsStorageProvider:
    def __init__(self, pacs_api: TelemisAPI):
        self.pacs = pacs_api

    async def get_slide_path(self, slide_id: str) -> Path:
        # Traduction slide_id → accession_number
        accession = self._slide_id_to_accession(slide_id)

        # Appel PACS (API externe)
        dicom_bytes = self.pacs.retrieve_study(accession)

        # Conversion DICOM → fichier local
        path = self._save_to_temp(dicom_bytes)
        return path
```

#### 2.2.3 Observer Pattern (Workflow Hooks)
**Problème**: Notifier systèmes externes d'événements.
**Solution**: Hooks que le système appelle.

```python
# Observer interface
class WorkflowHook(Protocol):
    async def on_event(self, event: WorkflowEvent) -> bool: ...

# Observers concrets
class PACSHook: ...  # Notifie PACS
class RISHook: ...  # Notifie RIS
class AuditLogHook: ...  # Log audit

# Subject (Viewer Service)
class SlideService:
    def __init__(self, hooks: List[WorkflowHook]):
        self.hooks = hooks

    async def open_slide(self, slide_id, user):
        # Logique métier
        slide = ...

        # Notifier tous les observers
        event = WorkflowEvent(type=WorkflowEventType.SLIDE_OPENED, ...)
        for hook in self.hooks:
            await hook.on_event(event)  # Fire-and-forget

        return slide
```

---

## 3. Structure des Interfaces

### 3.1 Arborescence

```
backend/
├── core/                         # ← NOUVEAU: Core abstractions
│   ├── __init__.py
│   ├── interfaces/               # ← Interfaces (Protocols)
│   │   ├── __init__.py
│   │   ├── auth.py               # AuthProvider interface
│   │   ├── storage.py            # StorageProvider interface
│   │   ├── slide_loader.py       # SlideLoader interface
│   │   ├── tile_cache.py         # TileCache interface
│   │   └── workflow.py           # WorkflowHook interface
│   ├── config/                   # ← Configuration centralisée
│   │   ├── __init__.py
│   │   ├── settings.py           # Pydantic settings
│   │   └── feature_flags.py      # Feature flags (A/B testing, etc.)
│   └── exceptions/               # ← Exceptions custom
│       ├── __init__.py
│       ├── base.py               # VarunaError base class
│       ├── storage.py            # Storage exceptions
│       ├── auth.py               # Auth exceptions
│       ├── slide.py              # Slide exceptions
│       └── workflow.py           # Workflow exceptions
│
├── routes/                       # ← EXISTANT: API endpoints
│   └── slides.py
│
├── services/                     # ← EXISTANT: Business logic
│   ├── format_detector.py
│   ├── tile_server.py
│   ├── slide_loader.py
│   └── ...
│
├── implementations/              # ← FUTUR: Implémentations concrètes
│   ├── auth/
│   │   ├── noop_auth.py          # Phase 1 (pas d'auth)
│   │   ├── ldap_auth.py          # Phase 2 (LDAP CHU)
│   │   └── keycloak_auth.py      # Phase 3 (SSO)
│   ├── storage/
│   │   ├── filesystem_storage.py # Phase 1 (actuel)
│   │   ├── s3_storage.py         # Phase 2 (cloud)
│   │   └── pacs_storage.py       # Phase 2 (PACS)
│   ├── loaders/
│   │   ├── openslide_loader.py   # Phase 1 (actuel)
│   │   └── vips_loader.py        # Phase 3 (optimisé)
│   ├── cache/
│   │   ├── noop_cache.py         # Phase 1 (pas de cache)
│   │   ├── redis_cache.py        # Phase 2 (in-memory)
│   │   └── hybrid_cache.py       # Phase 3 (multi-tier)
│   └── workflow/
│       ├── noop_hook.py          # Phase 1 (pas d'intégration)
│       ├── pacs_hook.py          # Phase 2 (PACS intégration)
│       └── telemis_hook.py       # Phase 2 (Telemis spécifique)
│
└── tests/                        # ← AMÉLIORÉ: Tests modulaires
    ├── conftest.py               # Fixtures partagées
    ├── unit/                     # Tests unitaires (mocks)
    │   ├── test_auth_interface.py
    │   ├── test_storage_interface.py
    │   └── ...
    ├── integration/              # Tests intégration (vrais services)
    │   ├── test_filesystem_storage.py
    │   ├── test_redis_cache.py
    │   └── ...
    └── fixtures/                 # Test data
        └── sample_slides/
```

### 3.2 Interfaces Détaillées

Voir fichiers créés dans `backend/core/interfaces/`:
- `auth.py` - AuthProvider (authentification pluggable)
- `storage.py` - StorageProvider (filesystem, S3, PACS)
- `slide_loader.py` - SlideLoader (OpenSlide, Bio-Formats, custom)
- `tile_cache.py` - TileCache (Redis, filesystem, CDN)
- `workflow.py` - WorkflowHook (PACS, RIS, LIS integration)

---

## 4. Modules et Implémentations

### 4.1 Module Auth

#### 4.1.1 Interface
Voir `backend/core/interfaces/auth.py` pour détails complets.

#### 4.1.2 Implémentations

**Phase 1: NoOpAuthProvider** (développement)
```python
class NoOpAuthProvider:
    """Pas d'authentification (tous les users autorisés)."""

    async def authenticate(self, credentials):
        # Retourner user fictif pour dev
        return User(user_id="dev_user", username="developer", roles=["admin"])

    async def authorize(self, user, resource, action):
        # Toujours autorisé
        return True
```

**Phase 2: LDAPAuthProvider** (CHU UCL Namur)
```python
import ldap3

class LDAPAuthProvider:
    """Authentification via LDAP CHU UCL."""

    def __init__(self, server: str, base_dn: str):
        self.server = server
        self.base_dn = base_dn

    async def authenticate(self, credentials):
        username = credentials["username"]
        password = credentials["password"]

        # Connexion LDAP
        conn = ldap3.Connection(
            ldap3.Server(self.server),
            user=f"uid={username},{self.base_dn}",
            password=password
        )

        if not conn.bind():
            return None  # Auth failed

        # Récupérer attributs user
        conn.search(
            search_base=self.base_dn,
            search_filter=f"(uid={username})",
            attributes=["mail", "memberOf"]
        )

        entry = conn.entries[0]

        # Mapper groupes LDAP → roles VarunaPoC
        roles = self._map_ldap_groups_to_roles(entry.memberOf)

        return User(
            user_id=username,
            username=username,
            email=str(entry.mail),
            roles=roles
        )

    def _map_ldap_groups_to_roles(self, ldap_groups):
        # Exemple mapping
        roles = []
        if "cn=pathologists,ou=groups,dc=chu-ucl,dc=be" in ldap_groups:
            roles.append("pathologist")
        if "cn=admins,ou=groups,dc=chu-ucl,dc=be" in ldap_groups:
            roles.append("admin")
        return roles
```

**Phase 3: KeycloakAuthProvider** (SSO moderne)
```python
from keycloak import KeycloakOpenID

class KeycloakAuthProvider:
    """Authentification via Keycloak SSO."""

    def __init__(self, server_url: str, realm: str, client_id: str):
        self.keycloak = KeycloakOpenID(
            server_url=server_url,
            realm_name=realm,
            client_id=client_id
        )

    async def authenticate(self, credentials):
        # OAuth2 password flow (pour API)
        token = self.keycloak.token(
            username=credentials["username"],
            password=credentials["password"]
        )

        # Décoder token JWT
        user_info = self.keycloak.userinfo(token["access_token"])

        return User(
            user_id=user_info["sub"],
            username=user_info["preferred_username"],
            email=user_info["email"],
            roles=user_info.get("roles", [])
        )

    async def validate_token(self, token: str):
        # Valider JWT token
        user_info = self.keycloak.userinfo(token)
        return User(
            user_id=user_info["sub"],
            username=user_info["preferred_username"],
            email=user_info["email"],
            roles=user_info.get("roles", [])
        )
```

#### 4.1.3 Configuration

```python
# backend/core/config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Auth configuration
    auth_provider: str = "noop"  # "noop", "ldap", "keycloak"

    # LDAP settings
    ldap_server: str = "ldap://ldap.chu-ucl.be"
    ldap_base_dn: str = "dc=chu-ucl,dc=be"

    # Keycloak settings
    keycloak_server: str = "https://keycloak.chu-ucl.be"
    keycloak_realm: str = "varuna"
    keycloak_client_id: str = "varuna-backend"

    class Config:
        env_file = ".env"

# backend/main.py

from core.config import Settings
from implementations.auth.noop_auth import NoOpAuthProvider
from implementations.auth.ldap_auth import LDAPAuthProvider
from implementations.auth.keycloak_auth import KeycloakAuthProvider

settings = Settings()

# Factory pattern pour créer le bon auth provider
def create_auth_provider():
    if settings.auth_provider == "noop":
        return NoOpAuthProvider()
    elif settings.auth_provider == "ldap":
        return LDAPAuthProvider(
            server=settings.ldap_server,
            base_dn=settings.ldap_base_dn
        )
    elif settings.auth_provider == "keycloak":
        return KeycloakAuthProvider(
            server_url=settings.keycloak_server,
            realm=settings.keycloak_realm,
            client_id=settings.keycloak_client_id
        )
    else:
        raise ValueError(f"Unknown auth provider: {settings.auth_provider}")

auth_provider = create_auth_provider()
```

### 4.2 Module Storage

#### 4.2.1 Implémentations

**Phase 1: FilesystemStorageProvider**
```python
class FilesystemStorageProvider:
    """Storage sur filesystem local (Phase 1 - actuel)."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    async def list_slides(self, path="/", recursive=False, filters=None):
        # Utiliser format_detector existant
        detector = FormatDetector()
        slides = detector.scan_directory(self.root_dir / path.lstrip("/"), recursive)

        # Convertir en SlideMetadata
        return [self._to_metadata(s) for s in slides]

    async def get_slide_path(self, slide_id):
        # Utiliser slide_scanner existant
        from services.slide_scanner import get_slide_path_by_id
        return get_slide_path_by_id(slide_id)
```

**Phase 2: S3StorageProvider**
```python
import boto3
from pathlib import Path

class S3StorageProvider:
    """Storage sur S3/MinIO (Phase 2)."""

    def __init__(self, bucket: str, prefix: str = "slides/"):
        self.s3 = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix
        self.cache_dir = Path("/tmp/varuna_cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def list_slides(self, path="/", recursive=False, filters=None):
        # Liste objets S3 avec prefix
        prefix = f"{self.prefix}{path.lstrip('/')}"

        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            Delimiter="/" if not recursive else ""
        )

        slides = []
        for obj in response.get("Contents", []):
            # Filtrer fichiers slides (*.mrxs, *.bif, etc.)
            if self._is_slide_file(obj["Key"]):
                metadata = await self._get_metadata_from_s3(obj["Key"])
                slides.append(metadata)

        return slides

    async def get_slide_path(self, slide_id):
        # Vérifier cache local
        cached_path = self.cache_dir / slide_id
        if cached_path.exists():
            return cached_path

        # Télécharger depuis S3
        s3_key = self._slide_id_to_s3_key(slide_id)

        self.s3.download_file(
            Bucket=self.bucket,
            Key=s3_key,
            Filename=str(cached_path)
        )

        # Télécharger fichiers compagnons si nécessaire (.mrxs → folder)
        if cached_path.suffix == ".mrxs":
            await self._download_companion_folder(s3_key, cached_path)

        return cached_path

    async def store_slide(self, file, metadata, tags=None):
        # Upload vers S3
        slide_id = hashlib.md5(metadata["name"].encode()).hexdigest()[:12]
        s3_key = f"{self.prefix}{slide_id}/{metadata['name']}"

        self.s3.upload_fileobj(
            Fileobj=file,
            Bucket=self.bucket,
            Key=s3_key,
            ExtraArgs={
                "Metadata": {
                    "slide_id": slide_id,
                    "tags": ",".join(tags or [])
                }
            }
        )

        return slide_id
```

**Phase 2: PacsStorageProvider**
```python
from pydicom import dcmread
from pynetdicom import AE, evt
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind

class PacsStorageProvider:
    """Storage via PACS DICOM (Phase 2)."""

    def __init__(self, ae_title: str, pacs_server: str, pacs_port: int):
        self.ae = AE(ae_title=ae_title)
        self.pacs_server = pacs_server
        self.pacs_port = pacs_port
        self.cache_dir = Path("/tmp/pacs_cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def list_slides(self, path="/", recursive=False, filters=None):
        # DICOM C-FIND query
        from pydicom.dataset import Dataset

        ds = Dataset()
        ds.QueryRetrieveLevel = "STUDY"
        ds.PatientID = filters.get("patient_id", "") if filters else ""
        ds.StudyInstanceUID = ""
        ds.Modality = "SM"  # Slide Microscopy

        # Envoyer C-FIND
        assoc = self.ae.associate(self.pacs_server, self.pacs_port)
        if assoc.is_established:
            responses = assoc.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind)

            slides = []
            for status, identifier in responses:
                if status.Status == 0xFF00:  # Pending
                    # Convertir DICOM dataset → SlideMetadata
                    metadata = self._dicom_to_metadata(identifier)
                    slides.append(metadata)

            assoc.release()
            return slides

        raise WorkflowIntegrationError("PACS", "Cannot connect to PACS server")

    async def get_slide_path(self, slide_id):
        # DICOM C-MOVE retrieve
        # 1. Trouver Study/Series UID depuis slide_id
        study_uid, series_uid = self._slide_id_to_uids(slide_id)

        # 2. C-MOVE pour télécharger
        cached_path = self.cache_dir / f"{slide_id}.dcm"

        # TODO: Implémenter C-MOVE handler
        # Pour l'instant, simplification: supposer déjà téléchargé

        return cached_path
```

### 4.3 Module Cache

**Phase 1: NoOpCache**
```python
class NoOpCache:
    """Pas de cache (Phase 1)."""

    async def get_tile(self, slide_id, level, col, row, tile_size=256):
        return None  # Toujours cache miss

    async def set_tile(self, slide_id, level, col, row, tile_size, data, ttl=None):
        return True  # Ignorer silencieusement
```

**Phase 2: RedisCache**
```python
import redis.asyncio as redis

class RedisCache:
    """Cache tuiles dans Redis (Phase 2)."""

    def __init__(self, host="localhost", port=6379, ttl=3600):
        self.redis = redis.Redis(host=host, port=port)
        self.ttl = ttl

    async def get_tile(self, slide_id, level, col, row, tile_size=256):
        key = f"tile:{slide_id}:{level}:{col}_{row}:{tile_size}"
        data = await self.redis.get(key)
        return data  # bytes ou None

    async def set_tile(self, slide_id, level, col, row, tile_size, data, ttl=None):
        key = f"tile:{slide_id}:{level}:{col}_{row}:{tile_size}"
        await self.redis.set(key, data, ex=ttl or self.ttl)
        return True

    async def delete_tile(self, slide_id, level=None, col=None, row=None):
        # Pattern matching pour delete
        pattern = f"tile:{slide_id}:"
        if level is not None:
            pattern += f"{level}:"
        pattern += "*"

        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        return True
```

---

## 5. Guide d'Implémentation

### 5.1 Ajouter un Nouveau AuthProvider

**Cas d'usage**: CHU UCL veut utiliser Keycloak SSO au lieu de LDAP.

**Étapes:**

1. **Créer implémentation** dans `implementations/auth/keycloak_auth.py`:

```python
from core.interfaces import AuthProvider
from core.interfaces.auth import User
from keycloak import KeycloakOpenID

class KeycloakAuthProvider:
    def __init__(self, server_url, realm, client_id, client_secret):
        self.keycloak = KeycloakOpenID(...)

    async def authenticate(self, credentials):
        # Implémenter OAuth2 flow
        ...

    async def authorize(self, user, resource, action):
        # Implémenter RBAC via Keycloak roles
        ...

    # Implémenter autres méthodes...
```

2. **Ajouter configuration** dans `.env`:

```env
AUTH_PROVIDER=keycloak
KEYCLOAK_SERVER=https://keycloak.chu-ucl.be
KEYCLOAK_REALM=varuna
KEYCLOAK_CLIENT_ID=varuna-backend
KEYCLOAK_CLIENT_SECRET=secret123
```

3. **Enregistrer dans factory** (`main.py`):

```python
from implementations.auth.keycloak_auth import KeycloakAuthProvider

def create_auth_provider():
    if settings.auth_provider == "keycloak":
        return KeycloakAuthProvider(
            server_url=settings.keycloak_server,
            realm=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret=settings.keycloak_client_secret
        )
    # ...
```

4. **Tester avec mock**:

```python
# tests/unit/test_keycloak_auth.py

import pytest
from implementations.auth.keycloak_auth import KeycloakAuthProvider
from unittest.mock import Mock, patch

@pytest.mark.auth
@pytest.mark.asyncio
@patch("keycloak.KeycloakOpenID")
async def test_keycloak_authenticate(mock_keycloak):
    mock_keycloak.return_value.token.return_value = {
        "access_token": "fake_token"
    }
    mock_keycloak.return_value.userinfo.return_value = {
        "sub": "user123",
        "preferred_username": "pathologist1",
        "email": "path@chu.be",
        "roles": ["pathologist"]
    }

    provider = KeycloakAuthProvider(
        server_url="https://fake.keycloak",
        realm="test",
        client_id="test_client",
        client_secret="secret"
    )

    user = await provider.authenticate({
        "username": "pathologist1",
        "password": "password123"
    })

    assert user.username == "pathologist1"
    assert "pathologist" in user.roles
```

5. **Tester intégration** (avec vrai Keycloak):

```python
# tests/integration/test_keycloak_integration.py

import pytest

@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.requires_keycloak
@pytest.mark.asyncio
async def test_keycloak_real_auth():
    # Nécessite Keycloak running sur localhost:8080
    provider = KeycloakAuthProvider(
        server_url="http://localhost:8080",
        realm="test",
        client_id="varuna",
        client_secret=os.getenv("KEYCLOAK_SECRET")
    )

    # Tester avec vrai user
    user = await provider.authenticate({
        "username": "test_user",
        "password": "test_password"
    })

    assert user is not None
```

6. **Documenter**:

```markdown
# docs/architecture/AUTH_PROVIDERS.md

## Keycloak SSO

### Installation

```bash
pip install python-keycloak
```

### Configuration

Créer realm "varuna" dans Keycloak avec client "varuna-backend".

### .env

```env
AUTH_PROVIDER=keycloak
KEYCLOAK_SERVER=https://keycloak.chu-ucl.be
KEYCLOAK_REALM=varuna
KEYCLOAK_CLIENT_ID=varuna-backend
KEYCLOAK_CLIENT_SECRET=your_secret_here
```
```

### 5.2 Ajouter un Nouveau StorageProvider

Même processus que AuthProvider. Voir documentation complète dans le code.

---

## 6. Tests Modulaires

### 6.1 Organisation des Tests

```
tests/
├── conftest.py              # Fixtures partagées (mocks)
├── unit/                    # Tests unitaires (mocks uniquement)
│   ├── test_auth_interface.py
│   ├── test_storage_interface.py
│   ├── test_tile_cache_interface.py
│   └── ...
├── integration/             # Tests intégration (vrais services)
│   ├── test_filesystem_storage.py  # Teste FilesystemStorageProvider réel
│   ├── test_redis_cache.py         # Teste RedisCache réel (nécessite Redis)
│   ├── test_ldap_auth.py           # Teste LDAPAuth réel (nécessite LDAP)
│   └── ...
└── e2e/                     # Tests end-to-end (stack complet)
    └── test_viewer_workflow.py
```

### 6.2 Markers Pytest

```python
# Marker module
@pytest.mark.auth          # Tests auth module
@pytest.mark.storage       # Tests storage module
@pytest.mark.slides        # Tests slide loading
@pytest.mark.ml            # Tests ML integration
@pytest.mark.workflow      # Tests workflow hooks
@pytest.mark.cache         # Tests caching

# Marker type
@pytest.mark.unit          # Tests unitaires (rapides)
@pytest.mark.integration   # Tests intégration (lents)
@pytest.mark.e2e           # Tests end-to-end

# Marker environnement
@pytest.mark.requires_openslide  # Nécessite OpenSlide
@pytest.mark.requires_redis      # Nécessite Redis
@pytest.mark.requires_pacs       # Nécessite PACS server
```

### 6.3 Exécution des Tests

```bash
# Tous les tests
pytest

# Seulement tests unitaires (rapides)
pytest -m unit

# Seulement tests auth module
pytest -m auth

# Tous SAUF tests lents
pytest -m "not slow"

# Tests storage SANS tests nécessitant Redis
pytest -m "storage and not requires_redis"

# Coverage report
pytest --cov=backend --cov-report=html

# Tests verbose avec output
pytest -v -s

# Tests parallèles (plus rapide)
pytest -n auto
```

### 6.4 Exemples de Tests

Voir fichiers créés:
- `backend/tests/unit/test_auth_interface.py`
- `backend/tests/unit/test_storage_interface.py`

---

## 7. Exemples de Code

### 7.1 Utiliser AuthProvider dans une Route

```python
# routes/slides.py

from fastapi import APIRouter, Depends, HTTPException
from core.interfaces import AuthProvider
from core.exceptions import AuthorizationError

router = APIRouter()

# Dependency injection FastAPI
async def get_current_user(
    token: str = Header(...),
    auth_provider: AuthProvider = Depends(get_auth_provider)
):
    user = await auth_provider.validate_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

@router.get("/slides/{slide_id}/info")
async def get_slide_info(
    slide_id: str,
    user = Depends(get_current_user),
    auth_provider: AuthProvider = Depends(get_auth_provider),
    storage: StorageProvider = Depends(get_storage_provider)
):
    # Vérifier autorisation
    if not await auth_provider.authorize(user, f"slide:{slide_id}", "read"):
        raise HTTPException(403, "Access denied")

    # Récupérer slide
    metadata = await storage.get_metadata(slide_id)
    return metadata
```

### 7.2 Utiliser StorageProvider + TileCache

```python
# services/tile_server.py (refactoré)

from core.interfaces import StorageProvider, TileCache, SlideLoader

class TileServer:
    def __init__(
        self,
        storage: StorageProvider,
        loader: SlideLoader,
        cache: TileCache
    ):
        self.storage = storage
        self.loader = loader
        self.cache = cache

    async def get_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_size: int = 256
    ) -> bytes:
        # 1. Vérifier cache
        cached = await self.cache.get_tile(slide_id, level, col, row, tile_size)
        if cached:
            return cached  # Cache hit

        # 2. Cache miss: extraire depuis slide
        path = await self.storage.get_slide_path(slide_id)

        # 3. Calculer coordonnées
        metadata = self.loader.get_metadata(path)
        downsample = metadata["level_downsamples"][level]
        x_level0 = int(col * tile_size * downsample)
        y_level0 = int(row * tile_size * downsample)

        # 4. Extraire tuile
        tile_image = self.loader.read_region(
            file_path=path,
            location=(x_level0, y_level0),
            level=level,
            size=(tile_size, tile_size)
        )

        # 5. Convertir en JPEG
        buffer = BytesIO()
        tile_image.convert("RGB").save(buffer, format="JPEG", quality=85)
        tile_bytes = buffer.getvalue()

        # 6. Mettre en cache (fire-and-forget)
        await self.cache.set_tile(slide_id, level, col, row, tile_size, tile_bytes, ttl=3600)

        return tile_bytes
```

### 7.3 Utiliser WorkflowHook

```python
# services/slide_service.py

from core.interfaces import WorkflowHook
from core.interfaces.workflow import WorkflowEvent, WorkflowEventType

class SlideService:
    def __init__(self, hooks: List[WorkflowHook]):
        self.hooks = hooks

    async def open_slide(self, slide_id: str, user):
        # Logique métier
        slide = ...

        # Notifier hooks (PACS, RIS, audit)
        event = WorkflowEvent(
            event_type=WorkflowEventType.SLIDE_OPENED,
            slide_id=slide_id,
            user_id=user.user_id,
            metadata={"timestamp": datetime.now()}
        )

        for hook in self.hooks:
            try:
                await hook.on_event(event)
            except Exception as e:
                # Log erreur mais ne pas bloquer
                logger.error(f"Workflow hook error: {e}")

        return slide
```

---

## 8. Migration Progressive

### 8.1 Phase 1 → Phase 2

**Objectif**: Ajouter cache Redis SANS casser code existant.

**Étape 1: Créer RedisCache implementation**
```python
# implementations/cache/redis_cache.py
class RedisCache: ...  # (voir section 4.3)
```

**Étape 2: Ajouter configuration**
```python
# .env
CACHE_PROVIDER=redis  # ou "noop" pour désactiver
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Étape 3: Refactorer TileServer pour utiliser interface**
```python
# services/tile_server.py

# AVANT (Phase 1)
class TileServer:
    def get_tile(self, slide_path, level, col, row):
        slide = openslide.OpenSlide(slide_path)  # Pas de cache
        region = slide.read_region(...)
        return region

# APRÈS (Phase 2)
from core.interfaces import TileCache

class TileServer:
    def __init__(self, cache: TileCache):  # ← Injection
        self.cache = cache

    async def get_tile(self, slide_id, level, col, row):
        # Vérifier cache d'abord
        cached = await self.cache.get_tile(slide_id, level, col, row)
        if cached:
            return cached

        # Extraire si cache miss
        tile_bytes = ... # Extraction

        # Mettre en cache
        await self.cache.set_tile(slide_id, level, col, row, ..., tile_bytes)

        return tile_bytes
```

**Étape 4: Configurer injection dans main.py**
```python
# main.py

from implementations.cache.noop_cache import NoOpCache
from implementations.cache.redis_cache import RedisCache

def create_cache():
    if settings.cache_provider == "noop":
        return NoOpCache()
    elif settings.cache_provider == "redis":
        return RedisCache(
            host=settings.redis_host,
            port=settings.redis_port
        )

cache = create_cache()
tile_server = TileServer(cache=cache)  # Injection
```

**Résultat:**
- Code existant fonctionne toujours (NoOpCache)
- Redis activable via feature flag
- Tests unitaires utilisent mocks (pas besoin Redis réel)

---

## 9. FAQ

### Q1: Pourquoi Protocols au lieu de classes abstraites (ABC)?

**Réponse:**

Protocols = duck typing avec type checking.

```python
# ABC (héritage obligatoire)
from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    def get_slide_path(self, slide_id): ...

class FilesystemStorage(StorageProvider):  # DOIT hériter
    def get_slide_path(self, slide_id): ...

# Protocol (pas d'héritage requis)
from typing import Protocol

class StorageProvider(Protocol):
    def get_slide_path(self, slide_id): ...

class FilesystemStorage:  # PAS besoin d'hériter
    def get_slide_path(self, slide_id): ...  # Duck typing

# Les deux sont vérifiés par mypy, mais Protocol plus flexible
```

**Avantages Protocols:**
- Pas de couplage héritage
- Mocking plus facile
- Rétro-compatible (code existant devient compatible sans changements)

### Q2: Comment tester sans Redis/LDAP/PACS réel?

**Réponse:** Utiliser les fixtures mock dans `conftest.py`.

```python
# Test SANS Redis
@pytest.mark.unit
async def test_tile_cache(mock_tile_cache):
    # mock_tile_cache est un AsyncMock (in-memory dict)
    await mock_tile_cache.set_tile("abc123", 0, 0, 0, 256, b"data")
    tile = await mock_tile_cache.get_tile("abc123", 0, 0, 0, 256)
    assert tile == b"data"

# Test AVEC Redis
@pytest.mark.integration
@pytest.mark.requires_redis
async def test_redis_cache_real():
    cache = RedisCache(host="localhost", port=6379)
    await cache.set_tile("abc123", 0, 0, 0, 256, b"data")
    tile = await cache.get_tile("abc123", 0, 0, 0, 256)
    assert tile == b"data"
```

### Q3: Comment ajouter support d'un nouveau format de slide?

**Réponse:** Créer nouveau SlideLoader.

```python
# implementations/loaders/bioformats_loader.py

from core.interfaces import SlideLoader
import javabridge  # Bio-Formats Java bridge
import bioformats

class BioFormatsLoader:
    """Loader via Bio-Formats (support 150+ formats)."""

    def can_open(self, file_path):
        # Bio-Formats peut ouvrir presque tout
        return True

    def get_metadata(self, file_path):
        # Utiliser Bio-Formats metadata API
        metadata = bioformats.get_omexml_metadata(str(file_path))
        # Parser OME-XML...
        return {...}

    def read_region(self, file_path, location, level, size):
        # Bio-Formats ImageReader
        reader = bioformats.ImageReader(str(file_path))
        image = reader.read(series=level, rescale=False)
        # Crop region...
        return image

# Configuration
def create_slide_loader():
    if settings.slide_loader == "openslide":
        return OpenSlideLoader()
    elif settings.slide_loader == "bioformats":
        return BioFormatsLoader()
```

### Q4: Est-ce que ça casse le code Phase 1?

**Réponse:** NON. Architecture rétro-compatible.

**Stratégie:**
1. Créer adapters pour code existant
2. Refactorer progressivement (file par file)
3. Tests garantissent non-régression

**Exemple adapter:**
```python
# Adapter pour code existant
class LegacyTileServer:
    """Wrapper pour ancien tile_server.py."""

    def __init__(self, storage: StorageProvider, loader: SlideLoader, cache: TileCache):
        self.storage = storage
        self.loader = loader
        self.cache = cache

    def get_tile(self, slide_path, level, col, row):
        # Convertir ancien code pour utiliser nouvelles interfaces
        slide_id = self._path_to_id(slide_path)
        return asyncio.run(self._get_tile_async(slide_id, level, col, row))

    async def _get_tile_async(self, slide_id, level, col, row):
        # Utiliser nouvelles interfaces
        cached = await self.cache.get_tile(slide_id, level, col, row)
        if cached:
            return cached
        # ...
```

### Q5: Comment déployer en production?

**Réponse:** Docker Compose ou Kubernetes.

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    image: varuna-backend:latest
    environment:
      - AUTH_PROVIDER=ldap
      - STORAGE_PROVIDER=filesystem
      - CACHE_PROVIDER=redis
      - LDAP_SERVER=ldap://ldap.chu-ucl.be
      - REDIS_HOST=redis
    volumes:
      - /mnt/nas/slides:/slides:ro  # Mount NAS
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

  frontend:
    image: varuna-frontend:latest
    ports:
      - "80:80"

volumes:
  redis-data:
```

---

## Conclusion

Cette architecture modulaire permet:

1. **Flexibilité**: Chaque institution choisit ses implémentations (LDAP vs Keycloak, filesystem vs S3)
2. **Testabilité**: Tests unitaires avec mocks, tests intégration avec vrais services
3. **Évolutivité**: Ajouter fonctionnalités (ML, PACS) sans casser l'existant
4. **Maintenabilité**: Code clair, interfaces explicites, séparation des responsabilités

**Prochaines étapes:**
1. Implémenter adapters pour code Phase 1 existant
2. Créer implémentations Phase 2 (RedisCache, LDAPAuth, S3Storage)
3. Tests intégration exhaustifs
4. Documentation complète des providers

---

**Auteur:** Lead Architecte VarunaPoC
**Contact:** [À compléter]
**License:** Propriétaire (CHU UCL Namur)
**Version:** 2.0.0 - 2025-02-05
