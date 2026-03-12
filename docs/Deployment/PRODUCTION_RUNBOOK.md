# VarunaPoC - Production Deployment Runbook

**Version:** 1.0 | **Date:** 2026-03-11 | **Audience:** IT hospitalier

---

## Vue d'ensemble

Ce runbook couvre le deploiement de VarunaPoC en production dans un environnement hospitalier.
L'application est deployee via Docker Compose avec des profiles optionnels (auth, monitoring).

**Architecture des services :**

| Service | Role | Port interne |
|---------|------|-------------|
| nginx | Reverse proxy, TLS, cache tuiles | 80, 443 |
| backend (x2) | API FastAPI + OpenSlide | 8000 |
| frontend | SPA Vite (servi par nginx interne) | 80 |
| db | PostgreSQL 16 + PostGIS | 5432 |
| redis | Cache tuiles LRU | 6379 |
| migration | Init container (alembic) | - |
| keycloak | OIDC (profile auth) | 8080 |
| keycloak-db | PostgreSQL pour KC (profile auth) | 5432 |
| prometheus | Metriques (profile monitoring) | 9090 |
| grafana | Dashboards (profile monitoring) | 3000 |

---

## 1. Prerequis

### 1.1 Serveur

| Composant | Minimum | Recommande |
|-----------|---------|------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Stockage local | 50 GB (Docker + cache) | 100 GB |
| Stockage NAS | 1 TB (lames WSI) | 5 TB |
| Reseau | 1 Gbps | 10 Gbps |
| OS | Ubuntu 22.04 / RHEL 8+ | Ubuntu 24.04 |

### 1.2 Logiciels

```bash
# Verifier les prerequis
docker --version          # >= 24.0
docker compose version    # >= 2.20
openssl version           # >= 1.1.1
```

### 1.3 Acces reseau

- NAS slides monte en lecture seule
- Ports 80, 443 ouverts (entree)
- Port 8180 ouvert si Keycloak admin necessaire
- Ports 3000, 9090 restreints au reseau monitoring

---

## 2. Installation

### 2.1 Cloner le repository

```bash
cd /opt
git clone https://github.com/Yanstart/VarunaPoC.git
cd VarunaPoC
git checkout v1.0.0   # Utiliser le tag de release
```

### 2.2 Monter le stockage NAS

```bash
# Creer le point de montage
sudo mkdir -p /mnt/chu-slides

# Monter le NAS (adapter credentials)
sudo mount -t cifs -o username=USER,password=PASS,vers=3.0,ro \
    //serveur-nas/partage-lames /mnt/chu-slides

# Verifier le montage
ls /mnt/chu-slides | head -5

# Rendre persistant via /etc/fstab
echo '//serveur-nas/partage-lames /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,ro,_netdev 0 0' | sudo tee -a /etc/fstab
```

### 2.3 Generer les certificats TLS

```bash
# Option A : Certificat auto-signe (test)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/varuna.key \
    -out nginx/ssl/varuna.crt \
    -subj "/CN=varuna.chu-ucl.be"

# Option B : Certificat signe par la CA de l'hopital
# Placer les fichiers fournis par l'IT dans nginx/ssl/
cp /chemin/vers/certificat.crt nginx/ssl/varuna.crt
cp /chemin/vers/cle-privee.key nginx/ssl/varuna.key
chmod 600 nginx/ssl/varuna.key
```

### 2.4 Configurer l'environnement

```bash
cp .env.production.example .env.production
```

Editer `.env.production` et remplir les champs obligatoires :

```bash
# Generer des mots de passe forts
POSTGRES_PASSWORD=$(openssl rand -base64 24)
REDIS_PASSWORD=$(openssl rand -base64 24)

echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

# Si auth activee :
KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -base64 24)
KEYCLOAK_DB_PASSWORD=$(openssl rand -base64 24)

# Si monitoring active :
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 24)
```

**Variables obligatoires :**

| Variable | Description | Exemple |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL | (genere) |
| `REDIS_PASSWORD` | Mot de passe Redis | (genere) |
| `SLIDES_HOST_PATH` | Chemin NAS sur l'hote | `/mnt/chu-slides` |
| `CORS_ORIGINS` | Origines autorisees | `https://varuna.chu-ucl.be` |

---

## 3. Deploiement

### 3.1 Services de base (sans auth, sans monitoring)

```bash
docker compose -f docker-compose.production.yml \
    --env-file .env.production \
    up -d
```

### 3.2 Avec authentification

```bash
# S'assurer que AUTH_ENABLED=true dans .env.production
docker compose -f docker-compose.production.yml \
    --env-file .env.production \
    --profile auth \
    up -d
```

### 3.3 Stack complet (auth + monitoring)

```bash
docker compose -f docker-compose.production.yml \
    --env-file .env.production \
    --profile auth --profile monitoring \
    up -d
```

### 3.4 Verifier le deploiement

```bash
# Verifier que tous les services sont sains
docker compose -f docker-compose.production.yml ps

# Attendre que tous les healthchecks passent (2-3 min)
watch -n 5 'docker compose -f docker-compose.production.yml ps'

# Tester le backend
curl -k https://localhost/api/health
# Attendu : {"status":"healthy"}

# Tester le frontend
curl -sk https://localhost/ | head -5
# Attendu : HTML de l'application
```

