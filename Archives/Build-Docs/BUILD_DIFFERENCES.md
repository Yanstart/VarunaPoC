# Différences Build: Phase 1 vs Phase 2.1 vs Linux

**Version:** 1.0
**Date:** 2025-12-04

---

## =Ê RÉSUMÉ EXÉCUTIF

### Phase 1 (Localhost)
- Ports: Standard (8000, 80, 9090, 3000)
- CORS: localhost uniquement
- Build: VITE_API_URL=http://localhost:8000

### Phase 2.1 (Réseau Windows)
- Ports: Exposés sur 0.0.0.0 (toutes interfaces)
- CORS: IP serveur + localhost
- Build: VITE_API_URL=http://IP:8000 (baked in bundle JS)

### Linux (Phase 1 & 2.1)
- Chemins: `/home/user/...` au lieu de `C:/Users/...`
- Firewall: `ufw` au lieu de `New-NetFirewallRule`
- Scripts: `.sh` natifs (pas besoin `.bat`)

---

## = PHASE 1 VS PHASE 2.1 (Windows)

### 1. Backend - Différences

#### docker-compose.yml

**Phase 1:**
```yaml
ports:
  - "8000:8000"  # Localhost uniquement par défaut
```

**Phase 2.1:**
```yaml
ports:
  - "0.0.0.0:8000:8000"  # Accessible depuis réseau
```

**Explication:**
- Sans `0.0.0.0:`, Docker bind uniquement sur localhost (127.0.0.1)
- Avec `0.0.0.0:`, accessible depuis n'importe quelle interface réseau (LAN)

#### .env Files

**Phase 1 (`backend/.env.phase1`):**
```bash
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost
CORS_ORIGINS=http://localhost,http://localhost:80
```

**Phase 2.1 (`backend/.env.phase2.1`):**
```bash
API_BASE_URL=http://192.168.1.100:8000
FRONTEND_URL=http://192.168.1.100
CORS_ORIGINS=http://192.168.1.100,http://localhost
SERVER_HOST=0.0.0.0  # CRITIQUE
SERVER_PORT=8000
```

**Différence clé:** `CORS_ORIGINS` doit inclure l'IP du serveur pour que les clients distants puissent faire des requêtes cross-origin.

### 2. Frontend - Différences

#### Build Args (docker-compose.yml)

**Phase 1:**
```yaml
build:
  context: ./frontend
  dockerfile: Dockerfile
  args:
    - VITE_API_URL=http://localhost:8000
```

**Phase 2.1:**
```yaml
build:
  context: ./frontend
  dockerfile: Dockerfile
  args:
    - VITE_API_URL=http://192.168.1.100:8000
```

**  CRITIQUE:** `VITE_API_URL` est un **build-time argument**. Cela signifie:
- La valeur est "baked in" (figée) dans le bundle JavaScript durant le build
- Si vous changez l'IP après le build, vous **DEVEZ rebuild** le frontend
- C'est pourquoi on a deux docker-compose files séparés

#### Rebuild Nécessaire

```bash
# Si vous changez IP dans .env.phase2.1:
docker-compose -f docker-compose.phase2.1.yml build frontend

# Puis redémarrer:
docker-compose -f docker-compose.phase2.1.yml up -d
```

#### .env Files

**Phase 1 (`frontend/.env.phase1`):**
```bash
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=phase1-local
```

**Phase 2.1 (`frontend/.env.phase2.1`):**
```bash
VITE_API_URL=http://192.168.1.100:8000
VITE_ENVIRONMENT=phase2.1-network
```

### 3. Prometheus - Différences

#### Ports

**Phase 1:**
```yaml
ports:
  - "9090:9090"
```

**Phase 2.1:**
```yaml
ports:
  - "0.0.0.0:9090:9090"
```

**Aucune différence de configuration interne** - Prometheus scrape toujours `backend:8000` (nom de service Docker).

### 4. Grafana - Différences

#### Ports

**Phase 1:**
```yaml
ports:
  - "3000:3000"
```

**Phase 2.1:**
```yaml
ports:
  - "0.0.0.0:3000:3000"
```

#### Environment

**Phase 1:**
```yaml
environment:
  - GF_SERVER_ROOT_URL=http://localhost:3000
```

**Phase 2.1:**
```yaml
environment:
  - GF_SERVER_ROOT_URL=http://192.168.1.100:3000
```

**Impact:** URL de base pour redirects et embedded dashboards.

### 5. Réseau Docker - Différences

**Phase 1:**
```yaml
networks:
  varuna-network:
    driver: bridge
    name: varuna-phase1-network
```

**Phase 2.1:**
```yaml
networks:
  varuna-network:
    driver: bridge  # Pas de nom custom pour éviter conflits
```

**Différence:** Réseaux séparés pour éviter collisions entre Phase 1 et Phase 2.1.

---

## =» WINDOWS VS LINUX

### 1. Chemins Volumes

#### Windows (docker-compose)

```yaml
volumes:
  - C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides:/slides:ro
  #  Forward slashes requis
  #  Lettre de disque (C:)
```

#### Linux (docker-compose)

