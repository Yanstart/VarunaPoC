# VarunaPoC - Checklist Validation Sur Site (CHU UCL Namur)

**Objectif:** Valider le déploiement en 2 phases avec un temps limité sur site ("quelques heures")

**Phases:**
- **Phase 1:** Validation locale (localhost) - 30 minutes
- **Phase 2.1:** Validation réseau (accès distant) - 1 heure
- **Monitoring:** Collecte métriques - En continu

---

## =Ë Pré-Requis (À Vérifier AVANT Départ)

### Matériel et Logiciels

- [ ] **Laptop avec:**
  - Docker Desktop installé et fonctionnel
  - Git installé
  - PowerShell ou Bash disponible
  - Chrome ou Firefox installé

- [ ] **Projet VarunaPoC:**
  - Repository cloné dans: `C:\Users\junio\Desktop\CHU-UCL\VarunaPoC`
  - Branche à jour (pull récent)
  - Dossier `Slides/` contient lames de test

- [ ] **Scripts de déploiement:**
  - `Scripts/Deployment/deploy-phase1.sh` (ou .bat pour Windows)
  - `Scripts/Deployment/switch-to-network.sh`
  - `Scripts/Deployment/deploy-phase2.1.sh`

### Configuration Réseau (À Obtenir du CHU)

- [ ] **Informations réseau:**
  - Adresse IP du serveur: `_________________`
  - Nom DNS du serveur: `varun-p-01` (ou autre: `_________________`)
  - Masque sous-réseau: `_________________`
  - Passerelle: `_________________`

- [ ] **Ports requis (firewall):**
  - [ ] Port 80 (HTTP frontend)
  - [ ] Port 8000 (API backend)
  - [ ] Port 9090 (Prometheus metrics)

- [ ] **Accès client de test:**
  - IP du PC client: `_________________`
  - PC client sur même sous-réseau que serveur

---

## ñ Phase 1: Validation Locale (30 minutes)

### 1.1 Préparation Environnement (5 min)

```bash
# Ouvrir PowerShell ou Git Bash
cd C:\Users\junio\Desktop\CHU-UCL\VarunaPoC

# Vérifier que Docker est démarré
docker --version
docker ps

# Vérifier structure du projet
ls -la
ls -la Slides/
```

**Checklist:**
- [ ] Docker répond correctement
- [ ] Dossier `Slides/` contient lames de test (`.mrxs`, `.bif`, `.tif`)
- [ ] Fichiers `.env.phase1` existent dans `backend/` et `frontend/`

### 1.2 Déploiement Phase 1 (10 min)

```bash
# Option 1: Script automatique (recommandé)
./Scripts/Deployment/deploy-phase1.sh

# Option 2: Commandes manuelles
docker-compose -f docker-compose.phase1.yml build
docker-compose -f docker-compose.phase1.yml up -d
```

**Checklist:**
- [ ] Build backend réussit (sans erreurs)
- [ ] Build frontend réussit (sans erreurs)
- [ ] 3 conteneurs démarrent:
  - `varuna-backend-phase1` (port 8000)
  - `varuna-frontend-phase1` (port 80)
  - `varuna-prometheus-phase1` (port 9090)
- [ ] Health checks passent au vert (attendre 30-60 sec)

### 1.3 Tests Fonctionnels Phase 1 (10 min)

#### Test 1: Backend API

```bash
# Test health check
curl http://localhost:8000/api/health
# Attendu: {"status":"healthy"}

# Test liste des slides
curl http://localhost:8000/api/slides/
# Attendu: JSON avec liste de slides détectés

# Test métadonnées d'une slide (remplacer {id})
curl http://localhost:8000/api/slides/{id}/info
# Attendu: JSON avec dimensions, levels, vendor
```

**Checklist:**
- [ ] `/api/health` retourne `{"status":"healthy"}`
- [ ] `/api/slides/` retourne liste de slides (non vide)
- [ ] `/api/slides/{id}/info` retourne métadonnées correctes

#### Test 2: Frontend

```bash
# Ouvrir navigateur
start http://localhost
```

**Checklist:**
- [ ] Page d'accueil s'affiche correctement
- [ ] Liste des slides apparaît (non vide)
- [ ] Cliquer sur une slide ’ Viewer s'ouvre
- [ ] Navigation fluide (pan, zoom)
- [ ] Mini-map affiche position correcte
- [ ] Tuiles se chargent progressivement

