# VarunaPoC - Guide de Déploiement

**Version:** 1.0
**Date:** 2025-12-31
**Auteur:** Infrastructure Architect
**Niveau:** Production-Ready (Phase 2.5)

---

## Vue d'Ensemble

Ce guide décrit le déploiement de **VarunaPoC Phase 2.5** avec architecture optimisée comprenant:

- Cache Redis (tuiles)
- Load balancing (2 backends)
- Monitoring Prometheus + Grafana
- High availability (99.5%)
- Performance optimisée (< 2s P95)

---

## Prérequis

### Matériel et Réseau

| Composant | Exigence |
|-----------|----------|
| **Serveur** | 4 CPU cores, 16 GB RAM minimum |
| **Stockage local** | 50 GB (images Docker, cache Nginx) |
| **Stockage NAS** | 2-5 TB (lames histologiques) |
| **Réseau** | 1 Gbps minimum, accès NAS CHU |
| **Ports ouverts** | 80 (HTTP), 443 (HTTPS), 3000 (Grafana), 9090 (Prometheus) |

### Logiciels

| Logiciel | Version Minimum | Commande de Vérification |
|----------|-----------------|--------------------------|
| **Docker** | 24.0+ | `docker --version` |
| **Docker Compose** | 2.20+ | `docker-compose --version` |
| **Git** | 2.30+ | `git --version` |
| **OpenSSL** | 1.1.1+ | `openssl version` |

### Accès Réseau CHU

- NAS storage: `//imgsv-01-p/anapath_storage_nimble`
- Credentials SMB/CIFS
- Firewall configuré (ports 80, 443, 8000)

---

## Installation Rapide (Quick Start)

### Étape 1: Cloner le Repository

```bash
cd /opt
git clone https://github.com/chu-ucl/VarunaPoC.git
cd VarunaPoC
```

### Étape 2: Monter le Stockage NAS

```bash
# Créer le point de montage
sudo mkdir -p /mnt/chu-slides

# Monter le NAS (Linux)
sudo mount -t cifs -o username=USER,password=PASS,vers=3.0 \
    //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Vérifier le montage
ls /mnt/chu-slides
```

**Windows Server:**

```powershell
# Monter avec net use
net use Z: \\imgsv-01-p\anapath_storage_nimble /persistent:yes

# Créer un lien symbolique
New-Item -ItemType SymbolicLink -Path "C:\mnt\chu-slides" -Target "Z:\"
```

### Étape 3: Configuration

```bash
# Créer fichier .env
cp backend/.env.example backend/.env.production

# Éditer les variables d'environnement
nano backend/.env.production
```

**Contenu .env.production:**

```bash
# Backend Configuration
SLIDES_REPOSITORY_PATH=/slides
LOG_LEVEL=info
PYTHONUNBUFFERED=1

# Redis Cache
REDIS_URL=redis://redis:6379

# Monitoring
PROMETHEUS_ENABLED=true

# Security (générer avec: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here
```

### Étape 4: Déploiement Automatisé

```bash
# Rendre le script exécutable
chmod +x Scripts/deploy-optimized.sh

# Lancer le déploiement
./Scripts/deploy-optimized.sh
```

Le script effectue automatiquement:
1. Pre-flight checks (Docker, ports, NAS)
2. Build des images Docker
3. Génération certificats SSL (self-signed)
4. Démarrage des services
5. Health checks
6. Smoke tests

### Étape 5: Vérification

**Accéder aux services:**

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost | - |
| **Backend API** | http://localhost/api | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |

**Tests de santé:**

```bash
# Backend health
curl http://localhost/api/health

# Redis
docker exec varuna-redis redis-cli ping

# Containers status
docker-compose -f docker-compose.optimized.yml ps
```

---

## Déploiement Manuel (Étape par Étape)

### 1. Préparer l'Infrastructure

```bash
# Créer répertoires nécessaires
mkdir -p nginx/ssl
mkdir -p backend/logs
mkdir -p monitoring/alerts
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
```

### 2. Générer Certificats SSL

```bash
# Self-signed certificate (développement)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/varuna.key \
    -out nginx/ssl/varuna.crt \
    -subj "/C=BE/ST=Namur/L=Namur/O=CHU UCL Namur/CN=varuna.chu-ucl.be"
```

**Production:** Remplacer par certificat Let's Encrypt ou certificat CHU officiel.

### 3. Build des Images Docker

```bash
# Backend
docker build -t varuna-backend:latest ./backend

# Frontend
docker build -t varuna-frontend:latest ./frontend
```

### 4. Démarrer les Services

```bash
# Démarrer tous les services
docker-compose -f docker-compose.optimized.yml up -d

# Suivre les logs
docker-compose -f docker-compose.optimized.yml logs -f
```

