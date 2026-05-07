# nginx — Reverse proxy + TLS termination

## Rôle

- Termine TLS (cert + clé montés depuis l'hôte)
- Route `/` → `frontend`, `/api/*` → `backend`, `/api/v1/ws/*` → `backend` (WS upgrade)
- Cache local des tuiles (volume `varuna-nginx-cache`, ~10 Go)
- Expose `/health` pour les load balancers externes
- Expose `/nginx_status` pour `nginx-exporter` (Prometheus)

## Conteneur

| | |
|---|---|
| Image | `nginx:1.25-alpine` |
| Profils | `prod` |
| Ports hôte | `80` (HTTP, redirect vers HTTPS), `443` (HTTPS) |
| Volumes | `./nginx/nginx.conf`, `./nginx/ssl/`, `varuna-nginx-cache` |
| Entrypoint | `/docker-entrypoint-varuna.sh` (substitue `${NGINX_SERVER_NAME}` dans le template) |

## Variables d'env

| Variable             | Défaut                          | Rôle                                |
|----------------------|---------------------------------|-------------------------------------|
| `NGINX_SERVER_NAME`  | `localhost`                     | FQDN public (`varuna.hospital.example` en prod) |
| `NGINX_SSL_CERT`     | `/etc/nginx/ssl/varuna.crt`     | Cert TLS                            |
| `NGINX_SSL_KEY`      | `/etc/nginx/ssl/varuna.key`     | Clé TLS                             |
| `HTTP_PORT`          | `80`                            | Port HTTP                           |
| `HTTPS_PORT`         | `443`                           | Port HTTPS                          |

## Configuration

`nginx/nginx.conf` est un **template** : `${NGINX_SERVER_NAME}` est
substitué au démarrage par `nginx/docker-entrypoint.sh`. Toute modif
nécessite `docker compose restart nginx`.

Points de configuration usuels :
- Taille max requête : `client_max_body_size`
- Timeout proxy : `proxy_read_timeout` (important pour grosses tuiles WSI)
- WebSocket : `proxy_set_header Upgrade $http_upgrade;` et
  `proxy_set_header Connection "upgrade";` sur le bloc `/api/v1/ws/`
- Cache tuiles : `proxy_cache_path` + `proxy_cache_valid 200 24h`

## Certificats TLS

### Dev / test (auto-signé)

```bash
./nginx/generate-ssl-certs.sh   # génère varuna.crt + varuna.key dans nginx/ssl/
```

### Prod hospital

Placer cert + clé fournis par l'IT (`varuna.hospital.example.crt/key`)
dans `nginx/ssl/`, ou configurer le path dans `.env` :

```env
NGINX_SSL_CERT=/etc/letsencrypt/live/varuna.example/fullchain.pem
NGINX_SSL_KEY=/etc/letsencrypt/live/varuna.example/privkey.pem
```

Et monter le volume correspondant dans le compose (override file).

## Commandes admin

```bash
# Recharger conf (pas de downtime)
docker compose exec nginx nginx -s reload

# Test conf avant reload
docker compose exec nginx nginx -t

# Logs accès / erreurs
docker compose logs nginx | grep "GET /api/v1"

# Vider le cache tuiles
docker compose exec nginx find /var/cache/nginx -type f -delete
docker compose exec nginx nginx -s reload
```

## Métriques

- `/nginx_status` exposé pour `nginx-exporter` (port interne 9113)
- Métriques Prometheus : `nginx_connections_*`, `nginx_http_requests_total`
- Dashboard Grafana : `monitoring/grafana/dashboards/nginx.json`

## Désactiver

Pas de flag dédié — nginx fait partie de `prod`. Pour le retirer (par ex.
si on met devant un Traefik ou un IaaS load-balancer), lancer sans
`--profile prod` et déployer backend + frontend séparément derrière
votre proxy.

## Liens

- `nginx/nginx.conf` — template
- `nginx/docker-entrypoint.sh` — substitution env
- [docs/Deployment/NETWORK_SCENARIOS.md](../../Deployment/NETWORK_SCENARIOS.md)