#### Test 3: Monitoring Prometheus

```bash
# Ouvrir Prometheus
start http://localhost:9090
```

**Checklist:**
- [ ] Interface Prometheus s'affiche
- [ ] Dans "Status" ’ "Targets": `varuna-backend` est UP
- [ ] Dans "Graph", tester requêtes:
  - `varuna_http_requests_total` (compteur requêtes)
  - `varuna_tile_load_seconds` (histogramme temps chargement)
  - `varuna_slides_opened_total` (compteur slides ouvertes)
- [ ] Métriques affichent des valeurs (après navigation dans viewer)

### 1.4 Collecte Baseline Metrics (5 min)

**Actions:**
1. Ouvrir plusieurs slides différentes (`.mrxs`, `.bif`, `.tif`)
2. Naviguer dans chaque slide (zoom in/out, pan)
3. Mesurer temps de chargement subjectif
4. Noter impressions UX (fluidité, latence)

**Template de notes:**
```
Phase 1 - Localhost (Baseline)
- Slide .mrxs: Chargement initial ____ sec, Navigation [fluide/saccadée]
- Slide .bif:  Chargement initial ____ sec, Navigation [fluide/saccadée]
- Slide .tif:  Chargement initial ____ sec, Navigation [fluide/saccadée]
- Remarques: _________________________________________________
```

**Checklist:**
- [ ] Au moins 3 slides testées
- [ ] Métriques notées manuellement
- [ ] Prometheus collecte données (vérifier graphs)

---

## < Phase 2.1: Validation Réseau (1 heure)

### 2.1 Arrêt Phase 1 et Préparation (5 min)

```bash
# Arrêter Phase 1
docker-compose -f docker-compose.phase1.yml down

# Vérifier arrêt complet
docker ps
# Attendu: aucun conteneur VarunaPoC en cours
```

**Checklist:**
- [ ] Tous les conteneurs Phase 1 arrêtés
- [ ] Ports 80, 8000, 9090 libérés

### 2.2 Configuration Réseau (10 min)

#### Étape 1: Obtenir IP et Nom

```bash
# Sur Windows PowerShell
ipconfig /all
# Noter l'IPv4 Address de l'interface réseau active

# Exemple: 192.168.1.100
```

**Informations à noter:**
```
IP du serveur (hôte): __________________
Nom DNS (si configuré): varun-p-01 (ou _________________)
```

#### Étape 2: Switch Configuration

```bash
# Utiliser script automatique
./Scripts/Deployment/switch-to-network.sh 192.168.1.100 varun-p-01

# OU manuellement éditer:
# - backend/.env.phase2.1 (API_BASE_URL, CORS_ORIGINS)
# - frontend/.env.phase2.1 (VITE_API_URL)
# - docker-compose.phase2.1.yml (build args)
```

**Checklist:**
- [ ] Script s'exécute sans erreur
- [ ] Backups créés (`.backup.YYYYMMDD_HHMMSS`)
- [ ] Fichiers mis à jour avec bonne IP/nom

#### Étape 3: Firewall Configuration

**Windows Defender Firewall:**

```powershell
# Ouvrir PowerShell en Administrateur

# Port 80 (Frontend HTTP)
New-NetFirewallRule -DisplayName "VarunaPoC Frontend" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# Port 8000 (Backend API)
New-NetFirewallRule -DisplayName "VarunaPoC Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Port 9090 (Prometheus)
New-NetFirewallRule -DisplayName "VarunaPoC Prometheus" -Direction Inbound -LocalPort 9090 -Protocol TCP -Action Allow
```

**Checklist:**
- [ ] Règles firewall créées (vérifier dans Windows Defender)
- [ ] Ports 80, 8000, 9090 autorisés pour connexions entrantes

#### Étape 4: DNS/Hosts Configuration (Optionnel)

Si le CHU n'a pas de DNS configuré pour `varun-p-01`:

**Sur le PC client:**

```bash
# Windows: Éditer C:\Windows\System32\drivers\etc\hosts
# (Ouvrir Notepad en Administrateur)

192.168.1.100   varun-p-01
```

**Checklist:**
- [ ] Entrée `hosts` ajoutée (si nécessaire)
- [ ] `ping varun-p-01` fonctionne depuis client

### 2.3 Déploiement Phase 2.1 (10 min)

