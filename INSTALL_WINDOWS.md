# Installation Windows - Guide Complet

Ce guide détaille l'installation complète sur Windows, incluant les solutions aux problèmes courants.

## Prérequis

- **Python 3.8+** installé
- **Node.js 18+** installé
- **OpenSlide Windows binaries**

---

## Étape 1: Installer OpenSlide (CRITIQUE pour backend)

### Téléchargement

1. Aller sur: 
2. Télécharger **"OpenSlide Windows binaries"** (fichier .zip)
3. Extraire dans `C:\OpenSlide` (ou autre dossier de votre choix)

Vous devriez avoir cette structure:
```
C:\OpenSlide\
├── bin\
│   ├── libopenslide-0.dll
│   ├── libglib-2.0-0.dll
│   └── ... (autres DLLs)
├── include\
└── lib\
```

### Configuration

Ouvrir `backend/config_openslide.py` et modifier:

```python
OPENSLIDE_PATH = r"C:\OpenSlide\bin"  # Votre chemin ici
```

**Alternative:** Ajouter `C:\OpenSlide\bin` au PATH système Windows:
1. Rechercher "Variables d'environnement" dans Windows
2. Modifier la variable PATH
3. Ajouter `C:\OpenSlide\bin`
4. Redémarrer terminal

---

## Étape 2: Backend Installation

```powershell
cd backend

# Créer environnement virtuel
python -m venv venv

# Activer (PowerShell)
venv\Scripts\activate

# OU Activer (cmd)
venv\Scripts\activate.bat

# Installer dépendances
pip install -r requirements.txt
```

### Test OpenSlide

```powershell
python -c "import config_openslide; import openslide; print('OpenSlide OK')"
```

Si erreur "ModuleNotFoundError: Couldn't locate OpenSlide DLL":
- Vérifier que `C:\OpenSlide\bin` existe
- Vérifier `config_openslide.py` a le bon chemin
- Vérifier que `libopenslide-0.dll` est dans le dossier bin

### Lancer Backend

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Vérifier: http://localhost:8000/docs

---

## Étape 3: Frontend Installation

### Problème Courant: Rollup Module Error

Si vous voyez:
```
Error: Cannot find module @rollup/rollup-win32-x64-msvc
```

**Solution:**

```powershell
cd frontend

# Supprimer cache npm
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Réinstaller PROPREMENT
npm install

# OU si problème persiste, forcer reinstall Vite
npm install vite@latest --save-dev --force
```

### Lancer Frontend

```powershell
npm run dev
```

Ouvre automatiquement: http://localhost:5173

---

## Problèmes Courants et Solutions

### Backend: "ModuleNotFoundError: Couldn't locate OpenSlide DLL"

**Cause:** Python ne trouve pas `libopenslide-0.dll`

**Solutions:**
1. Vérifier `backend/config_openslide.py` ligne 18: chemin correct?
2. Vérifier fichier existe: `C:\OpenSlide\bin\libopenslide-0.dll`
3. Alternative: Ajouter au PATH système (voir Étape 1)

### Backend: "ImportError: DLL load failed"

**Cause:** DLLs dépendantes manquantes (glib, etc.)

**Solution:** Télécharger package COMPLET depuis openslide.org (pas juste libopenslide seule)

### Frontend: "Cannot find module @rollup/rollup-win32-x64-msvc"

**Cause:** Bug npm avec optional dependencies

**Solution:**
```powershell
Remove-Item -Recurse -Force node_modules, package-lock.json
npm cache clean --force
npm install
```

### Frontend: Port 5173 déjà utilisé

**Solution:**
```powershell
# Modifier port dans vite.config.js
npm run dev -- --port 3000
```

---

## Vérification Installation Complète

### Backend
```powershell
# Terminal 1
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

Tests:
- http://localhost:8000 → JSON status
- http://localhost:8000/api/health → `{"status":"healthy"}`
- http://localhost:8000/api/slides → Liste lames (peut être vide si /Slides vide)

### Frontend
```powershell
# Terminal 2 (nouveau)
cd frontend
npm run dev
```

Tests:
- http://localhost:5173 → UI s'affiche
- Pas d'erreurs dans console navigateur (F12)
- Si lames dans /Slides: liste s'affiche dans sidebar

---

## Commandes de Maintenance

### Réinstaller Backend
```powershell
cd backend
Remove-Item -Recurse -Force venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Réinstaller Frontend
```powershell
cd frontend
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install
```

### Mettre à jour dépendances
```powershell
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm update
```

---

## Aide Supplémentaire

- OpenSlide docs: https://openslide.org/api/python/#installing
- FastAPI troubleshooting: https://fastapi.tiangolo.com/
- Vite troubleshooting: https://vitejs.dev/guide/troubleshooting.html

Pour issues: GitHub Issues du projet
