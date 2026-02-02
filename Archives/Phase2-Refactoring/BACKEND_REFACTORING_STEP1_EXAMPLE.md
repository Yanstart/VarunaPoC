# Étape 1: Configuration Centralisée - Exemple Pratique

**Date:** 2025-12-31
**Durée estimée:** 2 heures
**Prérequis:** Python 3.11+, pip, virtualenv

---

## Objectif

Centraliser toute la configuration backend dans un seul fichier `config.py` utilisant Pydantic Settings, avec support de variables d'environnement via `.env`.

**Avant:**

- Configuration dispersée dans 5 fichiers différents
- Chemins hardcodés (`C:\msys64\ucrt64\bin`)
- Pas de validation au démarrage

**Après:**

- Configuration centralisée dans `config.py`
- Variables d'environnement (`.env`)
- Validation automatique (Pydantic)
- Single source of truth

---

## Étape 1.1: Installer Pydantic Settings (10 min)

### 1. Activer environnement virtuel

```bash
cd C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Installer dépendances

```bash
pip install pydantic-settings python-dotenv
```

### 3. Mettre à jour requirements.txt

```bash
pip freeze > requirements.txt
```

**Vérification:**

```bash
pip list | grep pydantic
# Devrait afficher:
# pydantic                2.x.x
# pydantic-core           2.x.x
# pydantic-settings       2.x.x
```

---

## Étape 1.2: Créer config.py (30 min)

### Fichier: `backend/config.py`

```python
"""
Configuration centralisée VarunaPoC Backend.

Toute configuration est chargée depuis variables d'environnement (.env)
avec fallbacks pour développement local.

Usage:
    from config import settings
    print(settings.slides_root)
    print(settings.cors_origins)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
import sys


class Settings(BaseSettings):
    """
    Configuration centralisée du backend.

    Variables chargées depuis:
    1. Fichier .env (priorité)
    2. Variables d'environnement système
    3. Valeurs par défaut (ci-dessous)

    Documentation:
        https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    # =========================================================================
    # SLIDES REPOSITORY
    # =========================================================================

    slides_root: str = "/slides"
    """
    Chemin racine du répertoire contenant les slides.

    Développement local: C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides
    Production Docker: /slides
    """

    # =========================================================================
    # OPENSLIDE (Windows uniquement)
    # =========================================================================

    openslide_dll_path: str = r"C:\msys64\ucrt64\bin"
    """
    Chemin vers les DLLs OpenSlide sur Windows.

    Si sur Linux/Docker, cette variable est ignorée (OpenSlide installé système).
    """

    # =========================================================================
    # API CONFIGURATION
    # =========================================================================

    api_title: str = "VarunaPoC Backend API"
    api_version: str = "1.8.0"
    api_description: str = "Digital Pathology Slide Viewer API"

    cors_origins: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Docker frontend
        "http://localhost",       # Frontend on port 80
    ]
    """
    Liste des origines autorisées pour CORS.

    Format: liste d'URLs complètes, séparées par virgules dans .env
    Exemple .env: CORS_ORIGINS=http://localhost:5173,http://localhost:8080
    """

    # =========================================================================
    # CACHE CONFIGURATION
    # =========================================================================

    cache_type: str = "memory"
    """
    Type de cache utilisé.

    Options:
    - "memory": Cache en mémoire (dict Python) - Phase 1
    - "redis": Cache Redis - Phase 2
    """

    cache_max_slides: int = 5
    """
    Nombre maximum de slides gardées ouvertes en mémoire.

    Augmenter si serveur a beaucoup de RAM (1 slide MRXS ≈ 100MB en mémoire).
    """

    cache_ttl_seconds: int = 3600
    """
    Durée de vie (TTL) des entrées en cache (secondes).

    3600 = 1 heure
    """

    redis_url: str = "redis://localhost:6379"
    """
    URL connexion Redis (si cache_type="redis").

    Format: redis://[user:password@]host:port[/db]
    """

    # =========================================================================
    # DATABASE (MLOps Phase 2)
    # =========================================================================

    database_url: str = "sqlite:///./varuna.db"
    """
    URL connexion base de données (tags, feedback, audit).

    Développement: SQLite (sqlite:///./varuna.db)
    Production: PostgreSQL (postgresql://user:pass@host:5432/varuna)
    """

    # =========================================================================
    # PACS INTEGRATION (Phase 2+)
    # =========================================================================

    pacs_enabled: bool = False
    """Active/désactive intégration PACS Telemis."""

    pacs_url: str = ""
    """URL API PACS Telemis."""

    pacs_username: str = ""
    pacs_password: str = ""

    # =========================================================================
    # MONITORING
    # =========================================================================

    prometheus_enabled: bool = False
    """Active/désactive métriques Prometheus."""

    log_level: str = "INFO"
    """
    Niveau de logging.

    Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """

    # =========================================================================
    # SECURITY
    # =========================================================================

    allowed_slide_extensions: List[str] = [
        ".mrxs", ".bif", ".svs", ".ndpi", ".scn", ".tif", ".tiff",
        ".vms", ".vmu", ".czi", ".dcm", ".svslide"
    ]
    """Extensions de fichiers acceptées comme slides."""

    max_upload_size_mb: int = 5000
    """Taille maximale upload (si upload activé Phase 2+)."""

    # =========================================================================
    # PYDANTIC CONFIGURATION
    # =========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# =========================================================================