```bash
# Option 1: Script automatique (recommandé)
./Scripts/Deployment/deploy-phase2.1.sh

# Option 2: Commandes manuelles
docker-compose -f docker-compose.phase2.1.yml build
docker-compose -f docker-compose.phase2.1.yml up -d
```

**Checklist:**
- [ ] Build réussit (sans erreurs)
- [ ] 3 conteneurs démarrent avec suffixe `-phase2.1`
- [ ] Ports exposés sur `0.0.0.0` (toutes interfaces)
- [ ] Health checks passent au vert

### 2.4 Tests Réseau Depuis Serveur (10 min)

**Sur le serveur (localhost):**

```bash
# Test 1: Backend
curl http://localhost:8000/api/health
curl http://192.168.1.100:8000/api/health

# Test 2: Frontend
start http://localhost
start http://192.168.1.100

# Test 3: Prometheus
start http://localhost:9090
start http://192.168.1.100:9090
```

**Checklist:**
- [ ] Backend répond sur `localhost:8000`
- [ ] Backend répond sur `IP:8000`
- [ ] Frontend accessible via `localhost`
- [ ] Frontend accessible via `IP`
- [ ] Prometheus accessible via `IP:9090`

### 2.5 Tests Réseau Depuis PC Client (20 min)

**CRITIQUE: Ces tests valident la réussite de Phase 2.1**

#### Test 1: Connectivité Réseau

```bash
# Depuis PC client (PowerShell)

# Ping serveur
ping varun-p-01
# OU
ping 192.168.1.100

# Test ports ouverts (PowerShell)
Test-NetConnection -ComputerName varun-p-01 -Port 80
Test-NetConnection -ComputerName varun-p-01 -Port 8000
Test-NetConnection -ComputerName varun-p-01 -Port 9090
```

**Checklist:**
- [ ] Ping réussit (< 100ms idéalement)
- [ ] Port 80 accessible
- [ ] Port 8000 accessible
- [ ] Port 9090 accessible

#### Test 2: API Backend

```bash
# Depuis PC client
curl http://varun-p-01:8000/api/health
# Attendu: {"status":"healthy"}

curl http://varun-p-01:8000/api/slides/
# Attendu: JSON liste slides
```

**Checklist:**
- [ ] `/api/health` répond correctement
- [ ] `/api/slides/` retourne données
- [ ] Latence réseau acceptable (< 100ms)

#### Test 3: Frontend Viewer

**Depuis PC client:**

```bash
# Ouvrir navigateur Chrome/Firefox
start http://varun-p-01
```

**Checklist:**
- [ ] Page d'accueil s'affiche
- [ ] Liste des slides chargée
- [ ] CRITIQUE: Vérifier console navigateur (F12):
  - [ ] Aucune erreur CORS
  - [ ] Aucune erreur "Mixed Content"
  - [ ] Requêtes API vers `http://varun-p-01:8000` réussies
- [ ] Cliquer sur slide ’ Viewer s'ouvre
- [ ] Navigation fluide (comparable à Phase 1)
- [ ] Tuiles se chargent correctement

#### Test 4: Prometheus Metrics

```bash
# Depuis PC client
start http://varun-p-01:9090
```

**Checklist:**
- [ ] Interface Prometheus accessible
- [ ] Target `varuna-backend` est UP
- [ ] Métriques disponibles (mêmes que Phase 1)

### 2.6 Comparaison Performances Phase 1 vs Phase 2.1 (10 min)

**Actions:**
1. Ouvrir mêmes slides que Phase 1
2. Naviguer de manière identique
3. Noter temps de chargement subjectif
4. Comparer avec notes Phase 1

**Template de notes:**
```
Phase 2.1 - Réseau (depuis PC client)
- Slide .mrxs: Chargement initial ____ sec, Navigation [fluide/saccadée]
- Slide .bif:  Chargement initial ____ sec, Navigation [fluide/saccadée]
- Slide .tif:  Chargement initial ____ sec, Navigation [fluide/saccadée]
- Latence réseau estimée: ____ ms
- Remarques: _________________________________________________

Comparaison avec Phase 1:
- Différence chargement: [minime / notable / importante]
- Impact navigation: [aucun / léger / important]
- Verdict: [Acceptable pour production / Nécessite optimisation]
```

**Checklist:**
- [ ] Comparaison effectuée pour 3 slides minimum
- [ ] Métriques Prometheus comparées (P50, P95, P99)
- [ ] Conclusion notée (acceptable ou non)

---

## =Ê Monitoring et Métriques (En Continu)