```yaml
volumes:
  - /home/user/VarunaPoC/Slides:/slides:ro
  #  Pas de lettre de disque
  #  Commence par /
```

**Adaptation:**

```yaml
# Solution portable (relative path)
volumes:
  - ./Slides:/slides:ro
  #  Fonctionne Windows ET Linux
  #   Mais moins explicite
```

### 2. Firewall

#### Windows (PowerShell)

```powershell
# Ouvrir ports (Administrateur requis)
New-NetFirewallRule -DisplayName "VarunaPoC Frontend" `
  -Direction Inbound `
  -LocalPort 80 `
  -Protocol TCP `
  -Action Allow

New-NetFirewallRule -DisplayName "VarunaPoC Backend" `
  -LocalPort 8000 `
  -Protocol TCP `
  -Action Allow

New-NetFirewallRule -DisplayName "VarunaPoC Prometheus" `
  -LocalPort 9090 `
  -Protocol TCP `
  -Action Allow

New-NetFirewallRule -DisplayName "VarunaPoC Grafana" `
  -LocalPort 3000 `
  -Protocol TCP `
  -Action Allow
```

#### Linux (UFW - Ubuntu/Debian)

```bash
# Activer UFW (si pas déjà fait)
sudo ufw enable

# Ouvrir ports
sudo ufw allow 80/tcp comment "VarunaPoC Frontend"
sudo ufw allow 8000/tcp comment "VarunaPoC Backend"
sudo ufw allow 9090/tcp comment "VarunaPoC Prometheus"
sudo ufw allow 3000/tcp comment "VarunaPoC Grafana"

# Vérifier
sudo ufw status numbered
```

#### Linux (iptables - Alternative)

```bash
# Ouvrir ports
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 9090 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT

# Sauvegarder règles
sudo iptables-save > /etc/iptables/rules.v4
```

### 3. Obtenir IP

#### Windows

```powershell
ipconfig
# Chercher IPv4 Address dans section active
```

#### Linux

```bash
# Méthode 1: ip (moderne)
ip addr show
# ou plus concis:
ip -4 addr show | grep inet

# Méthode 2: ifconfig (ancien)
ifconfig
# Chercher inet dans interface active (eth0, enp0s3, etc.)

# Méthode 3: hostname
hostname -I
```

### 4. Tester Connectivité

#### Windows

```powershell
# Ping
ping 192.168.1.100

# Test port spécifique
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000
```

#### Linux

```bash
# Ping
ping -c 4 192.168.1.100

# Test port (telnet)
telnet 192.168.1.100 8000

# Test port (nc - netcat)
nc -zv 192.168.1.100 8000

# Test port (curl)
curl -v telnet://192.168.1.100:8000
```

### 5. Docker Installation

#### Windows

- **Docker Desktop** avec GUI
- WSL 2 backend (recommandé)
- Interface graphique pour gestion

#### Linux

- **Docker Engine** (CLI uniquement)
- Installation via apt/yum/dnf selon distro

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Ajouter user au groupe docker (éviter sudo)
sudo usermod -aG docker $USER
# Se déconnecter/reconnecter pour appliquer
```

### 6. Scripts de Déploiement

#### Windows

**Options:**
1. **Git Bash** (`.sh` scripts fonctionnent)
2. **PowerShell** (créer `.ps1` équivalents)
3. **CMD** (créer `.bat` équivalents)

**Actuellement:** Scripts `.sh` fournis (fonctionnent avec Git Bash sur Windows).

#### Linux

**Native:** Scripts `.sh` fonctionnent directement.

```bash
# Rendre exécutable
chmod +x Scripts/Deployment/*.sh

# Exécuter
./Scripts/Deployment/deploy-phase1.sh
```

**Pas de modification nécessaire** pour scripts existants.

### 7. Permissions Fichiers

#### Windows

- Docker Desktop gère automatiquement
- Pas de problèmes `chown`/`chmod` habituels

#### Linux

**Problème potentiel:** Volumes montés peuvent avoir mauvaises permissions.

**Solution:**

```bash
# Vérifier propriétaire dossier Slides
ls -la Slides/

# Si nécessaire, ajuster permissions
sudo chown -R $USER:$USER Slides/

# Ou permissions lecture universelle
chmod -R a+r Slides/
```

**Dans Dockerfile backend:** Déjà configuré avec user non-root.

```dockerfile
# Créer user varuna (UID 1000)
RUN useradd -m -u 1000 varuna && \
    chown -R varuna:varuna /app

USER varuna
```

**Si problème persiste sur Linux:**

```yaml
# docker-compose: Spécifier UID/GID
services:
  backend:
    user: "1000:1000"  # Correspond à UID dans Dockerfile
```

---

## =' ADAPTATION POUR LINUX (Checklist)

### Modifications Requises

| Fichier/Commande | Windows | Linux | Action |
|------------------|---------|-------|--------|
| **docker-compose volumes** | `C:/Users/.../Slides` | `/home/user/.../Slides` | Changer chemin absolu |
| **Firewall** | PowerShell `New-NetFirewallRule` | `sudo ufw allow` | Adapter commandes |
| **IP** | `ipconfig` | `ip addr` ou `hostname -I` | Adapter commande |
| **Test port** | `Test-NetConnection` | `nc -zv` ou `telnet` | Adapter commande |
| **Scripts .sh** | Git Bash ou équivalent `.ps1` | Natif | Aucune modification |
| **Permissions slides** | Auto | Possiblement `chmod`/`chown` | Vérifier permissions |

