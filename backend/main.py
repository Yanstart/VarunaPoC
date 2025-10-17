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
    title="VarunaPoC Backend",
    description="Digital Pathology Slide Viewer API - Phase 1 Hello World",
    version="0.1.0"
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


@app.get("/")
async def root():
    """
    Health check endpoint.

    Returns:
        Service status et lien vers documentation.
    """
    return {
        "service": "VarunaPoC Backend",
        "status": "running",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health():
    """
    API health check.

    Technical Notes:
        - Utilisé par frontend pour vérifier backend disponible
        - Pas de dépendances externes (OpenSlide, filesystem)
    """
    return {"status": "healthy"}
