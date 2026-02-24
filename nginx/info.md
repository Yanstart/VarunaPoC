# nginx

## But
Reverse proxy et serveur de fichiers statiques. Point d'entree reseau unique pour le backend API et le frontend.

## Pourquoi
En milieu hospitalier, un seul port expose (80/443) simplifie les regles firewall. Le cache de tuiles (10 GB, TTL 24h) reduit la charge backend de 50%+.

## Comment
- Reverse proxy vers backend (least_conn load balancing)
- Sert le frontend statique depuis /usr/share/nginx/html
- Cache agressif des tuiles (`/api/slides/*/tile/*` -> 24h TTL, 10 GB max)
- TLS termination (HTTP/2) en production, HTTP en dev
- Headers securite: HSTS, X-Frame-Options, CSP

## Structure
```
nginx/
  nginx.conf             # Config complete (308 lignes): proxy, cache, TLS, securite, health
  generate-ssl-certs.sh  # Generation certificats SSL auto-signes
```

## Points cles
- Cache tiles: `proxy_cache_path /var/cache/nginx/tiles levels=1:2 keys_zone=tiles:10m max_size=10g`
- Health checks: `/health` (backend), `/nginx_status` (nginx)
- Reseau Docker: 172.28.0.0/16