### Métriques Clés à Surveiller

#### 1. Tile Load Time (Métrique CRITIQUE)

**Dans Prometheus:**
```promql
# P50 (médiane)
histogram_quantile(0.5, rate(varuna_tile_load_seconds_bucket[5m]))

# P95 (95e percentile)
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m]))

# P99 (99e percentile)
histogram_quantile(0.99, rate(varuna_tile_load_seconds_bucket[5m]))
```

**Objectifs:**
- **P50:** < 50ms (excellent) / < 100ms (acceptable)
- **P95:** < 150ms (excellent) / < 250ms (acceptable)
- **P99:** < 300ms (excellent) / < 500ms (acceptable)

**Checklist:**
- [ ] P50 mesuré: ____ ms
- [ ] P95 mesuré: ____ ms
- [ ] P99 mesuré: ____ ms
- [ ] Objectifs atteints: [Oui / Partiellement / Non]

#### 2. Time to First Tile (TTFT)

**Dans Prometheus:**
```promql
histogram_quantile(0.5, rate(varuna_time_to_first_tile_seconds_bucket[5m]))
```

**Objectif:** < 1 seconde (excellent) / < 2 secondes (acceptable)

**Checklist:**
- [ ] TTFT mesuré: ____ secondes
- [ ] Objectif atteint: [Oui / Non]

#### 3. HTTP Request Duration

**Dans Prometheus:**
```promql
histogram_quantile(0.95, rate(varuna_http_request_duration_seconds_bucket[5m]))
```

**Objectif:** < 200ms (API endpoints)

**Checklist:**
- [ ] Latence API mesurée: ____ ms
- [ ] Objectif atteint: [Oui / Non]

#### 4. Slides Opened par Format

**Dans Prometheus:**
```promql
sum by (format) (varuna_slides_opened_total)
```

**Checklist:**
- [ ] Formats testés: `.mrxs`, `.bif`, `.tif`
- [ ] Tous les formats fonctionnent: [Oui / Non]
- [ ] Format problématique (si applicable): ________________

---

## =¨ Troubleshooting Rapide

### Problème: Conteneur ne démarre pas

**Symptômes:**
```bash
docker ps
# Aucun conteneur ou conteneur status "Exited"
```

**Solutions:**
1. Vérifier logs:
   ```bash
   docker-compose -f docker-compose.phase2.1.yml logs backend
   docker-compose -f docker-compose.phase2.1.yml logs frontend
   ```
2. Erreur commune: Volume mount invalide
   - Vérifier que `Slides/` existe
   - Vérifier path Windows: `C:/Users/.../Slides` (slashes forward)

### Problème: Backend répond mais frontend ne charge pas

**Symptômes:**
- `curl http://localhost:8000/api/health` fonctionne
- `http://localhost` affiche page blanche

**Solutions:**
1. Vérifier console navigateur (F12) ’ Onglet Console
2. Erreur CORS:
   ```bash
   # Éditer backend/.env.phase2.1
   CORS_ORIGINS=http://localhost,http://varun-p-01,http://192.168.1.100

   # Redémarrer backend
   docker-compose -f docker-compose.phase2.1.yml restart backend
   ```

### Problème: Client distant ne peut pas se connecter

**Symptômes:**
- Depuis serveur: `curl http://localhost:8000` fonctionne
- Depuis client: `curl http://varun-p-01:8000` timeout

**Solutions:**
1. Vérifier firewall Windows:
   ```powershell
   Get-NetFirewallRule -DisplayName "VarunaPoC*"
   ```
2. Vérifier binding `0.0.0.0` dans docker-compose:
   ```yaml
   ports:
     - "0.0.0.0:8000:8000"  # Correct
     # PAS "127.0.0.1:8000:8000"
   ```
3. Tester avec IP directement (pas hostname):
   ```bash
   curl http://192.168.1.100:8000/api/health
   ```

### Problème: Slides ne s'affichent pas

**Symptômes:**
- Liste slides vide
- Erreur "Slide not found"

**Solutions:**
1. Vérifier volume mount:
   ```bash
   docker exec -it varuna-backend-phase2.1 ls -la /slides
   # Doit lister fichiers .mrxs, .bif, .tif
   ```
2. Si vide, corriger path dans docker-compose.phase2.1.yml:
   ```yaml
   volumes:
     - C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides:/slides:ro
   ```

### Problème: Prometheus ne scrape pas backend

