# VarunaPoC - Digital Pathology Slide Viewer

**Viewer web de lames histologiques pour CHU UCL Namur**

Remplace le client lourd actuel par une solution web moderne, vendor-neutral et sécurisée.

## Stack Technique

- **Backend:** FastAPI + OpenSlide (Python)
- **Frontend:** Vite + Vanilla JavaScript + OpenSeadragon
- **Formats supportés:** .mrxs (3DHistech), .bif, .tif (Roche/Ventana)

## Phase 1 - Hello World ✅

**Objectif:** Preuve de concept minimaliste - Détection et affichage overview.

**Fonctionnalités:**
- Auto-détection des lames dans `/Slides`
- Affichage liste des lames dans sidebar
- Clic sur lame → Overview affiché dans mini-map OpenSeadragon
- Zone principale noire (placeholder future navigation)

**Principe 80/20:**
Code simple, direct, fonctionnel. Pas d'optimisations prématurées.

## Installation et Lancement

### Backend

```bash
cd backend

# Créer environnement virtuel
python -m venv venv

# Activer (Windows)
venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Lancer serveur
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**IMPORTANT:** OpenSlide doit être installé sur le système.
- Windows: https://openslide.org/download/
- Linux: `sudo apt-get install openslide-tools`

**Vérifier:** http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Installer dépendances
npm install

# Lancer dev server
npm run dev
```

**Ouvre automatiquement:** http://localhost:5173

## Test Complet

1. **Backend running:** http://localhost:8000/api/health → `{"status":"healthy"}`
2. **Frontend running:** http://localhost:5173 → UI s'affiche
3. **Cliquer sur une lame:** Overview apparaît dans mini-map (coin bas-droit)
4. **Métadonnées affichées:** Format, dimensions, niveaux pyramidaux

## Structure Projet

```
VarunaPoC/
├── backend/           # FastAPI + OpenSlide
│   ├── main.py        # Entry point
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic (scanner, loader)
│   └── utils/         # Helpers
│
├── frontend/          # Vite + OpenSeadragon
│   ├── src/
│   │   ├── main.js         # Entry point
│   │   ├── components/     # UI components
│   │   └── utils/          # API client
│   └── index.html
│
├── Slides/            # Test slides (gitignored)
│   ├── 3Dhistec/      # .mrxs files + companions
│   └── ROCHE/         # .bif, .tif files
│
├── CLAUDE.md          # Guide complet pour Claude Agent
└── README.md          # Ce fichier
```

## Documentation

- **CLAUDE.md:** Guide exhaustif pour développement (architecture, docs officielles, scope)
- **backend/README.md:** Installation backend, API endpoints, OpenSlide
- **frontend/README.md:** Installation frontend, OpenSeadragon, components
- **Chaque dossier:** README.md avec détails techniques

## Phase 2 - Prochaines Étapes

- [ ] Tiling DZI pour navigation interactive dans zone principale
- [ ] Mapping coordonnées OpenSeadragon ↔ OpenSlide (CRITICAL!)
- [ ] Cache tiles backend (Redis ou filesystem)
- [ ] Performance optimization (60fps, < 100ms tile load)
- [ ] Tests avec toutes les lames (.mrxs, .bif, .tif)

## Phase 1 Validée Si

- ✅ Backend détecte toutes les lames dans `/Slides`
- ✅ OpenSlide ouvre tous formats (.mrxs avec compagnons, .bif, .tif)
- ✅ Overview extrait avec `get_thumbnail()` (simple, efficace)
- ✅ Frontend affiche liste et overview dans mini-map
- ✅ Communication backend ↔ frontend fonctionne
- ✅ Code commenté et documenté

## Commandes Rapides

```bash
# Backend
cd backend && venv\Scripts\activate && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# Test API
curl http://localhost:8000/api/slides
curl http://localhost:8000/api/slides/{id}/info
```

## Support

- Issues: GitHub Issues
- Documentation: CLAUDE.md
- API Docs: http://localhost:8000/docs

---

**STATUS:** Phase 1 Hello World Complete
**VERSION:** 0.1.0
**DATE:** 2025-10-17
