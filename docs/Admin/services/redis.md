# redis — TileCache L2

## Rôle

Cache distribué L2 pour les tuiles WSI. Le backend a un `TwoLevelTileCache`
qui combine :
- **L1** : cache mémoire `cachetools` (in-process, par worker uvicorn)
- **L2** : Redis (partagé entre tous les workers / réplicats backend)

Sans Redis, le backend dégrade gracieusement vers L1 seul. Le cache n'est
jamais bloquant : si Redis tombe, le backend log un warning et continue.

## Conteneur

| | |
|---|---|
| Image | `redis:7-alpine` |
| Profils | `cache`, `dev`, `prod` |
| Port hôte | `6380` (dev) / `6379` (prod), via `REDIS_HOST_PORT` |
| Port interne | `6379` |
| Volume | `varuna-redis-data` 🟢 reconstructible |
| Healthcheck | `redis-cli ping` toutes les 10 s |

## Variables d'env

| Variable             | Défaut  | Rôle                                                |
|----------------------|---------|-----------------------------------------------------|
| `REDIS_PASSWORD`     | (vide)  | Activer auth en prod ; vide = pas d'auth (dev)      |
| `REDIS_HOST_PORT`    | `6380`  | Port mappé sur l'hôte                               |
| `REDIS_MAX_MEMORY`   | `2gb`   | Limite mémoire ; politique `allkeys-lru`            |

Variables côté **backend** :

| Variable                  | Défaut  | Rôle                                                |
|---------------------------|---------|-----------------------------------------------------|
| `TILE_CACHE_L2_ENABLED`   | `true`  | Mettre `false` pour désactiver L2 sans toucher Docker |
| `TILE_CACHE_L2_TTL_SECONDS` | `3600` | TTL des entrées L2                                  |

## Diagnostic

```bash
# Latence
docker compose exec redis redis-cli --latency-history

# Top mémoire
docker compose exec redis redis-cli --bigkeys

# Clés actuelles (attention en prod, KEYS bloque)
docker compose exec redis redis-cli --scan --pattern 'tile:*' | head

# Hit rate
docker compose exec redis redis-cli INFO stats | grep keyspace
```

Le backend expose aussi des métriques :
`varuna_tile_cache_hits_total{level}` et
`varuna_tile_cache_misses_total{level}` sur `/metrics`.

## Désactiver complètement

```env
# .env
TILE_CACHE_L2_ENABLED=false
```

Lancer sans `--profile cache`. Le backend log au démarrage :
`TileCache L2 disabled, falling back to L1-only`.

## Hardening prod

- `REDIS_PASSWORD` obligatoire (32+ caractères)
- Ne PAS exposer 6379 en dehors du LAN admin
- `maxmemory-policy=allkeys-lru` (déjà configuré) pour qu'un OOM ne
  fasse pas tomber Redis
- Surveillance via `redis-exporter` (profil `monitoring`)

## Liens

- [Redis 7 docs](https://redis.io/docs/)
- [INFRASTRUCTURE.md](../INFRASTRUCTURE.md) — métriques exposées
