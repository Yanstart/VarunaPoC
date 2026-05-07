# cache

## But
Systemes de cache pour deux domaines distincts:
- **ML** (embeddings, heatmaps): cache memoire L1 + disque L2 (numpy).
- **Tiles** (tuiles WSI): cache memoire L1 + Redis L2 (TileCache Protocol).

## Pourquoi
- ML: les calculs sont couteux ; le cache evite les recalculs et accelere les requetes suivantes.
- Tiles: l'extraction OpenSlide n'est pas thread-safe et les memes tuiles sont demandees lors du panning/zoom. Le cache distribue Redis permet le scaling horizontal (plusieurs instances backend partagent le meme cache).

## Comment
- `MemoryCache` (cachetools TTL) sert de L1 pour ML *et* tiles ; meme classe, deux instances.
- `DiskCache` est specifique aux ML embeddings (.npy sur disque, persistance longue).
- `RedisCache` est un wrapper async sur redis.asyncio avec circuit-breaker et stats.
- `TwoLevelTileCache` orchestre L1 (memoire) + L2 (Redis) pour les tiles ; degrade gracieusement en L1-only si Redis est down.

## Structure
- `__init__.py` -- Package cache (vide).
- `memory_cache.py` -- Cache L1 en memoire avec TTL (cachetools), stats hits/misses.
- `disk_cache.py` -- Cache L2 ML sur disque (.npy), organise par slide_id et modele, ecriture atomique.
- `redis_cache.py` -- Wrapper async Redis (L2 tiles, future utilisation distributed). Circuit-breaker pour eviter de bloquer si Redis down.
- `two_level_tile_cache.py` -- TileCache Protocol implementer composant MemoryCache (L1) + RedisCache (L2). Cle: `{slide_id}:{level}:{col}_{row}:{tile_size}`.

## Configuration
Variables d'environnement (voir `backend/.env.example`):
- `TILE_CACHE_L2_ENABLED` (default `true`) -- desactiver pour fallback L1-only.
- `TILE_CACHE_L2_TTL_SECONDS` (default `3600`) -- TTL des tuiles dans Redis.
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`, `REDIS_CONNECT_TIMEOUT`.

## Conteneur dev
Le serveur Redis dev tourne via `docker compose --profile cache` (inclus aussi dans `--profile dev`) sur le port hote `6380` (production: `6379`).
```bash
docker compose --profile dev up -d redis
```
