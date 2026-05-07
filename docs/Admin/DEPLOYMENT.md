# Déploiement — du laptop dev au serveur hôpital

Cette page décrit la procédure de déploiement complet sur un nouvel hôte.
Pour les ports, la topologie et la liste des services : voir
[INFRASTRUCTURE.md](./INFRASTRUCTURE.md). Pour le choix des modules à
activer : voir [PROFILES.md](./PROFILES.md).

---

## Pré-requis hôte

### Logiciel

- Docker Engine ≥ 24.0 avec Compose v2 (`docker compose` — pas `docker-compose`)
- 50 Go d'espace disque libre minimum (200 Go pour prod + monitoring)
- Accès Internet pour le pull des images au premier démarrage
- Linux (Ubuntu 22.04+, RHEL 8+) ou Windows avec WSL2 + Docker Desktop

### Hardware <a id="hardware"></a>

| Profil prévu                              | RAM    | CPU      | Disque  | GPU              |
|-------------------------------------------|--------|----------|---------|------------------|
| Workstation dev                           | 8 Go   | 2 cœurs  | 20 Go   | optionnel        |
| Démo / pilote (prod sans monitoring)      | 16 Go  | 4 cœurs  | 100 Go  | optionnel        |
| Production hôpital                        | 32 Go  | 8 cœurs  | 1 To    | recommandé (ML)  |
| Hôte d'entraînement ML séparé             | 64 Go  | 12 cœurs | 2 To    | NVIDIA CUDA req. |

Le stockage des lames histologiques (`Slides/`) compte ~60 Go pour le
dataset de test ; en production hospitalière, prévoir plusieurs To et un
montage NFS / SMB monté en lecture seule sur l'hôte (variable
`SLIDES_HOST_PATH`).

### Pour les hôtes avec GPU

```bash
# NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

Vérifier : `docker run --rm --gpus all nvidia/cuda:12.2.0-base nvidia-smi`.

---

## Procédure — workstation dev (10 min)

```bash
# 1. Cloner le repo
git clone https://github.com/Yanstart/VarunaPoC.git
cd VarunaPoC

# 2. Configurer l'environnement
cp .env.dev.example .env

# 3. Démarrer l'infra
docker compose --profile dev up -d

# 4. Vérifier
docker compose ps
docker compose --profile dev logs --tail=50

# 5. Lancer backend et frontend localement
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000 &

cd ../frontend
npm ci
npm run dev
```

Ouvrir http://localhost:5173.

---

## Procédure — production (30–60 min) <a id="prod"></a>

### Étape 1 — préparer l'hôte

```bash
sudo mkdir -p /opt/varuna && cd /opt/varuna
sudo chown -R $USER:$USER /opt/varuna

# Cloner ou pull la version cible (tag de release recommandé)
git clone https://github.com/Yanstart/VarunaPoC.git .
git checkout v0.1.0
```

### Étape 2 — configurer les secrets

```bash
cp .env.prod.example .env

# Générer des passwords forts pour CHAQUE variable CHANGE_ME_*
# Exemple :
sed -i "s|CHANGE_ME_strong_db_password|$(openssl rand -base64 32 | tr -d '+/=' | head -c 32)|g" .env
# … répéter pour redis, keycloak, grafana, minio, mlops-db
```

Auditer le fichier `.env` final : aucune valeur ne doit commencer par
`CHANGE_ME_`. Restreindre les permissions :

```bash
chmod 600 .env
```

### Étape 3 — TLS

Placer les certificats dans `nginx/ssl/`, ou pointer `NGINX_SSL_CERT` /
`NGINX_SSL_KEY` ailleurs dans `.env`. Pour générer un cert auto-signé en
test :

```bash
./nginx/generate-ssl-certs.sh
```

### Étape 4 — Slides

Monter la partition lames :

```bash
sudo mkdir -p /mnt/chu-slides
# Si NFS :
sudo mount -t nfs nas.hospital.example:/varuna/slides /mnt/chu-slides
# Persister dans /etc/fstab

# Vérifier qu'il y a des lames
ls /mnt/chu-slides | head
```

Et pointer `SLIDES_HOST_PATH=/mnt/chu-slides` dans `.env`.

### Étape 5 — pull et up

```bash
# Pull explicite (sinon up le fait)
docker compose --profile prod --profile monitoring pull

# Démarrage
docker compose --profile prod --profile monitoring up -d

# Suivre le démarrage
docker compose --profile prod --profile monitoring logs -f --tail=20
```

Comptez ~3 minutes pour que tout soit `healthy`. Keycloak met le plus
longtemps (~90 s).

### Étape 6 — validation

```bash
# Tous les services healthy ?
docker compose --profile prod --profile monitoring ps

# API ?
curl -fsS https://varuna.hospital.example/api/v1/health

# Auth ?
curl -fsS https://varuna.hospital.example/api/v1/auth/whoami \
  -H "Authorization: Bearer $TOKEN"

# Métriques exposées ?
curl -fsS http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'
```

---

## Hardening prod hospital

Le compose unifié privilégie la lisibilité et utilise UN réseau bridge.
Pour la prod hospitalière, créer un override `docker-compose.hospital.yml`
qui :

- Sépare `auth` et `monitoring` sur des réseaux internes (`internal: true`)
- Pin chaque image par SHA digest (cf. `docker-compose.production.yml` archivé
  dans `Archives/Phase2-Deployment/` pour le pattern)
- Active des `deploy.resources.limits` stricts
- Migre les passwords vers Docker Secrets (pattern `*_FILE`)
- Restreint les ports admin sur `127.0.0.1` (Grafana, Prometheus, Alertmanager)

Lancer avec :

```bash
docker compose -f docker-compose.yml -f docker-compose.hospital.yml \
  --profile prod --profile monitoring up -d
```

Voir [docs/Deployment/](../Deployment/) pour les checklists CHU spécifiques
(secrets management, secret rotation, break-glass, network scenarios).

---

## Mises à jour

```bash
git fetch origin
git checkout v0.x.y                  # nouvelle release
docker compose --profile prod --profile monitoring pull
docker compose --profile prod --profile monitoring up -d
```

`migration` ré-exécute `alembic upgrade head` automatiquement avant que
backend démarre. Pour rollback, voir
[`Scripts/rollback.sh`](../../Scripts/rollback.sh) et
[`UPGRADE_PROTOCOL.md`](../Deployment/UPGRADE_PROTOCOL.md).

---

## Voir aussi

- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) — ports, réseaux, volumes
- [PROFILES.md](./PROFILES.md) — quels profils activer
- [OPERATIONS.md](./OPERATIONS.md) — opérations du quotidien
- [services/](./services/) — fiches par service
- [docs/Deployment/PRODUCTION_RUNBOOK.md](../Deployment/PRODUCTION_RUNBOOK.md) — runbook complet CHU