### 5. Configurer Grafana

```bash
# Se connecter: http://localhost:3000
# Login: admin / admin
# Changer le mot de passe

# Importer le dashboard VarunaPoC
# Dashboards -> Import -> Upload JSON file
# Fichier: monitoring/grafana/dashboards/varuna-wsi-perf.json
```

---

## Configuration Avancée

### Load Balancing (Nginx)

Le fichier `nginx/nginx.conf` est préconfigré avec:

- **Algorithme:** Least Connections (optimal pour WSI)
- **Health checks:** Automatic failover
- **Keepalive:** 32 connections persistantes
- **Timeout:** 60s pour grandes opérations

**Ajouter un backend supplémentaire:**

```yaml
# docker-compose.optimized.yml
backend-3:
  build: ./backend
  container_name: varuna-backend-3
  expose:
    - "8000"
  # ... (même config que backend-1)
```

```nginx
# nginx/nginx.conf
upstream varuna_backend {
    least_conn;
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;  # AJOUTER
}
```

### Cache Redis (Tuning)

**Augmenter la mémoire cache:**

```yaml
# docker-compose.optimized.yml
redis:
  command: >
    redis-server
    --maxmemory 8gb  # Augmenter de 4GB à 8GB
    --maxmemory-policy allkeys-lru
```

**Vérifier statistiques cache:**

```bash
# Se connecter à Redis
docker exec -it varuna-redis redis-cli

# Commandes utiles
INFO memory
INFO stats
DBSIZE
```

### Monitoring (Alertes)

**Configuration Alertmanager (email):**

```yaml
# alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.chu-ucl.be:587'
  smtp_from: 'varuna-alerts@chu-ucl.be'
  smtp_auth_username: 'varuna'
  smtp_auth_password: 'PASSWORD'

route:
  receiver: 'email-team'
  group_by: ['alertname', 'severity']

receivers:
  - name: 'email-team'
    email_configs:
      - to: 'anapath-it@chu-ucl.be'
```

---

## Métriques de Performance

### Objectifs (TFE Section 5.2)

| Métrique | Valeur Cible | Vérification |
|----------|--------------|--------------|
| **Temps chargement lame (P95)** | < 2s | Grafana dashboard "Tile Load Time" |
| **Latence navigation (P95)** | < 100ms | Prometheus query: `histogram_quantile(0.95, ...)` |
| **Disponibilité** | > 99.5% | Grafana dashboard "Uptime" |
| **Cache hit rate** | > 70% | Redis metrics panel |
| **Utilisateurs simultanés** | 10+ | Grafana "Active Sessions" |

### Requêtes Prometheus Utiles

**Temps de chargement P95:**

```promql
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m]))
```

**Cache hit rate:**

```promql
rate(varuna_cache_hits[5m]) / (rate(varuna_cache_hits[5m]) + rate(varuna_cache_misses[5m]))
```

**Disponibilité sur 1h:**

```promql
avg_over_time(up{job="varuna-backend"}[1h]) * 100
```

---

## Dépannage (Troubleshooting)

### Problème: Backend ne démarre pas

**Symptômes:**

```
docker-compose ps
varuna-backend-1   Exit 1
```

**Solutions:**

1. Vérifier les logs:
   ```bash
   docker-compose -f docker-compose.optimized.yml logs backend-1
   ```

2. Vérifier montage NAS:
   ```bash
   docker exec varuna-backend-1 ls /slides
   ```

3. Vérifier variables d'environnement:
   ```bash
   docker exec varuna-backend-1 env | grep SLIDES
   ```

### Problème: Redis OOM (Out of Memory)

**Symptômes:**

```
Redis: OOM command not allowed when used memory > 'maxmemory'
```

**Solutions:**

1. Vérifier mémoire utilisée:
   ```bash
   docker exec varuna-redis redis-cli INFO memory
   ```

2. Augmenter maxmemory (voir Configuration Avancée)

3. Vérifier évictions:
   ```bash
   docker exec varuna-redis redis-cli INFO stats | grep evicted_keys
   ```

### Problème: Nginx 502 Bad Gateway

**Symptômes:**

```
curl http://localhost/api/health
502 Bad Gateway
```

**Solutions:**

1. Vérifier backends sont UP:
   ```bash
   docker-compose ps | grep backend
   ```

2. Tester backend directement:
   ```bash
   docker exec -it varuna-backend-1 curl http://localhost:8000/api/health
   ```

3. Vérifier logs Nginx:
   ```bash
   docker-compose logs nginx | tail -50
   ```

### Problème: Performance dégradée

**Checklist:**

