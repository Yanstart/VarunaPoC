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

# IMPORTANT: Configure OpenSlide DLL path AVANT tout import
# (Nécessaire sur Windows pour trouver libopenslide-0.dll)
import config_openslide

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import slides
from monitoring import prometheus_middleware, metrics_endpoint

app = FastAPI(
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
        {
            "name": "health",
            "description": "Points de contrôle de santé du service"
        },
        {
            "name": "navigation",
            "description": "Navigation hiérarchique et détection de lames"
        },
        {
            "name": "visualization",
            "description": "Chargement et affichage des lames"
        }
    ]
)

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
        "http://localhost",       # Frontend on port 80
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Prometheus monitoring middleware
app.middleware("http")(prometheus_middleware)

# Routes
app.include_router(slides.router)


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
            "slide_overview": "/api/slides/{id}/overview"
        }
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
    return await metrics_endpoint(request)