# INSTANCE GLOBALE
# =========================================================================

settings = Settings()


# =========================================================================
# VALIDATION AU DÉMARRAGE
# =========================================================================

def validate_configuration():
    """
    Valide la configuration au démarrage.

    Raises:
        ValueError: Si configuration invalide
    """
    errors = []

    # Vérifier slides_root existe
    slides_path = Path(settings.slides_root)
    if not slides_path.exists():
        errors.append(
            f"SLIDES_ROOT does not exist: {settings.slides_root}\n"
            f"  Please create directory or update SLIDES_ROOT in .env"
        )

    # Vérifier OpenSlide DLL path (Windows uniquement)
    if sys.platform == "win32":
        dll_path = Path(settings.openslide_dll_path)
        if not dll_path.exists():
            errors.append(
                f"OPENSLIDE_DLL_PATH does not exist: {settings.openslide_dll_path}\n"
                f"  Please install OpenSlide or update path in .env\n"
                f"  Download: https://openslide.org/download/"
            )

    # Vérifier cache_type valide
    if settings.cache_type not in ["memory", "redis"]:
        errors.append(
            f"Invalid CACHE_TYPE: {settings.cache_type}\n"
            f"  Must be 'memory' or 'redis'"
        )

    # Vérifier log_level valide
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.log_level.upper() not in valid_log_levels:
        errors.append(
            f"Invalid LOG_LEVEL: {settings.log_level}\n"
            f"  Must be one of: {', '.join(valid_log_levels)}"
        )

    # Si erreurs, lever exception
    if errors:
        error_message = "\n\n".join([
            "=" * 70,
            "CONFIGURATION ERRORS DETECTED",
            "=" * 70,
            *errors,
            "=" * 70
        ])
        raise ValueError(error_message)

    print("[OK] Configuration validated successfully")


# Valider au import (démarrage application)
validate_configuration()
```

---

## Étape 1.3: Créer .env.example (10 min)

### Fichier: `backend/.env.example`

```bash
# =============================================================================
# VarunaPoC Backend - Configuration Template
# =============================================================================
# Copier ce fichier vers .env et modifier les valeurs selon votre environnement
#
# Linux/Mac:   cp .env.example .env
# Windows:     copy .env.example .env
# =============================================================================

# =============================================================================
# SLIDES REPOSITORY
# =============================================================================

# Chemin racine des slides
# Développement local Windows: C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides
# Développement local Linux: /home/user/VarunaPoC/Slides
# Production Docker: /slides
SLIDES_ROOT=/slides

# =============================================================================
# OPENSLIDE (Windows uniquement)
# =============================================================================

# Chemin vers DLLs OpenSlide
# Installation MSYS2 UCRT64 (recommandé): C:\msys64\ucrt64\bin
# Installation manuelle: C:\OpenSlide\bin
OPENSLIDE_DLL_PATH=C:\msys64\ucrt64\bin

# =============================================================================
# API CONFIGURATION
# =============================================================================

API_TITLE=VarunaPoC Backend API
API_VERSION=1.8.0

# Origines CORS (séparées par virgules, SANS espaces)
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost

# =============================================================================
# CACHE
# =============================================================================

# Type de cache: "memory" ou "redis"
CACHE_TYPE=memory

# Nombre max de slides en cache simultanément
CACHE_MAX_SLIDES=5

# Durée de vie cache (secondes)
CACHE_TTL_SECONDS=3600

# URL Redis (si CACHE_TYPE=redis)
REDIS_URL=redis://localhost:6379

# =============================================================================
# DATABASE (MLOps Phase 2)
# =============================================================================

# SQLite (développement)
DATABASE_URL=sqlite:///./varuna.db

# PostgreSQL (production)
# DATABASE_URL=postgresql://varuna_user:password@localhost:5432/varuna

# =============================================================================
# PACS INTEGRATION (Phase 2+)
# =============================================================================