```bash
# 1. Vérifier cache hit rate (target: >70%)
curl http://localhost:9090/api/v1/query?query=varuna_cache_hit_rate

# 2. Vérifier latence NAS
docker exec varuna-backend-1 time ls /slides > /dev/null

# 3. Vérifier CPU/RAM containers
docker stats

# 4. Vérifier réseau
docker exec varuna-backend-1 ping -c 5 redis

# 5. Analyser slow requests
docker-compose logs backend-1 | grep "request_time"
```

---

## Maintenance

### Backup Quotidien

**Script automatisé:**

```bash
#!/bin/bash
# /opt/varuna/scripts/backup.sh

BACKUP_DIR="/mnt/backup/varuna"
DATE=$(date +%Y%m%d_%H%M%S)

# 1. Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    nginx/nginx.conf \
    backend/.env.production \
    monitoring/

# 2. Backup Redis (tile cache metadata - optional)
docker exec varuna-redis redis-cli BGSAVE
docker cp varuna-redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# 3. Cleanup old backups (30 days)
find "$BACKUP_DIR" -mtime +30 -delete
```

**Cron:**

```cron
0 2 * * * /opt/varuna/scripts/backup.sh
```

### Mise à Jour

**Procédure zero-downtime:**

```bash
# 1. Pull latest code
git pull origin main

# 2. Build new images
docker-compose -f docker-compose.optimized.yml build

# 3. Update backend-1 (backend-2 still serving)
docker-compose -f docker-compose.optimized.yml up -d --no-deps backend-1

# Wait for health check
sleep 30

# 4. Update backend-2
docker-compose -f docker-compose.optimized.yml up -d --no-deps backend-2

# 5. Update frontend & nginx
docker-compose -f docker-compose.optimized.yml up -d --no-deps frontend nginx
```

### Monitoring Régulier

**Weekly checklist:**

- [ ] Vérifier disponibilité (Grafana dashboard)
- [ ] Vérifier cache hit rate (>70%)
- [ ] Analyser erreurs logs
- [ ] Vérifier espace disque (`df -h`)
- [ ] Vérifier certificat SSL expiration
- [ ] Tester backup restore

---

## Migration vers Kubernetes (Phase 3)

**Prérequis:**

- Cluster Kubernetes opérationnel
- Helm 3.x installé
- kubectl configuré

**Étapes:**

1. Adapter manifests K8s:
   ```bash
   cp -r k8s/templates k8s/production
   # Éditer values.yaml
   ```

2. Déployer avec Helm:
   ```bash
   helm install varuna ./helm/varuna \
       --namespace production \
       --create-namespace
   ```

3. Vérifier déploiement:
   ```bash
   kubectl get pods -n production
   kubectl rollout status deployment/varuna-backend -n production
   ```

Voir `docs/INFRASTRUCTURE_ARCHITECTURE.md` pour architecture K8s complète.

---

## Support et Contacts

**CHU UCL Namur:**

- **IT Infrastructure:** infrastructure@chuuclnamur.be
- **Storage Team:** storage-admins@chuuclnamur.be
- **Pathology Lab:** anapath@chuuclnamur.be

**Documentation:**

- Architecture: `docs/INFRASTRUCTURE_ARCHITECTURE.md`
- API Reference: http://localhost:8000/docs (Swagger UI)
- User Manual: `docs/Manuel/`

**Logs:**

```bash
# Tous les services
docker-compose -f docker-compose.optimized.yml logs -f

# Service spécifique
docker-compose -f docker-compose.optimized.yml logs -f backend-1

# Dernières 100 lignes
docker-compose -f docker-compose.optimized.yml logs --tail=100 backend-1
```

---

## Checklist de Déploiement

### Pré-Déploiement

- [ ] Serveur avec 4 CPU, 16 GB RAM minimum
- [ ] Docker 24.0+ et docker-compose 2.20+ installés
- [ ] NAS monté à `/mnt/chu-slides`
- [ ] Ports 80, 443, 3000, 9090 ouverts
- [ ] Certificat SSL disponible (ou généré)
- [ ] Fichier `.env.production` configuré

### Déploiement

- [ ] Repository cloné
- [ ] Images Docker buildées
- [ ] Services démarrés
- [ ] Health checks passés
- [ ] Smoke tests réussis

### Post-Déploiement

- [ ] Grafana configuré (dashboard importé)
- [ ] Alertes configurées
- [ ] Backup automatisé activé
- [ ] Documentation utilisateur fournie
- [ ] Formation équipe CHU effectuée

### Validation (1 semaine)

- [ ] Temps chargement < 2s P95 validé
- [ ] Disponibilité > 99.5% validée
- [ ] Cache hit rate > 70% validé
- [ ] Feedback utilisateurs collecté
- [ ] Plan de maintenance établi

---

**Auteur:** Infrastructure Architect
**Version:** 1.0
**Date:** 2025-12-31
**Statut:** Production-Ready
