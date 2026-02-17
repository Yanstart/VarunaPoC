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

load_dotenv()  # Load .env file (ML config, CORS, etc.)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

# IMPORTANT: Configure OpenSlide DLL path AVANT tout import
# (Nécessaire sur Windows pour trouver libopenslide-0.dll)
import config_openslide
from routes import ml, slides, viewstate

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

# Monitoring optionnel (requires prometheus_client)
try:
    from monitoring import metrics_endpoint, prometheus_middleware

    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    print("[INFO] Monitoring disabled (prometheus_client not installed)")

# Rate limiting optionnel (requires slowapi)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    # Read rate limit config from env (with defaults)
    _default_rate = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    _tile_rate = os.getenv("RATE_LIMIT_TILES", "500/minute")
    _ml_rate = os.getenv("RATE_LIMIT_ML", "30/minute")

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[_default_rate],
        headers_enabled=True,  # Add X-RateLimit-* headers
    )
    RATE_LIMITING_ENABLED = True
    print(
        f"[INFO] Rate limiting enabled "
        f"(default={_default_rate}, tiles={_tile_rate}, ml={_ml_rate})"
    )
except ImportError:
    RATE_LIMITING_ENABLED = False
    limiter = None
    _tile_rate = None
    _ml_rate = None
    print("[INFO] Rate limiting disabled (slowapi not installed)")


@asynccontextmanager
async def lifespan(_app):
    """Startup/shutdown events for DB and other resources."""
    # Startup
    try:
        from core.database import init_db

        await init_db()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.warning(f"Database not available (annotations disabled): {e}")
    yield
    # Shutdown
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

# Rate limiting middleware (optional - requires slowapi)
if RATE_LIMITING_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
# Read from environment variable (Phase 2.1+) or use defaults (Phase 1)
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # Phase 2.1: Read from env (comma-separated list)
    allow_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Phase 1: Default localhost origins
    allow_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Docker frontend
        "http://localhost",  # Frontend on port 80
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Prometheus monitoring middleware (optionnel)
if MONITORING_ENABLED:
    app.middleware("http")(prometheus_middleware)

# Routes
app.include_router(slides.router)
app.include_router(ml.router, prefix="/api")
app.include_router(viewstate.router)
if ANNOTATIONS_ENABLED:
    app.include_router(annotations.router)
    app.include_router(annotations.label_router)

# Phase 3: Auth routes
if auth_routes is not None:
    app.include_router(auth_routes.router)

# Phase 3: FHIR routes
if fhir_routes is not None and FHIR_ENABLED:
    app.include_router(fhir_routes.router)

# Phase 4: Quality routes (requires annotations)
if quality_routes is not None and QUALITY_ENABLED and ANNOTATIONS_ENABLED:
    app.include_router(quality_routes.router)

# Legacy sweep: Processing pipeline (batch tiles, normalization, outliers)
try:
    from routes import processing

    app.include_router(processing.router)
except ImportError:
    print("[INFO] Processing module disabled")

# Legacy sweep: Collaboration (sharing, WebSocket, merge)
try:
    from routes import sharing, ws

    app.include_router(sharing.router)
    app.include_router(ws.router)
except ImportError:
    print("[INFO] Collaboration modules disabled")

# Legacy sweep: Embeddings (UNI, Phikon, Virchow, CTransPath)
try:
    from routes import embeddings

    app.include_router(embeddings.router)
except ImportError:
    print("[INFO] Embeddings module disabled")

# Legacy sweep: DICOM export
try:
    from routes import exports

    app.include_router(exports.router)
except ImportError:
    print("[INFO] DICOM export module disabled")

# Legacy sweep: Plugin manager
try:
    from routes import plugins

    app.include_router(plugins.router)
except ImportError:
    print("[INFO] Plugin manager disabled")


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
        "docs": "/docs",
        "endpoints": {
            "navigation": "/api/slides/browse",
            "list_all": "/api/slides/",
            "slide_info": "/api/slides/{id}/info",
            "slide_overview": "/api/slides/{id}/overview",
        },
    }


@app.get("/api/health", tags=["health"])
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