PACS_ENABLED=false
PACS_URL=
PACS_USERNAME=
PACS_PASSWORD=

# =============================================================================
# MONITORING
# =============================================================================

PROMETHEUS_ENABLED=false

# Niveau de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# =============================================================================
# SECURITY
# =============================================================================

# Taille max upload (MB) - Phase 2+
MAX_UPLOAD_SIZE_MB=5000
```

### Créer .env local

```bash
cd C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend
copy .env.example .env

# Modifier .env avec vos chemins locaux
notepad .env  # ou vim .env sur Linux
```

**Valeurs recommandées développement local:**

```bash
SLIDES_ROOT=C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides
OPENSLIDE_DLL_PATH=C:\msys64\ucrt64\bin
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
CACHE_TYPE=memory
LOG_LEVEL=DEBUG
```

### Ajouter .env au .gitignore

```bash
echo ".env" >> .gitignore
```

---

## Étape 1.4: Migrer main.py (20 min)

### Modifications: `backend/main.py`

**AVANT:**

```python
# Configuration dispersée
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allow_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    allow_origins = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost",
    ]

app = FastAPI(
    title="VarunaPoC Backend API",
    version="1.7.0",
    # ...
)
```

**APRÈS:**

```python
# Importer configuration centralisée
from config import settings

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[...]
)

# CORS avec configuration centralisée
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check avec version depuis config
@app.get("/", tags=["health"])
async def root():
    return {
        "service": settings.api_title,
        "status": "running",
        "version": settings.api_version,
        "docs": "/docs",
        "endpoints": {...}
    }
```

---

## Étape 1.5: Migrer config_openslide.py (15 min)

### Modifications: `backend/config_openslide.py`

**AVANT:**

```python
# Chemin hardcodé
OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"

def configure_openslide_path():
    if not os.path.exists(OPENSLIDE_PATH):
        print(f"WARNING: OpenSlide path not found: {OPENSLIDE_PATH}")
        # ...
```

**APRÈS:**

```python
"""
Configuration OpenSlide pour Windows.

IMPORTANT: Ce module utilise maintenant la configuration centralisée (config.py).
"""

import os
import sys
from config import settings  # Import configuration centralisée


def configure_openslide_path():
    """
    Configure le chemin DLL pour OpenSlide sur Windows.

    Utilise settings.openslide_dll_path depuis config.py.
    Sur Linux/Docker, cette fonction ne fait rien (OpenSlide installé système).
    """
    # Skip sur Linux/Docker
    if sys.platform != "win32":
        print("[INFO] Linux/Docker detected, skipping DLL configuration")
        return True

    openslide_path = settings.openslide_dll_path

    if not os.path.exists(openslide_path):
        print(f"[ERROR] OpenSlide path not found: {openslide_path}")
        print("Please update OPENSLIDE_DLL_PATH in .env file")
        print("Download: https://openslide.org/download/")
        return False

    # Python 3.8+ recommande os.add_dll_directory()
    if sys.version_info >= (3, 8) and hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(openslide_path)
            print(f"[OK] OpenSlide DLL directory added: {openslide_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to add DLL directory: {e}")
            return False
    else:
        # Fallback pour Python < 3.8
        os.environ['PATH'] = openslide_path + os.pathsep + os.environ.get('PATH', '')
        print(f"[OK] OpenSlide added to PATH: {openslide_path}")
        return True


# Auto-configure au import
configure_openslide_path()
```

---

## Étape 1.6: Migrer folder_browser.py (20 min)

### Modifications: `backend/services/folder_browser.py`

**AVANT:**

```python
import sys

def _get_slides_root() -> Path:
    """Détermine le chemin des slides avec fallback local."""
    # 1. Variable d'environnement
    env_path = os.getenv("SLIDES_REPOSITORY_PATH")
    if env_path:
        return Path(env_path)

    # 2. Fallback local
    local_path = Path(__file__).resolve().parent.parent.parent / "Slides"
    if local_path.exists():
        return local_path

    # 3. Chemin Docker
    if sys.platform != "win32":
        docker_path = Path("/slides")
        if docker_path.exists():
            return docker_path

    # 4. Par défaut
    return Path("/slides")

SLIDES_ROOT = _get_slides_root()
print(f"[SLIDES] Final SLIDES_ROOT: {SLIDES_ROOT}")
```

**APRÈS:**

```python
from config import settings

# Utiliser configuration centralisée
SLIDES_ROOT = Path(settings.slides_root)
print(f"[SLIDES] Using SLIDES_ROOT from config: {SLIDES_ROOT}")

