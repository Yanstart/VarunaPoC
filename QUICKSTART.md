# Quick Start Guide - VarunaPoC

> **Pour le déploiement officiel** (dev workstation, prod hôpital), voir
> [`docs/Admin/DEPLOYMENT.md`](docs/Admin/DEPLOYMENT.md). Cette page-ci
> traite uniquement de la mise au point Python/Node locale (Windows MSYS2,
> bootstrap npm) — utile en complément, pas en remplacement.

Guide rapide pour démarrer le projet après avoir suivi les corrections.

## Vous avez installé OpenSlide via MSYS2 ✅

Le chemin `C:\msys64\ucrt64\bin` est maintenant configuré dans `backend/config_openslide.py`.

---

## Étape 1: Tester Backend

```powershell
cd backend
venv\Scripts\activate

# Test OpenSlide
python -c "import config_openslide; import openslide; print('✓ OpenSlide OK')"
```

**Résultat attendu:**
```
✓ OpenSlide DLL directory added: C:\msys64\ucrt64\bin
✓ OpenSlide OK
```

Si vous voyez ce message, OpenSlide fonctionne! ✅

### Lancer Backend

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Vérifier dans le navigateur: http://localhost:8000/docs

---

## Étape 2: Fixer et Lancer Frontend

### Option A: Script Automatique (Recommandé)

```powershell
cd frontend
.\fix-npm.ps1
npm run dev
```

### Option B: Commandes Manuelles

```powershell
cd frontend

# Nettoyer
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Réinstaller
npm cache clean --force
npm install

# Lancer
npm run dev
```

Le navigateur s'ouvrira automatiquement sur http://localhost:5173

---

## Étape 3: Tester l'Application

1. **Backend:** http://localhost:8000/docs
   - Essayer: GET /api/slides
   - Doit retourner liste vide ou lames détectées

2. **Frontend:** http://localhost:5173
   - Sidebar doit s'afficher
   - Si lames dans `/Slides`: liste apparaît
   - Clic sur lame: overview dans mini-map (coin bas-droit)

---

## Structure Complète en Cours d'Exécution

**Terminal 1 - Backend:**
```powershell
PS C:\...\VarunaPoC\backend> venv\Scripts\activate
(venv) PS C:\...\VarunaPoC\backend> uvicorn main:app --reload
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
✓ OpenSlide DLL directory added: C:\msys64\ucrt64\bin
```

**Terminal 2 - Frontend:**
```powershell
PS C:\...\VarunaPoC\frontend> npm run dev
VITE v5.0.11  ready in 234 ms
➜  Local:   http://localhost:5173/
```

---

## Ajouter des Lames de Test

Placer vos fichiers dans:
```
VarunaPoC/Slides/
├── 3Dhistec/
│   └── sample.mrxs + sample/ (dossier compagnon)
└── ROCHE/
    ├── sample.bif
    └── sample.tif
```

Redémarrer backend (ou attendre auto-reload) pour détecter nouvelles lames.

---

## Problèmes Fréquents

### Backend: "Couldn't locate OpenSlide DLL"

**Solution:**
Vérifier que MSYS2 est installé dans `C:\msys64`. Si ailleurs:
```powershell
notepad backend\config_openslide.py
# Modifier ligne 23: OPENSLIDE_PATH = r"C:\votre\chemin\msys64\ucrt64\bin"
```

### Frontend: Erreur rollup module

**Solution:**
```powershell
cd frontend
.\fix-npm.ps1
```

### Port déjà utilisé

**Backend (changer port):**
```powershell
uvicorn main:app --reload --port 8001
```

**Frontend (changer port):**
```powershell
npm run dev -- --port 3000
```

---

## Commandes Utiles

```powershell
# Arrêter serveurs: Ctrl+C dans chaque terminal

# Redémarrer backend
cd backend
venv\Scripts\activate
uvicorn main:app --reload

# Redémarrer frontend
cd frontend
npm run dev

# Voir logs backend détaillés
uvicorn main:app --reload --log-level debug

# Nettoyer tout et recommencer
cd backend
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cd ../frontend
.\fix-npm.ps1
```

---

## Pour aller plus loin

Cette page-ci ne couvre que le **bootstrap Python/Node local** (souvent
demandé sous Windows à cause de MSYS2). Pour la suite :

- **Stack complète en Docker (dev ou prod)** : voir [`docs/Admin/DEPLOYMENT.md`](docs/Admin/DEPLOYMENT.md).
- **Topologie réseau, ports, profils Compose** : voir [`docs/Admin/INFRASTRUCTURE.md`](docs/Admin/INFRASTRUCTURE.md) et [`docs/Admin/PROFILES.md`](docs/Admin/PROFILES.md).
- **Manuel utilisateur clinicien** : voir [`docs/Manuel/`](docs/Manuel/).
- **Architecture du backend (6 Protocols, Strangler Fig, sprints)** : voir [`docs/architecture/MODULAR_ARCHITECTURE.md`](docs/architecture/MODULAR_ARCHITECTURE.md).
