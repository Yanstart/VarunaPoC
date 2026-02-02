# Scripts de Déploiement VarunaPoC

Scripts automatisés pour déploiement et configuration de VarunaPoC.

**Version:** 1.0
**Compatibilité:** Linux (natif), Windows (via bash/Git Bash/PowerShell)

---

## 📋 LISTE DES SCRIPTS

### 1. Configuration Réseau

#### `firewall-host.sh` ⭐ NOUVEAU
**Usage:** Configuration firewall sur le serveur (hôte)

```bash
# Configuration
./firewall-host.sh

# Suppression
./firewall-host.sh --remove
```

**Ce que fait ce script:**
- Détecte automatiquement l'OS (Windows/Linux)
- Configure le firewall pour autoriser les ports VarunaPoC
- Supporte UFW (Ubuntu/Debian), iptables (Linux), Windows Defender Firewall

**Ports ouverts:**
- 80 (Frontend HTTP)
- 8000 (Backend API)
- 9090 (Prometheus)
- 3000 (Grafana)

**Exécution:**
- **Linux:** `sudo ./firewall-host.sh`
- **Windows:** Dans Git Bash ou PowerShell en Administrateur: `bash firewall-host.sh`

---

#### `test-connectivity.sh` ⭐ NOUVEAU
**Usage:** Test connectivité client → serveur (Phase 2.1)

```bash
./test-connectivity.sh <SERVER_IP>

# Exemple:
./test-connectivity.sh 192.168.1.100
```

**Ce que fait ce script:**
- Ping serveur
- Test accessibilité ports TCP (80, 8000, 9090, 3000)
- Test endpoints HTTP (health checks)
- Rapport détaillé (succès/échecs)

**Exécution:**
- **Linux:** `./test-connectivity.sh 192.168.1.100`
- **Windows:** Dans Git Bash: `bash test-connectivity.sh 192.168.1.100`

---

#### `switch-to-network.sh`
**Usage:** Transition Phase 1 (localhost) → Phase 2.1 (réseau)

```bash
./switch-to-network.sh <SERVER_IP> [HOSTNAME]

# Exemples:
./switch-to-network.sh 192.168.1.100
./switch-to-network.sh 192.168.1.100 varun-p-01
```

**Ce que fait ce script:**
- Remplace `localhost` par l'IP serveur dans:
  - `backend/.env.phase2.1`
  - `frontend/.env.phase2.1`
  - `docker-compose.phase2.1.yml`
- Crée backups automatiques (`.backup.YYYYMMDD_HHMMSS`)
- Valide format IP

**⚠️ Après exécution:** Rebuild frontend requis (VITE_API_URL baked in)

```bash
docker-compose -f docker-compose.phase2.1.yml build frontend
docker-compose -f docker-compose.phase2.1.yml up -d
```

---

### 2. Déploiement

#### `deploy-phase1.sh` (À créer)
**Usage:** Déploiement automatique Phase 1 (localhost)

```bash
./deploy-phase1.sh
```

**Fonctionnalités prévues:**
- Validation pré-requis (Docker, dossier Slides/)
- Build images Docker
- Démarrage conteneurs
- Health checks automatiques
- Tests de fumée (smoke tests)
- Rollback si échec

---

#### `deploy-phase2.1.sh` (À créer)
**Usage:** Déploiement automatique Phase 2.1 (réseau)

```bash
./deploy-phase2.1.sh
```

**Fonctionnalités prévues:**
- Validation configuration réseau (IP, firewall)
- Vérification .env files mis à jour
- Build images Docker
- Démarrage conteneurs (binding 0.0.0.0)
- Health checks
- Tests connectivité depuis serveur

---

#### `stop-phase1.sh` (À créer)
**Usage:** Arrêt propre Phase 1

```bash
./stop-phase1.sh [--clean] [--volumes]
```

---

## 🖥️ COMPATIBILITÉ WINDOWS/LINUX

### Line Endings

**Tous les scripts utilisent Unix line endings (LF)**, pas Windows (CRLF).

**Vérification:**
```bash
file Scripts/Deployment/*.sh | grep -E "(CRLF|CR)"
# Si vide: OK (tous LF)
```

**Conversion si nécessaire:**
```bash
# Installer dos2unix (Linux):
sudo apt-get install dos2unix

# Convertir:
dos2unix Scripts/Deployment/*.sh

# OU avec sed:
sed -i 's/\r$//' Scripts/Deployment/*.sh
```

### Exécution sur Windows

**Option 1: Git Bash (Recommandé)**
```bash
# Git Bash intègre bash Unix-like
bash firewall-host.sh
bash test-connectivity.sh 192.168.1.100
```

**Option 2: PowerShell**
```powershell
# PowerShell peut exécuter bash si Git installé
bash .\Scripts\Deployment\firewall-host.sh
bash .\Scripts\Deployment\test-connectivity.sh 192.168.1.100
```

**Option 3: WSL (Windows Subsystem for Linux)**
```bash
wsl bash Scripts/Deployment/firewall-host.sh
```

### Exécution sur Linux

**Natif - Aucune adaptation nécessaire:**
```bash
# Rendre exécutable (première fois)
chmod +x Scripts/Deployment/*.sh

# Exécuter
./Scripts/Deployment/firewall-host.sh
./Scripts/Deployment/test-connectivity.sh 192.168.1.100
```

---

## 🔐 PERMISSIONS

### Linux

**Sudo requis pour:**
- `firewall-host.sh` (modification firewall système)

**Pas de sudo pour:**
- `test-connectivity.sh` (tests réseau)
- `switch-to-network.sh` (édition fichiers locaux)

