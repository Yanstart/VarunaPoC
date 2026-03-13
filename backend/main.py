"""
VarunaPoC Backend - FastAPI Server

Point d'entrée principal du serveur backend.
Sert les APIs pour le viewer web de lames histologiques.

Documentation:
- FastAPI: https://fastapi.tiangolo.com/
- CORS Middleware: https://fastapi.tiangolo.com/tutorial/cors/

Run:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

API Docs:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # Load .env file before Settings reads env vars

from core.logging_config import setup_logging

setup_logging()

from settings import get_settings

settings = get_settings()

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

# IMPORTANT: Configure OpenSlide DLL path AVANT tout import
# (Nécessaire sur Windows pour trouver libopenslide-0.dll)
import config_openslide
from core.feature_flags import feature_registry
from routes import capabilities, ml, slides, viewstate

# Phase 2: Annotations (optional - requires sqlalchemy + asyncpg)
try:
    from routes import annotations

    ANNOTATIONS_ENABLED = True
except ImportError:
    ANNOTATIONS_ENABLED = False
    print("[INFO] Annotations module disabled (install sqlalchemy, asyncpg, geoalchemy2)")

# Phase 3: Auth (optional)
try:
    from auth import AUTH_ENABLED
    from auth import routes as auth_routes

    print(f"[INFO] Auth module loaded (AUTH_ENABLED={AUTH_ENABLED})")
except ImportError:
    AUTH_ENABLED = False
    auth_routes = None
    print("[INFO] Auth module disabled")

# Phase 3: FHIR stub (optional)
try:
    from fhir import FHIR_ENABLED
    from fhir import routes as fhir_routes

    print(f"[INFO] FHIR module loaded (FHIR_ENABLED={FHIR_ENABLED})")
except ImportError:
    FHIR_ENABLED = False
    fhir_routes = None
    print("[INFO] FHIR module disabled")

# Phase 4: Quality metrics (optional - requires annotations)
try:
    from quality import QUALITY_ENABLED
    from quality import routes as quality_routes

    print(f"[INFO] Quality module loaded (QUALITY_ENABLED={QUALITY_ENABLED})")
except ImportError:
    QUALITY_ENABLED = False
    quality_routes = None
    print("[INFO] Quality module disabled")

logger = logging.getLogger(__name__)

from core.log_filters import PIIMaskingFilter

logging.getLogger().addFilter(PIIMaskingFilter())

# Plugin loader (always available — uses only stdlib)
from core.plugin_loader import discover_plugins, load_plugin, unload_plugins

# PLUGINS_DIR: directory scanned for plugin packages at startup
PLUGINS_DIR = os.getenv("PLUGINS_DIR", "./plugins")

# Monitoring optionnel (requires prometheus_client)
try:
    from monitoring import metrics_endpoint, prometheus_middleware

    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    print("[INFO] Monitoring disabled (prometheus_client not installed)")

# OpenTelemetry tracing (optional: OTEL_ENABLED=true)
try:
    from core.tracing import setup_tracing

    _TRACING_DEFERRED = True  # will be called after app is created
except ImportError:
    _TRACING_DEFERRED = False
    print("[INFO] OpenTelemetry disabled")

# Rate limiting optionnel (requires slowapi)
from rate_limiting import (
    RATE_LIMITING_ENABLED,
    annotation_write_rate,
    auth_rate,
    default_rate,
    limiter,
    ml_rate,
    tile_rate,
)

if RATE_LIMITING_ENABLED:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    print(
        f"[INFO] Rate limiting enabled "
        f"(default={default_rate}, tiles={tile_rate}, ml={ml_rate}, "
        f"auth={auth_rate}, annotations={annotation_write_rate})"
    )
else:
    print("[INFO] Rate limiting disabled (slowapi not installed)")


@asynccontextmanager
async def lifespan(_app):  # noqa: PLR0915
    """Startup/shutdown events for DB, plugins, and other resources."""
    # --- Startup validation (issue #282) ---
    from pathlib import Path as FsPath

    slides_path = FsPath(settings.slides_repository_path)
    if not slides_path.exists():
        logger.warning(
            "SLIDES_REPOSITORY_PATH does not exist: %s — browse/tile endpoints will fail",
            slides_path,
        )

    if settings.auth_enabled:
        oidc_url = os.getenv("OIDC_ISSUER_URL", "")
        if not oidc_url:
            _msg = (
                "AUTH_ENABLED=true but OIDC_ISSUER_URL is not set. "
                "Set OIDC_ISSUER_URL or disable auth with AUTH_ENABLED=false."
            )
            raise ValueError(_msg)
        logger.info("Auth enabled: OIDC issuer=%s", oidc_url)
    else:
        logger.warning("AUTH_ENABLED=false — all endpoints accessible without authentication")

    logger.info(
        "Startup config: auth=%s, slides=%s, db=%s",
        settings.auth_enabled,
        settings.slides_repository_path,
        "configured" if "postgresql" in settings.database_url else "sqlite",
    )

    # --- Redis connectivity check (non-fatal) ---
    if settings.redis_url:
        try:
            import redis as _redis_mod

            _r = _redis_mod.from_url(settings.redis_url, socket_connect_timeout=2)
            _r.ping()
            logger.info("Redis reachable at %s", settings.redis_url)
        except Exception as _redis_exc:
            logger.warning(
                "Redis not reachable (%s) — features requiring Redis will use fallbacks", _redis_exc
            )

    # --- Database ---
    try:
        from core.database import init_db

        await init_db()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.warning("Database not available (annotations disabled): %s", e)

    manifests = discover_plugins(PLUGINS_DIR)
    for manifest in manifests:
        plugin_name = manifest.get("name", manifest.get("_name", "unknown"))
        load_plugin(plugin_name, _app, meta=manifest)

    # Feature flag summary — logged once at startup for observability
    all_flags = feature_registry.get_all()
    enabled = [k for k, v in all_flags.items() if v]
    disabled = [k for k, v in all_flags.items() if not v]
    logger.info("Feature flags enabled: %s", ", ".join(enabled) if enabled else "(none)")
    logger.info("Feature flags disabled: %s", ", ".join(disabled) if disabled else "(none)")
    logger.info(
        "Validated services: slides_path=%s, database=%s, redis=%s",
        "ok" if slides_path.exists() else "missing",
        "configured" if "postgresql" in settings.database_url else "sqlite",
        "configured" if settings.redis_url else "not set",
    )

    yield

    # --- Shutdown: ML worker cleanup (issue #281) ---
    try:
        from routes.ml import _ml_worker

        if _ml_worker is not None and _ml_worker.is_alive():
            logger.info("Stopping ML worker process...")
            _ml_worker.stop()
            logger.info("ML worker stopped")
    except Exception as e:
        logger.debug("ML worker cleanup skipped: %s", e)

    unload_plugins()

    try:
        from core.database import close_db

        await close_db()
        logger.info("Database connection pool closed")
    except Exception:  # nosec B110 - Best-effort cleanup during shutdown, failure is acceptable
        pass


app = FastAPI(
    lifespan=lifespan,
    title="VarunaPoC Backend API",
    description="""
