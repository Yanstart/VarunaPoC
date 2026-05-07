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
  Slides/                  # Donnees de test multi-vendeur (~60 GB, 10 formats)
  Scripts/                 # Deploiement Docker + gestion fork OpenSlide
  Config_Integration_Infra/ # Config plugin Telemis (PACS hospitalier)
  docs/                    # Documentation technique, manuel utilisateur, standards
    Admin/                 # Manuel administrateur (topologie, profils, ops, fiches services)
    architecture/          # MODULAR_ARCHITECTURE.md canonique (Protocols + sprints)
    Manuel/                # Manuel utilisateur (cliniciens)
    Deployment/            # Guides specifiques deploiement (CHU, secrets, breakglass)
  Archives/                # Plans clos + historique + research future-phase
  .github/                 # CI/CD workflows + runner self-hosted (4 replicas)
```

## Fichiers racine
```
README.md             # Presentation projet
QUICKSTART.md         # Demarrage rapide
CONTRIBUTING.md       # Workflow git
docker-compose.yml    # Compose unifie, pilote par profils Docker
.env.dev.example      # Template variables d'environnement (developpement)
.env.prod.example     # Template variables d'environnement (production)
```

## Demarrage rapide
```bash
# Dev workstation (db + redis + keycloak + orthanc + hapi-fhir)
cp .env.dev.example .env
docker compose --profile dev up -d

# Production (full stack + monitoring)
cp .env.prod.example .env
# editer .env, remplacer chaque CHANGE_ME_*
docker compose --profile prod --profile monitoring up -d
```

Pour le manuel administrateur complet (topologie reseau, profils, ops), voir
[`docs/Admin/`](./docs/Admin/).

## Chaque dossier contient un `info.md` avec: But, Pourquoi, Comment, Structure
