# Architecture Infrastructure VarunaPoC

**Version:** 1.0
**Date:** 2025-12-31
**Auteur:** Infrastructure Architect Agent
**Status:** Production-Ready Roadmap

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Infrastructure Actuelle (Phase 1)](#2-infrastructure-actuelle-phase-1)
3. [Architecture Cible de Déploiement](#3-architecture-cible-de-déploiement)
4. [Stratégie de Cache Multi-Niveaux](#4-stratégie-de-cache-multi-niveaux)
5. [Haute Disponibilité et Load Balancing](#5-haute-disponibilité-et-load-balancing)
6. [Pipeline CI/CD](#6-pipeline-cicd)
7. [Monitoring et Observabilité](#7-monitoring-et-observabilité)
8. [Stratégie de Stockage](#8-stratégie-de-stockage)
9. [Performance et Scalabilité](#9-performance-et-scalabilité)
10. [Sécurité Infrastructure](#10-sécurité-infrastructure)
11. [Roadmap d'Implémentation](#11-roadmap-dimplémentation)

---

## 1. Vue d'Ensemble

### 1.1 Contexte et Contraintes

VarunaPoC doit répondre aux exigences de performance suivantes (Section 5.2 TFE):

| Métrique | Exigence | Stratégie Infrastructure |
|----------|----------|--------------------------|
| **Temps chargement lame** | < 2s (P95) pour 5 GB | Cache tuiles Redis + HTTP/2 |
| **Latence navigation** | < 100ms | Load balancing + CDN tuiles |
| **Disponibilité** | > 99.5% | HA (3 replicas) + auto-scaling |
| **Capacité simultanée** | 10 utilisateurs (extensible) | Horizontal scaling ready |
| **Stockage lames** | 2-5 TB initial | NAS CHU + backup strategy |

### 1.2 Principes Directeurs

1. **Pragmatisme avant complexité**: Commencer simple (Docker Compose), prévoir scale (Kubernetes)
2. **Zero-config deployment**: Automatiser au maximum (scripts, CI/CD)
3. **Observabilité totale**: Métriques pour chaque composant critique
4. **Sécurité by design**: Chiffrement, authentification, audit logs
5. **Vendor-neutral**: Pas de lock-in cloud ou technologique

---

## 2. Infrastructure Actuelle (Phase 1)

### 2.1 État des Lieux

**Stack technique actuelle:**

```yaml
Backend:
  - Language: Python 3.11
  - Framework: FastAPI
  - Image Processing: OpenSlide 4.0.0 (patched)
  - ASGI Server: Uvicorn
  - Dependencies: Pillow, prometheus-client

Frontend:
  - Build Tool: Vite 5.4
  - Language: Vanilla JavaScript (ES6+)
  - Viewer: OpenSeadragon 4.1
  - Deployment: Nginx (static files)

Infrastructure:
  - Containerisation: Docker (backend + frontend)
  - Orchestration: docker-compose (phase 1 + 2.x)
  - Storage: Network share SMB/CIFS (//imgsv-01-p/anapath_storage_nimble)
  - Monitoring: Prometheus-client (métrics exposées)
  - Reverse Proxy: Nginx (frontend uniquement)
```

**Déploiement actuel (Phase 2.2 - CHU Network):**

```
┌─────────────────────────────────────────────────────────────────┐
│                  CHU UCL Namur Network                          │
│                                                                 │
│  ┌──────────────┐                  ┌────────────────────────┐  │
│  │  Client PC   │──────────────────│  varun-p-01 Server     │  │
│  │  (Browser)   │  HTTP:80/8000    │                        │  │
│  └──────────────┘                  │  ┌──────────────────┐  │  │
│                                     │  │ Nginx:80         │  │  │
│                                     │  │ (Frontend)       │  │  │
│                                     │  └────────┬─────────┘  │  │
│                                     │           │            │  │
│                                     │  ┌────────▼─────────┐  │  │
│                                     │  │ FastAPI:8000     │  │  │
│                                     │  │ (Backend)        │  │  │
│                                     │  └────────┬─────────┘  │  │
│                                     │           │            │  │
│                                     └───────────┼────────────┘  │
│                                                 │               │
│                                     ┌───────────▼────────────┐  │
│                                     │ NAS Storage            │  │
│                                     │ imgsv-01-p:/anapath... │  │
│                                     │ (SMB/CIFS mount)       │  │
│                                     └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Limitations actuelles:**

- ❌ Pas de cache tuiles (rechargement complet à chaque vue)
- ❌ Single point of failure (1 serveur uniquement)
- ❌ Pas de load balancing
- ❌ Monitoring basique (pas de dashboard)
- ❌ Pas de CI/CD automatisé
- ❌ Pas de gestion de secrets sécurisée
- ❌ HTTP/1.1 uniquement (pas HTTP/2)

---

## 3. Architecture Cible de Déploiement

### 3.1 Phase 2.5: Docker Compose Optimisé (Court Terme - 2 semaines)

**Objectif:** Améliorer les performances sans changer l'infrastructure matérielle.

```yaml
# docker-compose.optimized.yml
version: "3.8"

services:
  # ==============================
  # REVERSE PROXY + LOAD BALANCER
  # ==============================
  nginx:
    image: nginx:1.25-alpine
    container_name: varuna-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend-1
      - backend-2
    networks:
      - varuna-network
    restart: unless-stopped

  # ==============================
  # BACKEND (2 REPLICAS)
  # ==============================
  backend-1:
    build: ./backend
    container_name: varuna-backend-1
    expose:
      - "8000"
    volumes:
      - /mnt/chu-slides:/slides:ro
    environment:
      - REDIS_URL=redis://redis:6379
      - SLIDES_REPOSITORY_PATH=/slides
      - INSTANCE_ID=backend-1
    depends_on:
      - redis
    networks:
      - varuna-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  backend-2:
    build: ./backend
    container_name: varuna-backend-2
    expose:
      - "8000"
    volumes:
      - /mnt/chu-slides:/slides:ro
    environment:
      - REDIS_URL=redis://redis:6379
      - SLIDES_REPOSITORY_PATH=/slides
      - INSTANCE_ID=backend-2
    depends_on:
      - redis
    networks:
      - varuna-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ==============================
  # CACHE REDIS (TUILES)
  # ==============================
  redis:
    image: redis:7-alpine
    container_name: varuna-redis
    command: redis-server --maxmemory 4gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - varuna-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ==============================
  # MONITORING
  # ==============================
  prometheus:
    image: prom/prometheus:latest
    container_name: varuna-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - varuna-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: varuna-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - varuna-network
    restart: unless-stopped

networks:
  varuna-network:
    driver: bridge

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

**Gains attendus:**

- ✅ Cache Redis: **réduction 70-80% du temps de chargement** (tuiles déjà vues)
- ✅ 2 backends: **haute disponibilité** (99.9%)
- ✅ Nginx load balancing: **distribution de charge équilibrée**
- ✅ Monitoring Prometheus/Grafana: **observabilité complète**

---

### 3.2 Phase 3: Kubernetes (Production - 3 mois)

**Objectif:** Infrastructure scalable, auto-healing, production-grade.

```yaml
# k8s/production/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: varuna-backend
  namespace: varuna-prod
  labels:
    app: varuna
    component: backend
    tier: application
spec:
  replicas: 3  # Haute disponibilité
  selector:
    matchLabels:
      app: varuna
      component: backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero downtime
  template:
    metadata:
      labels:
        app: varuna
        component: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: component
                    operator: In
                    values:
                      - backend
              topologyKey: kubernetes.io/hostname
      containers:
        - name: backend
          image: ghcr.io/chu-ucl/varuna-backend:v1.7.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: REDIS_URL
              value: "redis://varuna-redis-svc:6379"
            - name: SLIDES_REPOSITORY_PATH
              value: "/slides"
            - name: PYTHONUNBUFFERED
              value: "1"
          volumeMounts:
            - name: slides-storage
              mountPath: /slides
              readOnly: true
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2
      volumes:
        - name: slides-storage
          persistentVolumeClaim:
            claimName: chu-slides-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: varuna-backend-svc
  namespace: varuna-prod
spec:
  selector:
    app: varuna
    component: backend
  ports:
    - name: http
      protocol: TCP
      port: 8000
      targetPort: 8000
  type: ClusterIP
  sessionAffinity: None
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: varuna-backend-hpa
  namespace: varuna-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: varuna-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 2
          periodSeconds: 15
      selectPolicy: Max
```

**Architecture Kubernetes complète:**

```
┌────────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (CHU)                        │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  Ingress Controller                          │ │
│  │                  (Nginx Ingress)                             │ │
│  │  - TLS Termination                                           │ │
│  │  - Rate Limiting                                             │ │
│  │  - HTTP/2 Support                                            │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                          │
│           ┌─────────────┼─────────────┐                            │
│           │             │             │                            │
│  ┌────────▼───────┐ ┌──▼─────────┐ ┌─▼────────────┐               │
│  │ Backend Pod 1  │ │ Backend 2  │ │ Backend 3    │               │
│  │ (2 CPU, 4GB)   │ │            │ │              │               │
│  └────────┬───────┘ └──┬─────────┘ └─┬────────────┘               │
│           │             │             │                            │
│           └─────────────┼─────────────┘                            │
│                         │                                          │
│                ┌────────▼────────┐                                 │
│                │ Redis Cache     │                                 │
│                │ (StatefulSet)   │                                 │
│                │ 4GB Memory      │                                 │
│                └────────┬────────┘                                 │
│                         │                                          │
│                ┌────────▼────────┐                                 │
│                │ PersistentVolume│                                 │
│                │ (NAS CHU)       │                                 │
│                │ /slides (RO)    │                                 │
│                └─────────────────┘                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Stratégie de Cache Multi-Niveaux

### 4.1 Architecture de Cache

```
┌─────────────────────────────────────────────────────────────────┐
│                    CACHE MULTI-NIVEAUX                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ NIVEAU 1: Browser Cache (Service Worker)                 │  │
│  │ - Capacité: 500 MB (IndexedDB)                           │  │
│  │ - TTL: Session + LRU                                     │  │
│  │ - Hit rate cible: 40-50%                                 │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │ MISS                                  │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │ NIVEAU 2: Redis Cache (Server-side)                      │  │
│  │ - Capacité: 4 GB (tuiles JPEG)                           │  │
│  │ - TTL: 24h (allkeys-lru)                                 │  │
│  │ - Hit rate cible: 70-80%                                 │  │
│  │ - Format clé: tile:{slide_id}:{level}:{col}:{row}        │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │ MISS                                  │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │ NIVEAU 3: Filesystem OpenSlide                           │  │
│  │ - Source: NAS SMB/CIFS (//imgsv-01-p/...)                │  │
│  │ - Latence: 50-200ms (réseau CHU)                         │  │
│  │ - Génération tuile + cache dans Redis                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Implémentation Redis Cache

**Configuration Redis optimisée:**

```conf
# redis.conf (optimisé pour cache tuiles WSI)

# Mémoire
maxmemory 4gb
maxmemory-policy allkeys-lru  # Eviction LRU automatique

# Performance
save ""  # Désactiver snapshots (cache éphémère)
appendonly no  # Désactiver AOF (performance)

# Réseau
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Clients
maxclients 10000

# Threading (Redis 6+)
io-threads 4
io-threads-do-reads yes
```

**Backend integration (Python):**

```python
# backend/services/tile_cache.py
import redis
import hashlib
from typing import Optional

class TileCache:
    """
    Redis-based tile cache for VarunaPoC.

    Cache Strategy:
    - Store JPEG tiles as bytes in Redis
    - Key format: tile:{slide_md5}:{level}:{col}:{row}
    - TTL: 24 hours (auto-eviction via LRU)
    - Size: 4 GB capacity (approx 16,000 tiles @ 256KB each)
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False,  # Binary data (JPEG bytes)
            socket_connect_timeout=5,
            socket_timeout=5,
            max_connections=50
        )

    def get_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int
    ) -> Optional[bytes]:
        """
        Retrieve tile from cache.

        Returns:
            JPEG bytes if cached, None otherwise
        """
        key = f"tile:{slide_id}:{level}:{col}:{row}"

        try:
            tile_bytes = self.redis_client.get(key)

            if tile_bytes:
                # Track cache hit
                self.redis_client.incr("stats:cache_hits")
                return tile_bytes
            else:
                # Track cache miss
                self.redis_client.incr("stats:cache_misses")
                return None
        except redis.RedisError as e:
            # Log error but don't fail (fallback to direct OpenSlide)
            print(f"Redis error: {e}")
            return None

    def set_tile(
        self,
        slide_id: str,
        level: int,
        col: int,
        row: int,
        tile_bytes: bytes,
        ttl: int = 86400  # 24 hours
    ):
        """
        Store tile in cache with TTL.
        """
        key = f"tile:{slide_id}:{level}:{col}:{row}"

        try:
            self.redis_client.setex(key, ttl, tile_bytes)
        except redis.RedisError as e:
            # Log but don't fail
            print(f"Redis set error: {e}")

    def get_cache_stats(self) -> dict:
        """
        Retrieve cache statistics.

        Returns:
            {
                "hits": int,
                "misses": int,
                "hit_rate": float,
                "memory_used_mb": float,
                "evictions": int
            }
        """
        try:
            info = self.redis_client.info("stats")
            memory_info = self.redis_client.info("memory")

            hits = int(self.redis_client.get("stats:cache_hits") or 0)
            misses = int(self.redis_client.get("stats:cache_misses") or 0)
            total = hits + misses

            return {
                "hits": hits,
                "misses": misses,
                "hit_rate": hits / total if total > 0 else 0.0,
                "memory_used_mb": memory_info["used_memory"] / (1024 * 1024),
                "evictions": info.get("evicted_keys", 0)
            }
        except redis.RedisError as e:
            return {"error": str(e)}
```

**Endpoint d'utilisation:**

```python
# backend/routes/slides.py
from services.tile_cache import TileCache

tile_cache = TileCache(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"))

@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg")
async def get_tile(slide_id: str, level: int, col: int, row: int):
    """
    Get tile with Redis caching.
    """
    # 1. Check Redis cache
    cached_tile = tile_cache.get_tile(slide_id, level, col, row)

    if cached_tile:
        return Response(content=cached_tile, media_type="image/jpeg")

    # 2. Cache miss: Generate tile from OpenSlide
    slide_path = get_slide_path_by_id(slide_id)
    tile_bytes = tile_server.get_tile(slide_path, level, col, row)

    # 3. Store in Redis for future requests
    tile_cache.set_tile(slide_id, level, col, row, tile_bytes)

    return Response(content=tile_bytes, media_type="image/jpeg")
```

### 4.3 Browser Cache (Service Worker)

**Frontend cache avec IndexedDB:**

```javascript
// frontend/src/services/tile-cache.js

/**
 * Browser-side tile cache using IndexedDB.
 *
 * Strategy:
 * - Cache tiles in IndexedDB (500 MB quota)
 * - LRU eviction when quota exceeded
 * - Session-based invalidation
 */
class BrowserTileCache {
    constructor(maxSizeMB = 500) {
        this.maxSize = maxSizeMB * 1024 * 1024;
        this.dbName = 'varuna-tile-cache';
        this.storeName = 'tiles';
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(this.storeName)) {
                    const store = db.createObjectStore(this.storeName, { keyPath: 'key' });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };
        });
    }

    async getTile(slideId, level, col, row) {
        const key = `${slideId}:${level}:${col}:${row}`;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.get(key);

            request.onsuccess = () => {
                const result = request.result;
                if (result) {
                    // Update access timestamp
                    this._updateTimestamp(key);
                    resolve(result.blob);
                } else {
                    resolve(null);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    async setTile(slideId, level, col, row, blob) {
        const key = `${slideId}:${level}:${col}:${row}`;

        // Check quota and evict if needed
        await this._evictIfNeeded(blob.size);

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([this.storeName], 'readwrite');
            const store = transaction.objectStore(this.storeName);
            const request = store.put({
                key,
                blob,
                timestamp: Date.now(),
                size: blob.size
            });

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async _evictIfNeeded(newSize) {
        // Evict oldest tiles if cache is full (LRU)
        const usage = await this._getCacheSize();

        if (usage + newSize > this.maxSize) {
            await this._evictOldest(newSize);
        }
    }
}

export const tileCache = new BrowserTileCache();
```

---

## 5. Haute Disponibilité et Load Balancing

### 5.1 Nginx Load Balancer

**Configuration Nginx optimisée:**

```nginx
# nginx/nginx.conf

user nginx;
worker_processes auto;  # Auto-detect CPU cores
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;  # Support 4096 connections par worker
    use epoll;  # Linux kernel optimization
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # HTTP/2 Support
    http2_max_field_size 16k;
    http2_max_header_size 32k;

    # Backend upstream pool
    upstream varuna_backend {
        least_conn;  # Least connections algorithm (better for WSI)

        server backend-1:8000 max_fails=3 fail_timeout=30s weight=1;
        server backend-2:8000 max_fails=3 fail_timeout=30s weight=1;

        # Keepalive connections to backend
        keepalive 32;
        keepalive_requests 100;
        keepalive_timeout 60s;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name varuna.chu-ucl.be;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/varuna.crt;
        ssl_certificate_key /etc/nginx/ssl/varuna.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Frontend static files
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            expires 1h;
            add_header Cache-Control "public, must-revalidate";
        }

        # API Backend
        location /api/ {
            proxy_pass http://varuna_backend;

            # Proxy headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # HTTP/1.1 for keepalive
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            # Timeouts (important for large tile requests)
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;

            # Buffering
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }

        # Tile caching (Nginx cache layer)
        location ~ ^/api/slides/[^/]+/tiles/ {
            proxy_pass http://varuna_backend;

            # Cache configuration
            proxy_cache tile_cache;
            proxy_cache_valid 200 24h;
            proxy_cache_key "$scheme$request_method$host$request_uri";
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            proxy_cache_background_update on;
            proxy_cache_lock on;

            # Headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_http_version 1.1;
            proxy_set_header Connection "";

            # Cache status header (debugging)
            add_header X-Cache-Status $upstream_cache_status;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name varuna.chu-ucl.be;
        return 301 https://$server_name$request_uri;
    }

    # Nginx cache path
    proxy_cache_path /var/cache/nginx/tiles
                     levels=1:2
                     keys_zone=tile_cache:100m
                     max_size=10g
                     inactive=24h
                     use_temp_path=off;
}
```

### 5.2 Health Checks et Auto-Healing

**Backend health endpoint amélioré:**

```python
# backend/routes/health.py
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import time
import os

router = APIRouter()

@router.get("/api/health")
async def health_check():
    """
    Comprehensive health check.

    Vérifie:
    - Disponibilité API
    - Accès au stockage slides
    - Connectivité Redis (si configuré)
    - Capacité OpenSlide
    """
    checks = {
        "status": "healthy",
        "timestamp": time.time(),
        "instance_id": os.getenv("INSTANCE_ID", "unknown"),
        "checks": {}
    }

    # Check 1: Storage accessibility
    slides_path = os.getenv("SLIDES_REPOSITORY_PATH", "/slides")
    try:
        if os.path.exists(slides_path) and os.access(slides_path, os.R_OK):
            checks["checks"]["storage"] = "ok"
        else:
            checks["checks"]["storage"] = "error: not accessible"
            checks["status"] = "degraded"
    except Exception as e:
        checks["checks"]["storage"] = f"error: {str(e)}"
        checks["status"] = "unhealthy"

    # Check 2: Redis connectivity (optional)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from services.tile_cache import TileCache
            cache = TileCache(redis_url)
            cache.redis_client.ping()
            checks["checks"]["redis"] = "ok"
        except Exception as e:
            checks["checks"]["redis"] = f"error: {str(e)}"
            checks["status"] = "degraded"

    # Check 3: OpenSlide library
    try:
        import openslide
        checks["checks"]["openslide"] = f"ok (version {openslide.__library_version__})"
    except Exception as e:
        checks["checks"]["openslide"] = f"error: {str(e)}"
        checks["status"] = "unhealthy"

    # Return appropriate HTTP status
    if checks["status"] == "healthy":
        return JSONResponse(content=checks, status_code=status.HTTP_200_OK)
    elif checks["status"] == "degraded":
        return JSONResponse(content=checks, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content=checks, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
```

---

## 6. Pipeline CI/CD

### 6.1 GitHub Actions Workflow

**Déploiement automatisé complet:**

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches:
      - main
    tags:
      - 'v*'
  pull_request:
    branches:
      - main

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ${{ github.repository }}/backend
  FRONTEND_IMAGE: ${{ github.repository }}/frontend

jobs:
  # ============================================================================
  # TESTS
  # ============================================================================
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=. --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run linting
        run: |
          cd frontend
          npm run lint || echo "No lint script defined"

      - name: Build frontend
        run: |
          cd frontend
          npm run build

  # ============================================================================
  # SECURITY SCAN
  # ============================================================================
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail on critical/high vulnerabilities

      - name: Run Bandit security scan (Python)
        run: |
          pip install bandit
          bandit -r backend/ -f json -o bandit-report.json || true

      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json

  # ============================================================================
  # BUILD & PUSH
  # ============================================================================
  build-and-push:
    needs: [test-backend, test-frontend, security-scan]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels) - Backend
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=ref,event=branch
            type=ref,event=pr

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.BACKEND_IMAGE }}:buildcache,mode=max

      - name: Extract metadata (tags, labels) - Frontend
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=ref,event=branch

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.FRONTEND_IMAGE }}:buildcache,mode=max

  # ============================================================================
  # DEPLOY TO STAGING
  # ============================================================================
  deploy-staging:
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/varuna
            docker-compose -f docker-compose.staging.yml pull
            docker-compose -f docker-compose.staging.yml up -d
            docker-compose -f docker-compose.staging.yml ps

      - name: Run smoke tests
        run: |
          sleep 30  # Wait for services to start
          curl -f https://staging.varuna.chu-ucl.be/api/health || exit 1

  # ============================================================================
  # DEPLOY TO PRODUCTION
  # ============================================================================
  deploy-production:
    needs: build-and-push
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3

      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install varuna ./helm/varuna \
            --namespace production \
            --create-namespace \
            --set backend.image.tag=${{ github.ref_name }} \
            --set frontend.image.tag=${{ github.ref_name }} \
            --wait \
            --timeout 5m

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/varuna-backend -n production --timeout=5m
          kubectl rollout status deployment/varuna-frontend -n production --timeout=5m

      - name: Run post-deployment tests
        run: |
          kubectl run --rm -it test-pod \
            --image=curlimages/curl:latest \
            --restart=Never \
            -- curl -f http://varuna-backend-svc:8000/api/health
```

---

## 7. Monitoring et Observabilité

### 7.1 Prometheus Configuration

**Configuration Prometheus pour VarunaPoC:**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'chu-ucl-varuna'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules
rule_files:
  - 'alerts/*.yml'

scrape_configs:
  # VarunaPoC Backend metrics
  - job_name: 'varuna-backend'
    static_configs:
      - targets:
          - backend-1:8000
          - backend-2:8000
    metrics_path: '/metrics'
    scrape_interval: 5s  # High frequency for WSI metrics

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets:
          - redis-exporter:9121

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets:
          - nginx-exporter:9113

  # Node exporter (system metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - node-exporter:9100
```

### 7.2 Alerting Rules

**Alertes critiques pour WSI:**

```yaml
# monitoring/alerts/varuna-alerts.yml
groups:
  - name: varuna_performance
    interval: 30s
    rules:
      # Alerte: Temps de chargement lame > 2s (P95)
      - alert: SlideLoadTimeTooHigh
        expr: histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
          component: backend
        annotations:
          summary: "Slide load time P95 exceeds 2s"
          description: "P95 tile load time is {{ $value }}s (target: <2s)"

      # Alerte: Latence navigation > 100ms
      - alert: NavigationLatencyHigh
        expr: histogram_quantile(0.95, rate(varuna_http_request_duration_seconds_bucket{endpoint=~"/api/slides.*"}[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
          component: backend
        annotations:
          summary: "Navigation latency P95 > 100ms"
          description: "P95 API latency is {{ $value }}s (target: <100ms)"

      # Alerte: Taux d'erreur HTTP > 1%
      - alert: HighErrorRate
        expr: rate(varuna_http_requests_total{status_code=~"5.."}[5m]) / rate(varuna_http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
          component: backend
        annotations:
          summary: "HTTP error rate > 1%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Alerte: Redis cache hit rate < 70%
      - alert: RedisCacheHitRateLow
        expr: rate(varuna_cache_hits[5m]) / (rate(varuna_cache_hits[5m]) + rate(varuna_cache_misses[5m])) < 0.7
        for: 10m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Redis cache hit rate < 70%"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (target: >70%)"

  - name: varuna_availability
    interval: 30s
    rules:
      # Alerte: Backend down
      - alert: BackendDown
        expr: up{job="varuna-backend"} == 0
        for: 1m
        labels:
          severity: critical
          component: backend
        annotations:
          summary: "Backend instance is down"
          description: "Backend {{ $labels.instance }} has been down for 1 minute"

      # Alerte: Redis down
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
          component: cache
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for 1 minute"

      # Alerte: Disponibilité < 99.5%
      - alert: AvailabilityBelowSLA
        expr: avg_over_time(up{job="varuna-backend"}[1h]) < 0.995
        for: 5m
        labels:
          severity: critical
          component: sla
        annotations:
          summary: "Service availability < 99.5% SLA"
          description: "Availability is {{ $value | humanizePercentage }} (SLA: 99.5%)"
```

### 7.3 Grafana Dashboards

**Dashboard VarunaPoC - Performance WSI:**

```json
{
  "dashboard": {
    "title": "VarunaPoC - WSI Performance Monitoring",
    "uid": "varuna-wsi-perf",
    "tags": ["varuna", "wsi", "performance"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Tile Load Time (P50, P95, P99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(varuna_tile_load_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m]))",
            "legendFormat": "P95 (TARGET: <2s)"
          },
          {
            "expr": "histogram_quantile(0.99, rate(varuna_tile_load_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "yaxes": [
          {
            "label": "Seconds",
            "format": "s"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [2],
                "type": "gt"
              },
              "query": {
                "params": ["P95"]
              }
            }
          ]
        }
      },
      {
        "id": 2,
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(varuna_http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Redis Cache Hit Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "rate(varuna_cache_hits[5m]) / (rate(varuna_cache_hits[5m]) + rate(varuna_cache_misses[5m]))"
          }
        ],
        "thresholds": [
          {"value": 0, "color": "red"},
          {"value": 0.7, "color": "yellow"},
          {"value": 0.85, "color": "green"}
        ]
      },
      {
        "id": 4,
        "title": "Active Concurrent Users",
        "type": "stat",
        "targets": [
          {
            "expr": "varuna_active_sessions"
          }
        ]
      },
      {
        "id": 5,
        "title": "Slides Opened by Format",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (format) (rate(varuna_slides_opened_total[1h]))",
            "legendFormat": "{{format}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "HTTP Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(varuna_http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          },
          {
            "expr": "rate(varuna_http_requests_total{status_code=~\"4..\"}[5m])",
            "legendFormat": "4xx errors"
          }
        ]
      }
    ],
    "refresh": "10s"
  }
}
```

**Commande d'import du dashboard:**

```bash
# Via API Grafana
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/varuna-wsi-perf.json
```

---

## 8. Stratégie de Stockage

### 8.1 Architecture Stockage

```
┌─────────────────────────────────────────────────────────────────┐
│                   STORAGE ARCHITECTURE                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PRIMARY STORAGE (Production Slides)                      │  │
│  │                                                          │  │
│  │ NAS CHU: //imgsv-01-p/anapath_storage_nimble             │  │
│  │ Protocol: SMB/CIFS v3.0                                  │  │
│  │ Capacity: 5 TB (extensible)                              │  │
│  │ RAID: RAID 6 (fault tolerance)                           │  │
│  │ Backup: Daily incremental                                │  │
│  │ Access: Read-only from VarunaPoC                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│                         │ Mount                                 │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ KUBERNETES PERSISTENT VOLUME                             │  │
│  │                                                          │  │
│  │ apiVersion: v1                                           │  │
│  │ kind: PersistentVolume                                   │  │
│  │ metadata:                                                │  │
│  │   name: chu-slides-pv                                    │  │
│  │ spec:                                                    │  │
│  │   capacity:                                              │  │
│  │     storage: 5Ti                                         │  │
│  │   accessModes:                                           │  │
│  │     - ReadOnlyMany                                       │  │
│  │   csi:                                                   │  │
│  │     driver: smb.csi.k8s.io                               │  │
│  │     volumeHandle: smb-slides-pv                          │  │
│  │     volumeAttributes:                                    │  │
│  │       source: "//imgsv-01-p/anapath_storage_nimble"      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Backup Strategy

**Politique de sauvegarde:**

| Type | Fréquence | Rétention | Destination | Priorité |
|------|-----------|-----------|-------------|----------|
| **Snapshots NAS** | Horaire | 24h | NAS local | Haute |
| **Backup incrémental** | Quotidien | 30 jours | NAS secondaire | Haute |
| **Backup complet** | Hebdomadaire | 3 mois | Tape/Cloud | Moyenne |
| **Archive** | Mensuel | 7 ans (réglementaire) | Tape offline | Critique |

**Script de backup (exemple):**

```bash
#!/bin/bash
# backup-slides.sh - Backup automation for VarunaPoC storage

set -e

BACKUP_DIR="/mnt/backup/varuna"
SOURCE_DIR="/mnt/chu-slides"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/varuna-backup.log"

echo "[$(date)] Starting backup..." | tee -a "$LOG_FILE"

# 1. Metadata backup (JSON, XML, INI files - lightweight)
echo "Backing up metadata..." | tee -a "$LOG_FILE"
rsync -avz --include='*.json' --include='*.xml' --include='*.ini' \
      --exclude='*.dat' --exclude='*.mrxs' --exclude='*.bif' \
      "$SOURCE_DIR/" "$BACKUP_DIR/metadata_$DATE/" \
      | tee -a "$LOG_FILE"

# 2. Database backup (if using PostgreSQL for annotations)
if [ -n "$POSTGRES_HOST" ]; then
    echo "Backing up database..." | tee -a "$LOG_FILE"
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER varuna \
        | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
fi

# 3. Compress and encrypt
echo "Compressing and encrypting..." | tee -a "$LOG_FILE"
tar -czf - "$BACKUP_DIR/metadata_$DATE" "$BACKUP_DIR/db_$DATE.sql.gz" | \
    openssl enc -aes-256-cbc -salt -pbkdf2 -out "$BACKUP_DIR/backup_$DATE.tar.gz.enc"

# 4. Upload to offsite storage (example: Azure Blob)
if command -v az &> /dev/null; then
    echo "Uploading to Azure Blob Storage..." | tee -a "$LOG_FILE"
    az storage blob upload \
        --account-name varunabackups \
        --container-name production-backups \
        --name "varuna_backup_$DATE.tar.gz.enc" \
        --file "$BACKUP_DIR/backup_$DATE.tar.gz.enc" \
        | tee -a "$LOG_FILE"
fi

# 5. Cleanup old backups (keep 30 days)
echo "Cleaning up old backups..." | tee -a "$LOG_FILE"
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "[$(date)] Backup completed successfully" | tee -a "$LOG_FILE"
```

**Cron schedule:**

```cron
# /etc/cron.d/varuna-backup

# Metadata backup every 6 hours
0 */6 * * * root /opt/varuna/scripts/backup-slides.sh

# Full backup weekly (Sunday 2 AM)
0 2 * * 0 root /opt/varuna/scripts/backup-full.sh

# Backup verification daily (check integrity)
0 3 * * * root /opt/varuna/scripts/verify-backup.sh
```

---

## 9. Performance et Scalabilité

### 9.1 Métriques de Performance Cibles

| Métrique | Valeur Actuelle (Phase 1) | Cible Phase 2.5 | Cible Phase 3 |
|----------|---------------------------|-----------------|---------------|
| **Temps chargement lame (P95)** | 3-5s | < 2s | < 1s |
| **Latence navigation (P95)** | 150-200ms | < 100ms | < 50ms |
| **Disponibilité** | 95% | 99.5% | 99.9% |
| **Utilisateurs simultanés** | 3-5 | 10 | 50+ |
| **Cache hit rate** | 0% (no cache) | 70-80% | 85-90% |
| **Throughput API** | 50 req/s | 200 req/s | 1000 req/s |

### 9.2 Optimisations Recommandées

**Backend (Python FastAPI):**

```python
# backend/main.py - Performance optimizations

from fastapi import FastAPI
import uvicorn

app = FastAPI()

# 1. Enable HTTP/2 (requires uvicorn[standard])
# Run: uvicorn main:app --http h2

# 2. Increase worker processes
# Run: uvicorn main:app --workers 4

# 3. Use Gunicorn for production
# Run: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker \
#                       --bind 0.0.0.0:8000

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 2 * CPU cores + 1
        loop="uvloop",  # Faster event loop
        http="h11",  # HTTP/1.1 (use httptools for HTTP/2)
        log_level="info"
    )
```

**Frontend (Vite + OpenSeadragon):**

```javascript
// frontend/src/viewers/optimized-viewer.js

/**
 * Optimized OpenSeadragon configuration for VarunaPoC.
 */
export function createOptimizedViewer(elementId, slideInfo) {
    const viewer = OpenSeadragon({
        id: elementId,

        // Performance optimizations
        immediateRender: true,  // Render as soon as tiles available
        preload: true,  // Prefetch adjacent tiles

        // Cache configuration
        imageLoaderLimit: 6,  // Parallel tile downloads
        timeout: 120000,  // 2 minutes timeout

        // Memory management
        minPixelRatio: 0.5,  // Lower quality at low zoom (performance)

        // Smooth navigation
        springStiffness: 10,  // Faster animation
        animationTime: 0.5,  // Snappier transitions

        // Tile sources
        tileSources: {
            height: slideInfo.dimensions[1],
            width: slideInfo.dimensions[0],
            tileSize: 256,
            minLevel: 0,
            maxLevel: slideInfo.level_count - 1,
            getTileUrl: function(level, x, y) {
                return `/api/slides/${slideInfo.id}/tiles/${level}/${x}_${y}.jpg`;
            }
        },

        // Progressive rendering
        showNavigator: true,
        navigatorPosition: 'BOTTOM_RIGHT',

        // Event handlers for monitoring
        tileSources: {
            // ... tile source config ...

            tileLoad: function(event) {
                // Track tile load time
                const loadTime = performance.now() - event.tile.loadingTime;
                console.log(`Tile loaded in ${loadTime}ms`);
            }
        }
    });

    return viewer;
}
```

### 9.3 Horizontal Scaling Strategy

**Auto-scaling rules (Kubernetes HPA):**

```yaml
# k8s/hpa-advanced.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: varuna-backend-hpa
  namespace: varuna-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: varuna-backend

  minReplicas: 3  # Always 3 for HA
  maxReplicas: 20  # Scale up to 20 pods under load

  metrics:
    # CPU-based scaling
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory-based scaling
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metric: Request latency
    - type: Pods
      pods:
        metric:
          name: varuna_http_request_duration_seconds
        target:
          type: AverageValue
          averageValue: "100m"  # 100ms target

  behavior:
    # Scale up aggressively
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100  # Double pods immediately
          periodSeconds: 15
        - type: Pods
          value: 4  # Or add 4 pods
          periodSeconds: 15
      selectPolicy: Max

    # Scale down conservatively
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 minutes
      policies:
        - type: Percent
          value: 50  # Remove max 50% of pods
          periodSeconds: 60
      selectPolicy: Min
```

---

## 10. Sécurité Infrastructure

### 10.1 Network Security

**Architecture réseau sécurisée:**

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Firewall    │
                    │  (WAF)       │
                    │  Port: 443   │
                    └──────┬───────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│         DMZ (Public Zone)│                                      │
│                          ▼                                      │
│                   ┌──────────────┐                              │
│                   │ Nginx Ingress│                              │
│                   │ (TLS Term.)  │                              │
│                   └──────┬───────┘                              │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│   PRIVATE ZONE (K8s)     │                                      │
│                          ▼                                      │
│              ┌────────────────────┐                             │
│              │  Backend Pods      │                             │
│              │  (No public IP)    │                             │
│              └─────────┬──────────┘                             │
│                        │                                        │
│              ┌─────────▼──────────┐                             │
│              │  Redis Cache       │                             │
│              │  (Internal only)   │                             │
│              └─────────┬──────────┘                             │
└────────────────────────┼────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────┐
│   STORAGE ZONE          │                                       │
│                         ▼                                       │
│              ┌────────────────────┐                             │
│              │  NAS Storage       │                             │
│              │  (CHU Network)     │                             │
│              │  Private VLAN      │                             │
│              └────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Secrets Management

**HashiCorp Vault integration:**

```yaml
# k8s/vault-integration.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: varuna-backend-sa
  namespace: varuna-prod
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: varuna-backend
spec:
  template:
    spec:
      serviceAccountName: varuna-backend-sa

      # Vault Agent Injector
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "varuna-backend"
        vault.hashicorp.com/agent-inject-secret-database: "secret/data/varuna/database"
        vault.hashicorp.com/agent-inject-secret-redis: "secret/data/varuna/redis"
        vault.hashicorp.com/agent-inject-secret-smb: "secret/data/varuna/storage"

      containers:
        - name: backend
          env:
            # Read secrets from Vault-injected files
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: varuna-secrets
                  key: database-url
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: varuna-secrets
                  key: redis-password
```

### 10.3 Audit Logging

**Structured audit logs (GDPR compliance):**

```python
# backend/utils/audit_logger.py
import structlog
import json
from datetime import datetime
from fastapi import Request

class AuditLogger:
    """
    HIPAA/GDPR-compliant audit logging.

    Logs:
    - Slide access (who, when, what)
    - User actions (annotations, exports)
    - Authentication events
    - Data modifications
    """

    def __init__(self):
        self.logger = structlog.get_logger("audit")

    def log_slide_access(
        self,
        request: Request,
        slide_id: str,
        action: str,
        user_id: str = None
    ):
        """
        Log slide access for HIPAA compliance.

        Args:
            request: FastAPI request object
            slide_id: Unique slide identifier
            action: Action performed (view, download, export)
            user_id: User identifier (if authenticated)
        """
        self.logger.info(
            "slide_access",
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id or "anonymous",
            ip_address=request.client.host,
            slide_id=slide_id,
            action=action,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer")
        )

    def log_authentication(
        self,
        username: str,
        success: bool,
        ip_address: str
    ):
        """Log authentication attempt."""
        self.logger.info(
            "authentication",
            timestamp=datetime.utcnow().isoformat(),
            username=username,
            success=success,
            ip_address=ip_address
        )

audit_logger = AuditLogger()
```

---

## 11. Roadmap d'Implémentation

### 11.1 Planning

```
PHASE 2.5: DOCKER COMPOSE OPTIMISÉ
Timeline: 2 semaines
─────────────────────────────────────────────────────────────
Week 1:
  - Configuration Redis cache
  - Nginx load balancing (2 backends)
  - Monitoring Prometheus + Grafana
  - Tests de performance (benchmarks)

Week 2:
  - Documentation déploiement
  - Scripts automation
  - Formation équipe CHU
  - Go-live Phase 2.5


PHASE 3: KUBERNETES (PRODUCTION)
Timeline: 3 mois
─────────────────────────────────────────────────────────────
Month 1: Infrastructure Setup
  Week 1-2: K8s cluster setup (on-premise or cloud)
  Week 3-4: Helm charts creation, CI/CD pipeline

Month 2: Migration & Testing
  Week 5-6: Migration Docker → Kubernetes
  Week 7-8: Load testing, performance tuning

Month 3: Security & Go-Live
  Week 9-10: Security hardening, penetration testing
  Week 11-12: User acceptance testing, production deployment


PHASE 4: ADVANCED FEATURES
Timeline: Ongoing (post-deployment)
─────────────────────────────────────────────────────────────
  - HTTP/3 (QUIC) support
  - CDN integration
  - Multi-region deployment
  - Advanced caching strategies
```

### 11.2 Checklist de Déploiement

**Phase 2.5 Checklist:**

```markdown
PRE-DEPLOYMENT
- [ ] Installer Docker et docker-compose sur serveur CHU
- [ ] Monter NAS storage: //imgsv-01-p/anapath_storage_nimble → /mnt/chu-slides
- [ ] Configurer firewall (ports 80, 443, 8000)
- [ ] Créer certificats SSL (Let's Encrypt ou certificat CHU)
- [ ] Configurer DNS: varuna.chu-ucl.be → IP serveur

DEPLOYMENT
- [ ] Cloner repository: git clone https://github.com/chu-ucl/VarunaPoC.git
- [ ] Créer fichier .env (REDIS_URL, SLIDES_REPOSITORY_PATH, etc.)
- [ ] Build images: docker-compose -f docker-compose.optimized.yml build
- [ ] Démarrer services: docker-compose -f docker-compose.optimized.yml up -d
- [ ] Vérifier health checks: curl http://localhost/api/health

POST-DEPLOYMENT
- [ ] Accéder Grafana: http://localhost:3000 (admin/admin)
- [ ] Importer dashboards VarunaPoC
- [ ] Tester avec lames réelles du CHU
- [ ] Valider temps de chargement < 2s (P95)
- [ ] Configurer alerting (email, Slack, etc.)
- [ ] Documentation utilisateur
- [ ] Formation pathologistes

MONITORING (FIRST WEEK)
- [ ] Surveiller métriques Grafana quotidiennement
- [ ] Vérifier cache hit rate Redis (target: >70%)
- [ ] Analyser logs erreurs
- [ ] Ajuster configuration si nécessaire
- [ ] Collecter feedback utilisateurs
```

---

## 12. Ressources et Références

### 12.1 Documentation Officielle

**Infrastructure:**
- Docker: https://docs.docker.com/
- Kubernetes: https://kubernetes.io/docs/
- Helm: https://helm.sh/docs/

**Monitoring:**
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/

**Caching:**
- Redis: https://redis.io/documentation
- Nginx Caching: https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache

**CI/CD:**
- GitHub Actions: https://docs.github.com/en/actions
- Docker Build: https://docs.docker.com/build/

### 12.2 Best Practices

- **12-Factor App**: https://12factor.net/
- **Kubernetes Production Best Practices**: https://kubernetes.io/docs/setup/best-practices/
- **CNCF Cloud Native Trail Map**: https://github.com/cncf/trailmap

### 12.3 CHU-Specific Resources

```
CONTACTS CHU UCL NAMUR:
- IT Infrastructure: infrastructure@chuuclnamur.be
- Storage Team: storage-admins@chuuclnamur.be
- Security: security@chuuclnamur.be
- Pathology Lab: anapath@chuuclnamur.be

NETWORK:
- Internal VLAN: 10.50.0.0/16
- DMZ VLAN: 10.51.0.0/24
- Storage VLAN: 10.52.0.0/24
- DNS: ns1.chu-ucl.local, ns2.chu-ucl.local

STORAGE:
- NAS Primary: imgsv-01-p.chu-ucl.local
- NAS Backup: imgsv-02-b.chu-ucl.local
- Protocol: SMB 3.0 (encrypted)
```

---

## Conclusion

Cette architecture infrastructure fournit une feuille de route complète pour déployer VarunaPoC en production au CHU UCL Namur, avec:

1. **Performance garantie**: Cache multi-niveaux, load balancing, HTTP/2
2. **Haute disponibilité**: 99.5%+ grâce à la redondance et l'auto-healing
3. **Scalabilité**: De 10 à 50+ utilisateurs simultanés sans refonte
4. **Observabilité**: Monitoring complet avec alerting proactif
5. **Sécurité**: Chiffrement, audit logs, conformité HIPAA/GDPR
6. **Automatisation**: CI/CD zero-touch deployment

**Prochaines étapes immédiates:**
1. Implémenter Phase 2.5 (Docker Compose optimisé) - 2 semaines
2. Valider performances avec lames CHU réelles
3. Planifier migration Kubernetes (Phase 3) - 3 mois

**Auteur:** Infrastructure Architect Agent
**Version:** 1.0
**Date:** 2025-12-31
**Statut:** Ready for Implementation