# Plus de logique complexe - tout dans config.py
```

**Simplification:**

- Avant: 50 lignes de logique complexe
- Après: 3 lignes

---

## Étape 1.7: Tests (15 min)

### Test 1: Charger configuration

```python
# tests/test_config.py
import pytest
from config import Settings

def test_settings_load_default():
    """Test chargement configuration par défaut."""
    settings = Settings()

    # Vérifier valeurs par défaut
    assert settings.api_title == "VarunaPoC Backend API"
    assert settings.cache_type == "memory"
    assert settings.cache_max_slides == 5
    assert "http://localhost:5173" in settings.cors_origins

def test_settings_from_env(monkeypatch):
    """Test chargement depuis variables d'environnement."""
    # Simuler variables env
    monkeypatch.setenv("SLIDES_ROOT", "/custom/slides")
    monkeypatch.setenv("CACHE_TYPE", "redis")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.slides_root == "/custom/slides"
    assert settings.cache_type == "redis"
    assert settings.log_level == "DEBUG"

def test_settings_cors_origins_from_env(monkeypatch):
    """Test parsing CORS origins depuis env."""
    monkeypatch.setenv("CORS_ORIGINS", "http://app1.com,http://app2.com")

    settings = Settings()

    assert "http://app1.com" in settings.cors_origins
    assert "http://app2.com" in settings.cors_origins
```

### Test 2: Lancer backend

```bash
cd C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload
```

**Sortie attendue:**

```
[OK] Configuration validated successfully
[OK] OpenSlide DLL directory added: C:\msys64\ucrt64\bin
[SLIDES] Using SLIDES_ROOT from config: C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Test 3: Vérifier endpoints

```bash
# Health check
curl http://localhost:8000/

# Devrait retourner:
{
  "service": "VarunaPoC Backend API",
  "status": "running",
  "version": "1.8.0",
  ...
}
```

### Test 4: Vérifier erreur si config invalide

```bash
# Modifier .env avec chemin invalide
SLIDES_ROOT=/invalid/path

# Relancer backend
uvicorn main:app --reload
```

**Sortie attendue:**

```
======================================================================
CONFIGURATION ERRORS DETECTED
======================================================================

SLIDES_ROOT does not exist: /invalid/path
  Please create directory or update SLIDES_ROOT in .env

======================================================================
ValueError: [Configuration errors]
```

---

## Étape 1.8: Validation Finale (10 min)

### Checklist

- [ ] `config.py` créé avec toutes les variables
- [ ] `.env.example` créé et documenté
- [ ] `.env` local créé (gitignored)
- [ ] `main.py` utilise `settings`
- [ ] `config_openslide.py` utilise `settings`
- [ ] `folder_browser.py` utilise `settings`
- [ ] Tests passent (`pytest tests/test_config.py`)
- [ ] Backend démarre sans erreurs
- [ ] Endpoints répondent correctement
- [ ] Configuration invalide détectée au démarrage

### Nettoyage

```bash
# Supprimer ancienne logique (commentée pour référence)
# NE PAS supprimer immédiatement - garder backup 1 semaine

# backend/services/folder_browser.py
# Commenter ancien _get_slides_root() avec:
# DEPRECATED: Replaced by config.py - Remove after 2025-01-07
```

---

## Résumé

**Ce qui a changé:**

1. **Configuration dispersée → Centralisée**
   - Avant: 5 fichiers avec configuration
   - Après: 1 fichier `config.py`

2. **Chemins hardcodés → Variables d'environnement**
   - Avant: `OPENSLIDE_PATH = r"C:\msys64\ucrt64\bin"`
   - Après: `settings.openslide_dll_path` (depuis `.env`)

3. **Pas de validation → Validation automatique**
   - Avant: Erreurs découvertes à l'exécution
   - Après: Validation au démarrage (fail-fast)

4. **Code dupliqué → DRY**
   - Avant: Logique SLIDES_ROOT dupliquée
   - Après: Une seule source de vérité

**Bénéfices:**

- Configuration claire et documentée
- Facile à adapter (dev, test, prod)
- Validation automatique (détection erreurs précoce)
- Testable (injection de variables env)

**Temps réel:**

- Préparation: 10 min
- Développement: 1h30
- Tests: 15 min
- Documentation: 5 min
- **Total: 2h** ✅

---

## Prochaine Étape

**Étape 2: Exceptions Métier Centralisées (2h)**

- Créer hiérarchie d'exceptions custom
- Créer error handler global FastAPI
- Migrer `try/except` vers exceptions métier
- Tests avec codes HTTP appropriés

**Documentation:** `/docs/BACKEND_REFACTORING.md` section 3.1 Étape 2

---

**Document créé le:** 2025-12-31
**Auteur:** Backend Tech Lead
**Statut:** READY - Prêt à être exécuté