### Windows

**Administrateur requis pour:**
- `firewall-host.sh` (via PowerShell - règles Windows Defender)

**Pas d'admin pour:**
- `test-connectivity.sh`
- `switch-to-network.sh`

---

## 🚀 WORKFLOW DÉPLOIEMENT COMPLET

### Phase 1 (Localhost)

```bash
# 1. Déployer
./Scripts/Deployment/deploy-phase1.sh

# 2. Tester
curl http://localhost:8000/api/health
# Ouvrir http://localhost
# Ouvrir http://localhost:9090 (Prometheus)
# Ouvrir http://localhost:3000 (Grafana - admin/varuna2024)

# 3. Collecter baseline metrics (10-15 min)
```

### Phase 2.1 (Réseau)

```bash
# 1. Obtenir IP serveur
ipconfig  # Windows
# OU
hostname -I  # Linux

# 2. Configurer firewall SERVEUR
sudo ./Scripts/Deployment/firewall-host.sh

# 3. Switch configuration
./Scripts/Deployment/switch-to-network.sh 192.168.1.100

# 4. Arrêter Phase 1
docker-compose -f docker-compose.phase1.yml down

# 5. Déployer Phase 2.1
docker-compose -f docker-compose.phase2.1.yml build
docker-compose -f docker-compose.phase2.1.yml up -d

# 6. Tester depuis CLIENT
bash test-connectivity.sh 192.168.1.100

# 7. Ouvrir navigateur CLIENT
# http://192.168.1.100
# http://192.168.1.100:9090
# http://192.168.1.100:3000
```

---

## 🛠️ DÉPANNAGE

### Script ne s'exécute pas

**Erreur:** `Permission denied`
```bash
# Solution:
chmod +x Scripts/Deployment/firewall-host.sh
```

**Erreur:** `bad interpreter: /usr/bin/env: no such file or directory`
```bash
# Sur Windows Git Bash, vérifier que bash est dans PATH
# OU exécuter: bash firewall-host.sh
```

**Erreur:** `\r: command not found`
```bash
# Line endings Windows (CRLF) au lieu de Unix (LF)
# Solution:
dos2unix Scripts/Deployment/firewall-host.sh
# OU
sed -i 's/\r$//' Scripts/Deployment/firewall-host.sh
```

### Firewall Windows

**Erreur:** `Access is denied` dans PowerShell
```
Solution: Relancer PowerShell en Administrateur
Clic droit PowerShell → "Exécuter en tant qu'administrateur"
```

**Règles non créées:**
```powershell
# Vérifier règles existantes:
Get-NetFirewallRule -DisplayName "VarunaPoC*"

# Supprimer et recréer:
bash firewall-host.sh --remove
bash firewall-host.sh
```

### Firewall Linux

**Erreur:** `sudo: command not found`
```bash
# Sur certaines distros (ex: Alpine), installer sudo:
su -
apk add sudo  # Alpine
apt-get install sudo  # Debian/Ubuntu
```

**UFW non installé:**
```bash
sudo apt-get update
sudo apt-get install ufw
```

### Test Connectivité

**Tous tests échouent depuis client:**
1. Vérifier firewall serveur: `bash firewall-host.sh`
2. Vérifier services serveur: `docker ps`
3. Vérifier IP correcte: `ping 192.168.1.100`
4. Vérifier même réseau local (subnet)

**Ping OK mais ports fermés:**
- Firewall serveur bloque → Réexécuter `firewall-host.sh`
- Services pas démarrés → `docker-compose up -d`
- Ports pas exposés 0.0.0.0 → Vérifier `docker-compose.phase2.1.yml`

---

## 📚 RESSOURCES

### Documentation Projet

- **PROTOCOLE.md** - Procédure déploiement complète
- **BUILD_DIFFERENCES.md** - Différences Phase 1 vs 2.1, Windows vs Linux
- **docs/Deployment/ONSITE_VALIDATION_CHECKLIST.md** - Checklist sur site

### Commandes Utiles

```bash
# Vérifier line endings
file Scripts/Deployment/*.sh

# Rendre exécutables (Linux)
chmod +x Scripts/Deployment/*.sh

# Tester script sans exécuter (syntaxe)
bash -n Scripts/Deployment/firewall-host.sh

# Exécuter avec trace debug
bash -x Scripts/Deployment/firewall-host.sh
```

---

## 🔄 MAINTENANCE

### Ajouter Nouveau Port

**Éditer `firewall-host.sh`:**
```bash
# Ligne 34:
PORTS=(80 8000 9090 3000 NOUVEAU_PORT)
PORT_NAMES=("Frontend" "Backend API" "Prometheus" "Grafana" "Nouveau Service")
```

**Éditer `test-connectivity.sh`:**
```bash
# Ligne 37:
PORTS=(80 8000 9090 3000 NOUVEAU_PORT)
PORT_NAMES=("Frontend" "Backend API" "Prometheus" "Grafana" "Nouveau Service")
PORT_URLS=("/" "/api/health" "/-/healthy" "/api/health" "/nouveau/health")
```

### Vérifier Intégrité Scripts

```bash
# Tous scripts doivent avoir LF line endings
file Scripts/Deployment/*.sh | grep -v "CRLF"

# Tous scripts doivent être exécutables sur Linux
ls -la Scripts/Deployment/*.sh | grep "^-rwx"

# Shebang correct (portable)
head -1 Scripts/Deployment/*.sh | grep "#!/usr/bin/env bash"
```

---

**VERSION:** 1.0
**DERNIÈRE MISE À JOUR:** 2025-12-04
**AUTEUR:** Équipe VarunaPoC