## Digital Pathology Slide Viewer API

VarunaPoC est une visionneuse web de lames histologiques haute résolution développée pour le CHU UCL Namur.

### Fonctionnalités Principales

* **Navigation Hiérarchique** - Explorateur de dossiers dans `/Slides`
* **Détection Multi-Format** - Support MRXS, BIF, SVS, NDPI, TIFF et plus
* **Streaming de Tuiles** - Chargement à la demande (pas de fichier complet en mémoire)
* **Vendor-Neutral** - Compatible avec tous les fabricants de scanners

### Endpoints Disponibles

#### 🗂️ Navigation & Détection
* `GET /api/slides/browse` - Navigation dossier par dossier
* `GET /api/slides/` - Liste complète (scan récursif)

#### 🔬 Visualisation
* `GET /api/slides/{id}/info` - Métadonnées d'une lame
* `GET /api/slides/{id}/overview` - Image d'aperçu (JPEG)

### Documentation Complète

Voir `/docs/Manuel/` pour le guide utilisateur complet.
    """,
    version="1.7.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Points de contrôle de santé du service"},
        {"name": "navigation", "description": "Navigation hiérarchique et détection de lames"},
        {"name": "visualization", "description": "Chargement et affichage des lames"},
    ],
)

# OpenTelemetry instrumentation (deferred until app object is created)
if _TRACING_DEFERRED:
    setup_tracing(app)

# Rate limiting middleware (optional - requires slowapi)
if RATE_LIMITING_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers — structured error responses, no stack traces in production
from core.exception_handlers import register_exception_handlers

register_exception_handlers(app)

# CORS configuration
allow_origins = settings.cors_origin_list
if "*" in allow_origins and settings.auth_enabled:
    _cors_wildcard_err = (
        "CORS_ORIGINS contains wildcard '*' but AUTH_ENABLED=true. "
        "This is a security risk. Set explicit origins in CORS_ORIGINS."
    )
    raise ValueError(_cors_wildcard_err)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security headers — X-Content-Type-Options, X-Frame-Options, etc.
from core.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)

# Access log middleware — logs method, path, status, duration for every request
# (health/metrics paths are excluded to reduce noise)
from core.access_log import AccessLogMiddleware

app.add_middleware(AccessLogMiddleware)

# X-Request-ID middleware — added last so it executes first in the chain
# (Starlette/FastAPI middleware stack: last registered = outermost = runs first)
from core.request_context import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)

# Prometheus monitoring middleware (optionnel)
if MONITORING_ENABLED:
    app.middleware("http")(prometheus_middleware)

# ===========================================================================
# API v1 Router — all versioned endpoints under /api/v1/
# ===========================================================================
api_v1 = APIRouter(prefix="/api/v1")

# Core routes
api_v1.include_router(slides.router)
api_v1.include_router(ml.router)
api_v1.include_router(viewstate.router)
api_v1.include_router(capabilities.router)
if ANNOTATIONS_ENABLED:
    api_v1.include_router(annotations.router)
    api_v1.include_router(annotations.label_router)

# Auth routes
if auth_routes is not None:
    api_v1.include_router(auth_routes.router)

# Break-glass emergency access routes (requires auth module)
try:
    from routes import breakglass as breakglass_routes

    api_v1.include_router(breakglass_routes.router)
    print("[INFO] Break-glass routes loaded")
except ImportError:
    print("[INFO] Break-glass routes disabled")

# FHIR routes
if fhir_routes is not None and FHIR_ENABLED:
    api_v1.include_router(fhir_routes.router)

# Quality routes (requires annotations)
if quality_routes is not None and QUALITY_ENABLED and ANNOTATIONS_ENABLED:
    api_v1.include_router(quality_routes.router)

# Processing pipeline (batch tiles, normalization, outliers)
PROCESSING_ENABLED = False
try:
    from routes import processing

    api_v1.include_router(processing.router)
    PROCESSING_ENABLED = True
except ImportError:
    print("[INFO] Processing module disabled")

# Sharing — collaboration links and merge
COLLABORATION_ENABLED = False
try:
    from routes import sharing

    api_v1.include_router(sharing.router)
except ImportError:
    print("[INFO] Sharing module disabled")

# WebSocket (versioned under /api/v1)
try:
    from routes import ws

    api_v1.include_router(ws.router)
    COLLABORATION_ENABLED = True
except ImportError:
    print("[INFO] WebSocket module disabled")

# Embeddings — UNI, Phikon, Virchow, CTransPath
EMBEDDINGS_ENABLED = False
try:
    from routes import embeddings

    api_v1.include_router(embeddings.router)
    EMBEDDINGS_ENABLED = True
except ImportError:
    print("[INFO] Embeddings module disabled")

# DICOM export
DICOM_EXPORT_ENABLED = False
try:
    from routes import exports

    api_v1.include_router(exports.router)
    DICOM_EXPORT_ENABLED = True
except ImportError:
    print("[INFO] DICOM export module disabled")

# Plugin manager
PLUGINS_ENABLED = False
try:
    from routes import plugins

    api_v1.include_router(plugins.router)
    PLUGINS_ENABLED = True
except ImportError:
    print("[INFO] Plugin manager disabled")

# DICOMweb endpoints — WADO-RS, STOW-RS, QIDO-RS, SR, annotations
DICOMWEB_ENABLED = False
try:
    from routes import dicomweb

    api_v1.include_router(dicomweb.router)
    DICOMWEB_ENABLED = True
except ImportError:
    print("[INFO] DICOMweb module disabled")

# Standards: Integration (eHealth BE, HL7v2, APSR)
INTEGRATION_ENABLED = False
try:
    from routes import integration

    api_v1.include_router(integration.router)
    INTEGRATION_ENABLED = True
except ImportError:
    print("[INFO] Integration module disabled")

# Standards: Terminology (SNOMED CT, LOINC)
TERMINOLOGY_ENABLED = False
try:
    from routes import terminology

    api_v1.include_router(terminology.router)
    TERMINOLOGY_ENABLED = True
except ImportError:
    print("[INFO] Terminology module disabled")

# Standards: Audit API (search, GDPR register)
AUDIT_ENABLED = False
try:
    from routes import audit_api

    api_v1.include_router(audit_api.router)
    AUDIT_ENABLED = True
except ImportError:
    print("[INFO] Audit API module disabled")

# GDPR data subject rights (Art. 15-20)
try:
    from routes import gdpr

    api_v1.include_router(gdpr.router)
except ImportError:
    print("[INFO] GDPR module disabled")

# Regional standards — ABDM, SS-MIX2, I18n
REGIONAL_ENABLED = False
try:
    from routes import regional

    api_v1.include_router(regional.router)
    REGIONAL_ENABLED = True
except ImportError:
    print("[INFO] Regional module disabled")

# Mount the versioned API
app.include_router(api_v1)

# ── Feature flag registry ──────────────────────────────────────────────
# Register all feature flags so GET /api/capabilities can report them.
ML_ENABLED = os.getenv("ML_ENABLED", "true").lower() == "true"

feature_registry.register("annotations", ANNOTATIONS_ENABLED)
feature_registry.register("auth", AUTH_ENABLED)
feature_registry.register("fhir", FHIR_ENABLED)
feature_registry.register("quality", QUALITY_ENABLED)
feature_registry.register("monitoring", MONITORING_ENABLED)
feature_registry.register("rate_limiting", RATE_LIMITING_ENABLED)
feature_registry.register("ml", ML_ENABLED)
feature_registry.register("processing", PROCESSING_ENABLED)
feature_registry.register("collaboration", COLLABORATION_ENABLED)
feature_registry.register("embeddings", EMBEDDINGS_ENABLED)
feature_registry.register("dicom_export", DICOM_EXPORT_ENABLED)
feature_registry.register("plugins", PLUGINS_ENABLED)
feature_registry.register("dicomweb", DICOMWEB_ENABLED)
feature_registry.register("integration", INTEGRATION_ENABLED)
feature_registry.register("terminology", TERMINOLOGY_ENABLED)
feature_registry.register("audit", AUDIT_ENABLED)
feature_registry.register("regional", REGIONAL_ENABLED)


@app.get("/", tags=["health"])
async def root():
    """
    Health check endpoint.

    Returns:
        Service status et lien vers documentation.
    """
    return {
        "service": "VarunaPoC Backend",
        "status": "running",
        "version": "1.7.0",
        "api_version": "v1",
        "docs": "/docs",
        "endpoints": {
            "navigation": "/api/v1/slides/browse",
            "list_all": "/api/v1/slides/",
            "slide_info": "/api/v1/slides/{id}/info",
            "slide_overview": "/api/v1/slides/{id}/overview",
        },
    }


@app.get("/api/v1/health", tags=["health"])
async def health():
    """
    API health check.

    Technical Notes:
        - Utilisé par frontend pour vérifier backend disponible
        - Pas de dépendances externes (OpenSlide, filesystem)
    """
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics(request):
    """
    Prometheus metrics endpoint.

    Expose metrics for Prometheus scraping including:
    - HTTP request counts and durations
    - Tile load times (key metric for WSI benchmarking)
    - Time to first tile (TTFT)
    - Slides opened by format/vendor

    Technical Notes:
        - Scraped by Prometheus every 5 seconds
        - Metrics format: Prometheus text exposition format
        - See monitoring.py for metric definitions
    """
    if MONITORING_ENABLED:
        return await metrics_endpoint(request)
    return PlainTextResponse("Monitoring disabled (install prometheus_client)", status_code=503)