---

## 4. Operations courantes

### 4.1 Consulter les logs

```bash
# Tous les services
docker compose -f docker-compose.production.yml logs --tail 100

# Un service specifique
docker compose -f docker-compose.production.yml logs backend --tail 200 -f

# Erreurs uniquement
docker compose -f docker-compose.production.yml logs backend 2>&1 | grep -i error
```

### 4.2 Redemarrer un service

```bash
# Redemarrer le backend (sans downtime grace aux replicas)
docker compose -f docker-compose.production.yml restart backend

# Redemarrer nginx (breve coupure)
docker compose -f docker-compose.production.yml restart nginx
```

### 4.3 Mise a jour de l'application

```bash
# 1. Tirer les nouvelles images
docker compose -f docker-compose.production.yml pull

# 2. Recreer les services modifies (rolling update)
docker compose -f docker-compose.production.yml \
    --env-file .env.production \
    up -d --no-deps backend frontend nginx

# 3. Verifier les healthchecks
docker compose -f docker-compose.production.yml ps
```

### 4.4 Backup de la base de donnees

```bash
# Backup
docker compose -f docker-compose.production.yml exec db \
    pg_dump -U varuna -Fc varuna > backup_$(date +%Y%m%d_%H%M%S).dump

# Restore (arret du backend necessaire)
docker compose -f docker-compose.production.yml stop backend
docker compose -f docker-compose.production.yml exec -T db \
    pg_restore -U varuna -d varuna --clean < backup_YYYYMMDD.dump
docker compose -f docker-compose.production.yml start backend
```

### 4.5 Vider le cache tuiles

```bash
# Cache nginx (10 GB max)
docker compose -f docker-compose.production.yml exec nginx \
    rm -rf /var/cache/nginx/tiles/*

# Cache Redis
docker compose -f docker-compose.production.yml exec redis \
    redis-cli -a $REDIS_PASSWORD FLUSHDB
```

---

## 5. Diagnostics

### 5.1 Checklist de diagnostic rapide

```bash
# 1. Services actifs ?
docker compose -f docker-compose.production.yml ps

# 2. Espace disque ?
df -h /var/lib/docker
df -h /mnt/chu-slides

# 3. Backend accessible ?
curl -k https://localhost/api/health

# 4. Base de donnees accessible ?
docker compose -f docker-compose.production.yml exec db \
    pg_isready -U varuna

# 5. NAS monte ?
ls /mnt/chu-slides | head -3

# 6. Lames detectees ?
curl -k https://localhost/api/slides/browse
```

### 5.2 Problemes courants

| Symptome | Cause probable | Solution |
|----------|---------------|----------|
| 502 Bad Gateway | Backend non pret | `docker compose logs backend` puis attendre healthcheck |
| Lames non detectees | NAS non monte | `mount -a` puis redemarrer backend |
| Tuiles lentes | Cache froid | Recharger la lame, les tuiles seront cachees |
| Connexion DB refusee | Migration echouee | `docker compose logs migration` |
| CORS error (navigateur) | CORS_ORIGINS mal configure | Verifier `.env.production` et redemarrer |
| Keycloak 503 | Demarrage lent (~90s) | Patienter, verifier `docker compose logs keycloak` |

### 5.3 Performance

```bash
# Temps de reponse API
curl -k -w "Time: %{time_total}s\n" -o /dev/null -s https://localhost/api/health

# Utilisation memoire par service
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Connexions nginx
curl -s http://localhost/nginx_status 2>/dev/null || \
    docker compose -f docker-compose.production.yml exec nginx \
    wget -qO- http://localhost/nginx_status
```

---

## 6. Arret et desinstallation

### 6.1 Arret propre

```bash
docker compose -f docker-compose.production.yml \
    --profile auth --profile monitoring \
    down
```

### 6.2 Arret avec suppression des volumes (perte de donnees)

```bash
# ATTENTION : supprime toutes les donnees (DB, cache, Grafana)
docker compose -f docker-compose.production.yml \
    --profile auth --profile monitoring \
    down -v
```

---

## 7. Contacts et references

| Ressource | Lien |
|-----------|------|
| Repository | `https://github.com/Yanstart/VarunaPoC` |
| Documentation API | `https://varuna.chu-ucl.be/docs` (Swagger UI) |
| Grafana dashboards | `https://varuna.chu-ucl.be:3000` |
| Prometheus | `https://varuna.chu-ucl.be:9090` |
| Keycloak admin | `https://varuna.chu-ucl.be:8180` |

---

## Annexe A : Variables d'environnement

Voir `.env.production.example` pour la liste complete.
Toutes les variables marquees `[REQUIRED]` doivent etre remplies avant deploiement.

## Annexe B : Ports utilises

| Port | Service | Direction | Requis |
|------|---------|-----------|--------|
| 80 | HTTP (redirect HTTPS) | Entree | Oui |
| 443 | HTTPS (application) | Entree | Oui |
| 3000 | Grafana | Entree (restreint) | Non |
| 8180 | Keycloak admin | Entree (restreint) | Non |
| 9090 | Prometheus | Entree (restreint) | Non |
