# frontend — SPA Vite

## Rôle

Single-page application Vanilla JS + Vite + OpenSeadragon. Servie en
production sous forme de fichiers statiques par un nginx interne au
conteneur, accessible via le `nginx` reverse proxy.

En dev, on lance `npm run dev` (Vite dev server hot-reload sur :5173) et
le backend sur :8000 — pas besoin du conteneur frontend.

## Conteneur

| | |
|---|---|
| Image | `${FRONTEND_IMAGE}:${FRONTEND_IMAGE_TAG}` (default `ghcr.io/yanstart/varunapoc/frontend:main`) |
| Profils | `prod` |
| Port interne | `80` |
| Port hôte | aucun (via reverse proxy) |
| Healthcheck | `wget /` toutes les 10 s |

## Variables d'env

| Variable              | Défaut                              | Rôle                  |
|-----------------------|-------------------------------------|-----------------------|
| `FRONTEND_IMAGE`      | `ghcr.io/yanstart/varunapoc/frontend` | Registre/image      |
| `FRONTEND_IMAGE_TAG`  | `main`                              | Tag (release prod)    |

L'URL de l'API backend est résolue côté client via la requête au même
host (proxy nginx) ; pas de variable build-time exposée.

## Build local

```bash
cd frontend
npm ci
npm run build         # → dist/
npm run preview       # serveur statique pour valider le build
```

Pour rebuild l'image conteneur :

```bash
docker build -t ghcr.io/yanstart/varunapoc/frontend:dev frontend/
```

## Désactiver

Pas de flag : on lance simplement sans `--profile prod`. En dev, l'usage
`npm run dev` remplace le conteneur.

## Dépannage

| Symptôme                                  | Cause probable                                   |
|-------------------------------------------|--------------------------------------------------|
| Page blanche après login                  | CORS / `OIDC_REDIRECT_URI` mal configuré         |
| WebSocket workflow events se déconnecte    | nginx ne propage pas `Upgrade: websocket`        |
| Tuiles 401                                | Token JWT expiré côté frontend ; refresh         |
| Tuiles 502                                | Backend down ou healthcheck nginx → backend KO   |

## Liens

- `frontend/Dockerfile` — image multistage
- `frontend/vite.config.js`
- `frontend/src/main.js` — bootstrap
