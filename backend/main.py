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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import slides

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

# CORS pour Vite dev server (http://localhost:5173)
# IMPORTANT: Restreindre origins en production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["GET"],  # Read-only pour PoC
    allow_headers=["*"],
)

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
