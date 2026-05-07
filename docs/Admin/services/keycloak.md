# keycloak + keycloak-db — OIDC Identity Provider

## Rôle

Fournit l'authentification OIDC PKCE pour le frontend et la validation JWT
pour le backend. En production hospitalière, on remplace souvent Keycloak
par l'IdP existant (Azure AD, ADFS) en pointant `OIDC_ISSUER_URL` ailleurs.

Couples avec `keycloak-db` (PostgreSQL dédié, distinct de `db`).

## Conteneurs

### keycloak

| | |
|---|---|
| Image | `quay.io/keycloak/keycloak:23.0` |
| Profils | `auth`, `dev`, `prod` |
| Port hôte | `8180`, via `KEYCLOAK_HOST_PORT` |
| Port interne | `8080` |
| Volume | (realm-export.json en read-only mount) |
| Healthcheck | TCP socket + `/health/ready` toutes les 15 s, démarrage ~90 s |

### keycloak-db

| | |
|---|---|
| Image | `postgres:16-alpine` |
| Profils | `auth`, `dev`, `prod` |
| Volume | `varuna-keycloak-db-data` 🔴 critique |
| Pas de port hôte exposé |

## Variables d'env

| Variable                         | Défaut                          | Rôle                                          |
|----------------------------------|---------------------------------|-----------------------------------------------|
| `KEYCLOAK_COMMAND`               | `start-dev --import-realm`      | `start --optimized --import-realm` en prod    |
| `KEYCLOAK_ADMIN`                 | `admin`                         | Compte admin master realm                     |
| `KEYCLOAK_ADMIN_PASSWORD`        | `admin`                         | Changer en prod (32+ chars)                   |
| `KEYCLOAK_DB_PASSWORD`           | `keycloak_dev`                  | Mot de passe `keycloak-db`                    |
| `KC_HOSTNAME`                    | `keycloak`                      | DNS public (`auth.example.org` en prod)       |
| `KC_HOSTNAME_STRICT_HTTPS`       | `false`                         | `true` derrière TLS                           |
| `KC_PROXY`                       | `edge`                          | nginx termine TLS, Keycloak parle HTTP en interne |
| `KEYCLOAK_HOST_PORT`             | `8180`                          | Port mappé hôte                               |

## Realm import

Au démarrage, Keycloak importe `backend/keycloak/realm-export.json`. Ce
realm définit :

- 4 rôles : `LECTURE_SEULE`, `INFIRMIER`, `MEDECIN`, `ADMIN_TECHNIQUE`
- 4 utilisateurs de test : `dr.martin`, `nurse.dupont`, `admin`, `viewer`
  (mot de passe `password` pour tous)
- Le client OIDC `varuna-frontend` (PKCE, public)

**Pour changer le realm en prod**, soit on édite `realm-export.json` avant
le premier `up`, soit on importe via UI/admin-CLI puis on l'exporte.

## Accès admin

UI master realm : http://localhost:8180/admin/master/console

Admin CLI :

```bash
docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 --realm master \
  --user "$KEYCLOAK_ADMIN" --password "$KEYCLOAK_ADMIN_PASSWORD"

docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh get users -r varuna
```

## Désactiver complètement

```env
# .env (côté backend)
AUTH_ENABLED=false
```

Et lancer sans `--profile auth`. Le backend renvoie alors `User(id="anonymous",
roles=["ADMIN_TECHNIQUE"])` à toute requête. **Mode dev/démo uniquement.**

## Hardening prod

- `KEYCLOAK_COMMAND=start --optimized --import-realm`
- `KC_HOSTNAME_STRICT_HTTPS=true`, derrière nginx avec cert valide
- `KEYCLOAK_ADMIN_PASSWORD` 32+ chars
- `KEYCLOAK_DB_PASSWORD` distinct et fort
- Sauvegarder `varuna-keycloak-db-data` (perte = tous les users perdus)
- Ports admin (8180) sur 127.0.0.1 ou VPN admin uniquement

## Troubleshooting

| Symptôme                                                | Cause                                        |
|---------------------------------------------------------|----------------------------------------------|
| `keycloak` reste `unhealthy` > 3 min                    | DB non healthy ; vérifier logs `keycloak-db` |
| Login frontend bloque sur `/auth/realms/varuna/...`     | `KC_HOSTNAME` pas accessible depuis le navigateur |
| `Invalid token: signature mismatch`                     | JWKS cache backend obsolète. Restart backend |
| `Audience mismatch`                                     | Vérifier `OIDC_AUDIENCE` côté backend         |

## Liens

- [Keycloak 23 docs](https://www.keycloak.org/docs/23/)
- `backend/keycloak/realm-export.json` — config realm
- [docs/Deployment/SECRETS_MANAGEMENT.md](../../Deployment/SECRETS_MANAGEMENT.md)