**Symptômes:**
- Target "varuna-backend" DOWN dans Prometheus

**Solutions:**
1. Vérifier endpoint `/metrics`:
   ```bash
   curl http://localhost:8000/metrics
   # Doit retourner métriques Prometheus (format texte)
   ```
2. Vérifier configuration `monitoring/prometheus.yml`:
   ```yaml
   - targets: ['backend:8000']  # Nom du service Docker
   ```
3. Redémarrer Prometheus:
   ```bash
   docker-compose -f docker-compose.phase2.1.yml restart prometheus
   ```

---

##  Critères de Succès (Validation Finale)

### Phase 1 (Localhost)

- [x] Backend démarre et répond sur port 8000
- [x] Frontend démarre et accessible sur port 80
- [x] Au moins 3 slides détectées et ouvrables
- [x] Navigation fluide (60fps visuel, < 100ms tiles)
- [x] Prometheus collecte métriques
- [x] Baseline metrics notées

### Phase 2.1 (Réseau)

- [x] Firewall configuré (ports 80, 8000, 9090)
- [x] Services exposés sur `0.0.0.0` (toutes interfaces)
- [x] PC client peut ping serveur
- [x] API accessible depuis client (`curl http://varun-p-01:8000`)
- [x] Frontend accessible depuis client
- [x] Aucune erreur CORS dans console navigateur
- [x] Navigation fluide depuis client (comparable Phase 1)
- [x] Prometheus accessible depuis client
- [x] Métriques comparables Phase 1 vs Phase 2.1

### Monitoring

- [x] Tile Load Time P50 < 100ms (ou justification si > 100ms)
- [x] TTFT < 2 secondes
- [x] Formats `.mrxs`, `.bif`, `.tif` tous fonctionnels
- [x] Métriques Prometheus exportées et consultables

---

## =Ý Rapport de Validation (À Compléter Sur Site)

### Informations Générales

- **Date de validation:** ____________________
- **Durée totale:** ____ heures ____ minutes
- **Opérateur:** ____________________
- **Lieu:** CHU UCL Namur

### Résultats Phase 1

- Déploiement réussi: [Oui / Non]
- Slides testées: ___________________________________________
- Problèmes rencontrés: ___________________________________________
- Temps moyen chargement tile: ____ ms

### Résultats Phase 2.1

- Déploiement réussi: [Oui / Non]
- IP serveur: ____________________
- IP client test: ____________________
- Latence réseau: ____ ms
- Problèmes rencontrés: ___________________________________________
- Temps moyen chargement tile (réseau): ____ ms
- Différence vs Phase 1: ____ ms ([acceptable / problématique])

### Métriques Prometheus

| Métrique | Phase 1 (local) | Phase 2.1 (réseau) | Objectif | Atteint |
|----------|-----------------|---------------------|----------|---------|
| Tile Load P50 | ____ ms | ____ ms | < 100ms | [ ] |
| Tile Load P95 | ____ ms | ____ ms | < 250ms | [ ] |
| Tile Load P99 | ____ ms | ____ ms | < 500ms | [ ] |
| TTFT | ____ s | ____ s | < 2s | [ ] |
| API Latency | ____ ms | ____ ms | < 200ms | [ ] |

### Conclusion

- **Phase 1 validée:** [Oui / Non / Partiellement]
- **Phase 2.1 validée:** [Oui / Non / Partiellement]
- **Prêt pour Phase 2.2 (slides réseau):** [Oui / Non]
- **Recommandations:** ___________________________________________
  ___________________________________________
  ___________________________________________

### Signatures

- **Validateur (vous):** ____________________
- **Responsable CHU (si présent):** ____________________

---

## =Ú Ressources Complémentaires

- **Documentation complète:** `/docs/Deployment/`
- **Troubleshooting réseau:** `/docs/Deployment/NETWORK_TROUBLESHOOTING.md`
- **Guide Docker:** `/docs/Deployment/DOCKER_INTEGRATION_GUIDE.md`
- **Scripts déploiement:** `/Scripts/Deployment/`
- **Logs backend:** `docker-compose logs -f backend`
- **Logs frontend:** `docker-compose logs -f frontend`
- **Logs Prometheus:** `docker-compose logs -f prometheus`

---

**Version:** 1.0
**Dernière mise à jour:** 2025-12-04
**Auteur:** Équipe VarunaPoC
**Contexte:** Déploiement Phase 1 & 2.1 avec monitoring Prometheus