### Fichiers à Modifier (Linux)

#### 1. docker-compose.phase1.yml

```yaml
# AVANT (Windows):
volumes:
  - C:/Users/junio/Desktop/CHU-UCL/VarunaPoC/Slides:/slides:ro

# APRÈS (Linux):
volumes:
  - /home/user/VarunaPoC/Slides:/slides:ro
  # OU (relatif, portable):
  - ./Slides:/slides:ro
```

#### 2. docker-compose.phase2.1.yml

Même changement que ci-dessus.

#### 3. PROTOCOLE.md

**Section Firewall:**

Ajouter alternative Linux après commandes Windows:

```markdown
### Configuration Firewall

#### Sur Windows (PowerShell Administrateur):
[commandes existantes]

#### Sur Linux (Ubuntu/Debian):

```bash
sudo ufw enable
sudo ufw allow 80/tcp comment "VarunaPoC Frontend"
sudo ufw allow 8000/tcp comment "VarunaPoC Backend"
sudo ufw allow 9090/tcp comment "VarunaPoC Prometheus"
sudo ufw allow 3000/tcp comment "VarunaPoC Grafana"
sudo ufw status
```
```

**Section Obtenir IP:**

```markdown
### Obtenir Adresse IP

#### Sur Windows:
```powershell
ipconfig
```

#### Sur Linux:
```bash
hostname -I  # Simple
# OU
ip -4 addr show | grep inet
```
```

#### 4. Scripts/*.sh

**Vérifier shebang:**

```bash
#!/usr/bin/env bash
#  Portable (trouve bash automatiquement)

# PAS:
#!/bin/bash
#   Assume bash dans /bin (pas toujours vrai)
```

**Scripts existants OK** (utilisent déjà `#!/usr/bin/env bash`).

---

## =Ý RÉCAPITULATIF: CE QUI CHANGE

### Entre Phase 1 et Phase 2.1

| Aspect | Phase 1 | Phase 2.1 | Rebuild Requis? |
|--------|---------|-----------|-----------------|
| **Ports Backend** | `8000:8000` | `0.0.0.0:8000:8000` | L Non (config Docker) |
| **Ports Frontend** | `80:80` | `0.0.0.0:80:80` | L Non (config Docker) |
| **CORS_ORIGINS** | `localhost` | `IP + localhost` | L Non (.env seulement) |
| **VITE_API_URL** | `localhost:8000` | `IP:8000` |  **OUI** (build arg) |
| **GF_SERVER_ROOT_URL** | `localhost:3000` | `IP:3000` | L Non (env var) |
| **Firewall** | Optionnel | **Obligatoire** | N/A |

**  CRITIQUE:** Frontend **DOIT** être rebuild si IP change (VITE_API_URL baked in).

### Entre Windows et Linux

| Aspect | Changement | Effort |
|--------|------------|--------|
| **Chemins volumes** | Chemin absolu différent | P Faible (1 ligne) |
| **Firewall** | Commandes différentes | PP Moyen (4 commandes) |
| **Obtenir IP** | Commande différente | P Faible (1 commande) |
| **Test connectivité** | Commandes différentes | P Faible (adapter) |
| **Docker install** | Desktop vs Engine | PPP (si pas installé) |
| **Scripts .sh** | Aucun |  Fonctionnent déjà |
| **Permissions** | Possiblement `chmod` | P Faible (si besoin) |

**Effort total adaptation Linux:** PP (1-2 heures)

---

## =€ RECOMMANDATIONS

### Pour Déploiement Windows (Actuel)

1.  Utiliser scripts fournis (`.sh` avec Git Bash)
2.  Suivre PROTOCOLE.md tel quel
3.  Rebuild frontend si IP change:
   ```bash
   # Après changement IP dans .env.phase2.1:
   docker-compose -f docker-compose.phase2.1.yml build frontend
   docker-compose -f docker-compose.phase2.1.yml up -d
   ```

### Pour Futur Déploiement Linux

1. **Modifier docker-compose volumes:**
   ```yaml
   # Option portable (recommandé):
   volumes:
     - ./Slides:/slides:ro
   ```

2. **Créer script firewall Linux:**
   ```bash
   Scripts/Deployment/firewall-linux.sh
   ```
   Contenu: Commandes `ufw` équivalentes.

3. **Adapter section Firewall dans PROTOCOLE.md:**
   Ajouter alternative Linux après Windows.

4. **Vérifier permissions slides:**
   ```bash
   ls -la Slides/
   # Si besoin:
   chmod -R a+r Slides/
   ```

5. **Tester déploiement:**
   Scripts `.sh` fonctionnent nativement sur Linux.

---

**VERSION:** 1.0
**DERNIÈRE MISE À JOUR:** 2025-12-04
**AUTEUR:** Équipe VarunaPoC
