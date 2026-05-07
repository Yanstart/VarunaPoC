# Profils Compose — quand activer quoi

Le `docker-compose.yml` unique utilise des **profils Docker Compose** pour
choisir quels services démarrent. Chaque profil correspond à un module
fonctionnel.

---

## Liste des profils

| Profil       | Services inclus                                                                              | Usage                                            |
|--------------|----------------------------------------------------------------------------------------------|--------------------------------------------------|
| `core`       | `db`                                                                                         | Toujours actif. Sans la DB, rien ne tourne.      |
| `cache`      | `redis`                                                                                      | TileCache L2. Désactivable (fallback L1 mémoire).|
| `auth`       | `keycloak`, `keycloak-db`                                                                    | OIDC. Désactivable si `AUTH_ENABLED=false`.      |
| `pacs`       | `orthanc`                                                                                    | Sandbox PACS DICOM (dev/test seulement).         |
| `fhir`       | `hapi-fhir`                                                                                  | Sandbox FHIR R4 (dev/test seulement).            |
| `monitoring` | `prometheus`, `grafana`, `alertmanager`, `redis-exporter`, `nginx-exporter`, `node-exporter`, `cadvisor` | Observabilité.                                   |
| `mlops`      | `mlflow`, `minio`, `minio-init`, `mlops-db`                                                  | Pipeline d'entraînement / tracking modèles.      |
| `dev`        | superset auto : `db` + `redis` + `keycloak` (+ DB) + `orthanc` + `hapi-fhir`                  | Stack complète développeur (sans backend/front). |
| `prod`       | superset auto : `db` + `migration` + `backend` + `frontend` + `nginx` + `redis` + `keycloak` (+ DB) + monitoring | Stack complète prod.                             |

Un service peut appartenir à **plusieurs profils** : `db` est dans
`core`, `dev` ET `prod` — il démarre quel que soit le profil choisi.

---

## Combinaisons usuelles

### Workstation développeur

```bash
docker compose --profile dev up -d
```
Lance : db + redis + keycloak + orthanc + hapi-fhir.
Backend et frontend tournent en local (`uvicorn`, `npm run dev`).

### Démo / présentation locale (full stack)

```bash
docker compose --profile prod up -d
```
Toute la stack applicative dans Docker. Pas de monitoring (allège la machine).

### Production hôpital

```bash
docker compose --profile prod --profile monitoring up -d
```
Stack applicative + observabilité complète. Sans `pacs`/`fhir` parce qu'on
pointe vers les serveurs hospitaliers via `PACS_HOST` et `FHIR_BASE_URL`.

### Production + entraînement ML

```bash
docker compose --profile prod --profile monitoring --profile mlops up -d
```
Pour les hôtes qui hébergent **aussi** la pipeline de re-training. À éviter
sur l'hôte applicatif principal (compétition pour la RAM/disque).

### CI runner — tests d'intégration

```bash
docker compose --profile core --profile cache --profile auth up -d
```
Juste de quoi faire passer les tests qui ont besoin de PostgreSQL, Redis et
Keycloak.

### Test PACS isolé

```bash
docker compose --profile core --profile pacs up -d
```
DB + Orthanc, rien d'autre. Pour itérer sur une intégration DICOM.

---

## Désactiver un profil sans le supprimer

Pour arrêter UN module sans toucher aux autres :

```bash
# Stop le module monitoring sur une stack prod en cours
docker compose --profile monitoring stop

# Le réactiver ensuite
docker compose --profile prod --profile monitoring up -d
```

Compose ne supprime pas les conteneurs arrêtés ; un futur `up` les
redémarre depuis l'état précédent (volumes intacts).

---

## Activation par variable d'env

Plutôt que de répéter les `--profile X` à chaque commande, mettre dans
le `.env` :

```env
COMPOSE_PROFILES=prod,monitoring,mlops
```

Puis :

```bash
docker compose up -d
```

C'est ce que font `.env.dev.example` et `.env.prod.example` une fois
décommentés.

---

## Désactiver l'auth complètement

Backend a un mode anonyme. Dans `.env` :

```env
AUTH_ENABLED=false
```

Et lancer SANS le profil `auth` :

```bash
docker compose --profile core --profile cache up -d
```

Dans ce mode, le backend renvoie `User(roles=["ADMIN_TECHNIQUE"])` à toute
requête. **À ne JAMAIS faire en production** — uniquement pour démo/dev.

---

## Désactiver le cache L2

Redis devient optionnel. Dans `.env` :

```env
TILE_CACHE_L2_ENABLED=false
```

Lancer sans le profil `cache`. Le backend log au démarrage `TileCache L2
disabled, falling back to L1-only` et continue avec juste son cache mémoire.

---

## Que faire en production hospitalière

| Situation                                                          | Profils à activer                  | Notes                                                                       |
|--------------------------------------------------------------------|------------------------------------|-----------------------------------------------------------------------------|
| Hôpital fournit son propre PACS/FHIR/IdP                           | `prod`, `monitoring`               | Pas de `auth`/`pacs`/`fhir`. Pointer `OIDC_ISSUER_URL`, `PACS_HOST`, `FHIR_BASE_URL`. |
| Hôpital fournit IdP, mais pas FHIR ni PACS                         | `prod`, `monitoring`, `fhir`, `pacs` | Sandbox locaux pour faire les démos clinicien.                              |
| Pilote sur un poste isolé (pas connecté SI hôpital)                 | `dev`                              | Tout en local.                                                              |
| Hôte d'entraînement ML séparé                                      | `mlops`                            | Pas de `prod`. Backend prod consomme MLflow via `MLFLOW_TRACKING_URI`.      |

---

## Voir aussi

- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) — ports, volumes, dépendances
- [DEPLOYMENT.md](./DEPLOYMENT.md) — procédure complète
- [services/](./services/) — détail par service
