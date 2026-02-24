# VarunaPoC - Index de Navigation

## But
Viewer de lames histologiques digitales (WSI) pour le CHU UCL Namur. PoC pour la pathologie digitale: visualisation, annotation, ML, et integration hospitaliere.

## Architecture
```
[Frontend Vanilla JS + OSD] --> [Nginx reverse proxy + cache] --> [Backend FastAPI + OpenSlide]
                                                                         |
                                                         [PostgreSQL/PostGIS + Redis]
```

## Structure du projet
```
VarunaPoC/
  backend/                 # API FastAPI: tuiles, annotations, ML, FHIR, DICOM
  frontend/                # Viewer Vanilla JS + Vite + OpenSeadragon
  nginx/                   # Reverse proxy, cache tuiles 10 GB, TLS
  monitoring/              # Prometheus + Grafana + alertes
  openslide-patch/         # Fork OpenSlide patche (Ventana BIF LEFT)
  Slides/                  # Donnees de test multi-vendeur (~60 GB, 12+ formats)
  Scripts/                 # Deploiement Docker + gestion fork OpenSlide
  Config_Integration_Infra/ # Config plugin Telemis (PACS hospitalier)
  docs/                    # Documentation technique, manuel utilisateur, standards
  Archives/                # Plans futurs (refactoring, MLOps, securite) + historique
  .github/                 # CI/CD workflows + runner self-hosted (4 replicas)
```

## Fichiers racine
```
README.md                      # Presentation projet
QUICKSTART.md                  # Demarrage rapide
docker-compose.dev.yml         # Dev local
docker-compose.production.yml  # Production (nginx + cache + monitoring)
docker-compose.mlops.yml       # Stack MLOps
.env.production.example        # Template variables d'environnement
.env.mlops.example             # Template MLOps
```

## Demarrage rapide
```bash
# Dev
docker compose -f docker-compose.dev.yml up -d --build

# Production
cp .env.production.example .env.production
docker compose -f docker-compose.production.yml up -d --build
```

## Chaque dossier contient un `info.md` avec: But, Pourquoi, Comment, Structure
