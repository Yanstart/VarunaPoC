# Démarrage de l'infrastructure locale

**Statut:** ✅ Validé sur Windows 11 + Docker Desktop 29.x
**Dernière mise à jour:** 2026-05-26
**Public cible:** Dev / admin qui clone le repo pour lancer la stack complète (démo, captures, tests)

---

## Vue d'ensemble

La stack Varuna complète, c'est **18 containers** orchestrés par `docker compose` à partir d'un seul fichier `docker-compose.yml` profil-driven :

| Domaine | Services | Profil |
|---|---|---|
| Application | `backend` (FastAPI + OpenSlide), `frontend` (nginx + Vite build), `nginx` (reverse proxy) | `prod` |
| Stockage | `db` (PostGIS), `redis`, `keycloak-db` | `core`, `cache`, `auth` |
| Auth & IdP | `keycloak` | `auth` |
| Interopérabilité | `hapi-fhir`, `orthanc` (DICOM) | `fhir`, `pacs` |
| Observabilité | `prometheus`, `grafana`, `alertmanager`, exporters | `monitoring` |
| MLOps | `mlflow`, `minio`, `mlops-db` | `mlops` |

Le profil `prod` lance backend + frontend + nginx + stockage + auth + monitoring. Pour la démo complète, on ajoute `monitoring` + `mlops` + `fhir` + `pacs` (ces deux derniers sont activés sur le profil `prod` via `docker-compose.override.yml`).

---

## Prérequis

### Logiciels

- **Docker Desktop 29.x ou plus** (Windows / macOS / Linux).
  Vérifier : `docker info` doit répondre sans erreur.
- **Git** pour cloner le repo et faire les conversions de fin de ligne (`.gitattributes` force `LF` sur `*.sh`).
- **OpenSSL** (présent dans Git Bash sur Windows) pour générer le certificat HTTPS auto-signé.
- **PowerShell** sur Windows (utilisé pour quelques manipulations qui ne passent pas dans Git Bash).

### Système

- **RAM:** minimum 8 Go, recommandé 16 Go (le scan ML peut faire monter la conso).
- **Disque:** ~12 Go pour les images Docker + l'espace du dossier `Slides/` (~60 Go pour le jeu d'essai complet).
- **Ports libres sur l'hôte** (voir [Configuration des ports](#configuration-des-ports)).

### Données

- Le dossier `Slides/` à la racine du repo doit contenir au moins quelques lames test. Les sous-dossiers sont organisés par fournisseur (`Aperio/`, `Leica/`, `Hamamatsu/`, …). Ce dossier est gitignored — il faut se le procurer séparément.

---

## Configuration des ports

Par défaut, nginx écoute sur les ports **80** et **443**. Sur Windows, ces ports sont souvent capturés par le service `System` (HTTP.sys, IIS, WinRM). Vérifier avec :

```bash
netstat -ano | grep -E ":80\b|:443\b"
```

Si quelque chose tourne déjà sur 80/443, redéfinir les ports dans `.env` :

```env
HTTP_PORT=8200
HTTPS_PORT=8443
```

Les autres ports exposés (à laisser libres) :

| Port hôte | Service | Note |
|---|---|---|
| `8200` | nginx HTTP (alternative) | Configurable via `HTTP_PORT` |
| `8443` | nginx HTTPS | Configurable via `HTTPS_PORT` |
| `5433` | PostgreSQL | Évite collision avec `5432` (TimescaleDB) |
| `6380` | Redis | Évite collision avec `6379` |
| `8180` | Keycloak | OIDC IdP |
| `8090` | HAPI FHIR | Sandbox FHIR R4 |
| `4242` + `8042` | Orthanc | DICOM + Web UI |
| `3000` | Grafana | |
| `9090` / `9093` | Prometheus / Alertmanager | |
| `5000` | MLflow | |
| `9000` / `9001` | MinIO API / Console | |

---

## Première installation

### 1. Cloner le repo

```bash
git clone https://github.com/Yanstart/VarunaPoC.git
cd VarunaPoC
```

### 2. Créer le fichier `.env`

```bash
cp .env.dev.example .env
```

Ajuster les ports nginx si nécessaire (voir [Configuration des ports](#configuration-des-ports)) et conserver le bloc Keycloak suivant tel quel pour le dev local :

```env
KC_HOSTNAME=localhost
KC_HOSTNAME_PORT=8180
KC_HOSTNAME_STRICT_HTTPS=false
KC_PROXY=none
```

> `KC_PROXY=none` est volontaire pour le dev local : on n'a pas de reverse proxy devant Keycloak, donc on ne veut pas qu'il strippe le port. En prod, on repasse à `edge` et on met Keycloak derrière nginx avec un FQDN.

### 3. Générer le certificat HTTPS auto-signé

Le cert n'est pas committé. Le générer via PowerShell (Git Bash mange les `/CN=` dans `-subj`) :

```powershell
mkdir nginx\ssl -Force
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout nginx\ssl\varuna.key `
  -out nginx\ssl\varuna.crt `
  -subj "/CN=localhost"
```

Le navigateur affichera un warning au premier accès — c'est attendu, accepter l'exception.

### 4. Créer un `docker-compose.override.yml` local

Ce fichier n'est pas committé (host-specific). Le créer à la racine du repo avec ce contenu minimal pour le dev local Windows :

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    pull_policy: never
    environment:
      UVICORN_WORKERS: "1"
      OIDC_ISSUER_URL: "http://localhost:8180/realms/varuna"
      OIDC_INTERNAL_URL: "http://keycloak:8080/realms/varuna"

  migration:
    pull_policy: never

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: ""
    pull_policy: never

  keycloak:
    environment:
      KC_HOSTNAME_PORT: ${KC_HOSTNAME_PORT:-8180}

  mlflow:
    entrypoint: ["/bin/bash", "-c"]
    command:
      - |
        pip install --quiet psycopg2-binary boto3 &&
        exec mlflow server \
          --host 0.0.0.0 \
          --port 5000 \
          --backend-store-uri "$$MLFLOW_BACKEND_STORE_URI" \
          --default-artifact-root "$$MLFLOW_DEFAULT_ARTIFACT_ROOT"

  hapi-fhir:
    profiles: ["fhir", "dev", "prod"]

  orthanc:
    profiles: ["pacs", "dev", "prod"]
```

Justification de chaque bloc :

- `backend.build` + `pull_policy: never` : force le build local au lieu de tirer l'image depuis GHCR (registre privé, demanderait `docker login`).
- `UVICORN_WORKERS: "1"` : la re-exec d'OpenSlide avec `LD_LIBRARY_PATH` casse `multiprocessing.spawn` d'Uvicorn. Workaround connu — en prod on scale avec `BACKEND_REPLICAS`.
- `OIDC_INTERNAL_URL` : l'`iss` du JWT contient l'URL publique de Keycloak (`localhost:8180`), inaccessible depuis le container backend. `OIDC_INTERNAL_URL` pointe vers l'URL interne (`keycloak:8080`) pour fetch JWKS.
- `KC_HOSTNAME_PORT` : le `docker-compose.yml` canonique n'expose pas cette variable, l'override la propage.
- `mlflow.entrypoint` : l'image officielle MLflow ne contient pas `psycopg2`. Installation au boot — fragile, à remplacer en prod par un Dockerfile custom.
- `hapi-fhir` / `orthanc` profils étendus : pour qu'ils tournent dans le bloc `prod` (utile pour les démos / captures).

---

## Lancer la stack

### Démarrage complet (recommandé pour démo)

```bash
docker compose --profile prod --profile monitoring --profile mlops up -d
```

Premier lancement : compter ~5 à 10 minutes (build de l'image backend avec OpenSlide, pull des autres images).

Lancements suivants : ~30 secondes (images en cache).

### Démarrage minimal (juste l'app)

```bash
docker compose --profile prod up -d
```

Lance uniquement backend + frontend + nginx + auth + stockage. Pas de monitoring ni MLOps.

---

## Vérifier que tout est OK

### Statut des containers

```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep varuna
```

Vous devez voir 18 containers, la plupart en `Up X minutes (healthy)`. Les deux containers `varuna-migration` et `varuna-minio-init` sont en `Exited (0)` — c'est normal, ce sont des jobs one-shot qui ont terminé leur tâche.

### Smoke tests des endpoints

```bash
curl -sk -o /dev/null -w "viewer:       %{http_code}\n" https://localhost:8443/
curl -sk -o /dev/null -w "api health:   %{http_code}\n" https://localhost:8443/api/v1/health
curl -sk -o /dev/null -w "keycloak:     %{http_code}\n" http://localhost:8180/realms/varuna
curl -sk -o /dev/null -w "grafana:      %{http_code}\n" http://localhost:3000/api/health
curl -sk -o /dev/null -w "mlflow:       %{http_code}\n" http://localhost:5000/health
```

Tout doit répondre `200` (sauf Orthanc qui répond `401` — basic auth requis, c'est attendu).

---

## URLs et accès

### Application

| Service | URL | Auth |
|---|---|---|
| **Viewer (HTTPS)** | https://localhost:8443 | via Keycloak |
| Viewer (HTTP) | http://localhost:8200 | idem |
| Swagger | https://localhost:8443/api/v1/docs | — |

### Comptes Keycloak test

| User | Mot de passe | Rôle | Use case |
|---|---|---|---|
| dr.martin | password | MEDECIN | Pathologiste : annote, signe, voit tout |
| nurse.dupont | password | INFIRMIER | Pré-screening |
| admin | password | ADMIN_TECHNIQUE | Config, audit |
| viewer | password | LECTURE_SEULE | Lecture seule |

> ⚠️ Les hashes de mot de passe dans `backend/keycloak/realm-export.json` peuvent ne pas être acceptés par Keycloak 23 selon la version exacte. Si le login échoue avec "Invalid credentials", reset via l'Admin API :
> ```bash
> TOKEN=$(curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
>   -d "username=admin" -d "password=admin" -d "grant_type=password" -d "client_id=admin-cli" \
>   | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
> for u in dr.martin nurse.dupont viewer admin; do
>   UID=$(curl -s -H "Authorization: Bearer $TOKEN" \
>     "http://localhost:8180/admin/realms/varuna/users?username=$u&exact=true" \
>     | python -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")
>   curl -s -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
>     "http://localhost:8180/admin/realms/varuna/users/$UID/reset-password" \
>     -d '{"type":"password","value":"password","temporary":false}'
> done
> ```

### Monitoring & MLOps

| Service | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3000 | admin / admin (changement au 1er login) |
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| MLflow | http://localhost:5000 | — |
| MinIO Console | http://localhost:9001 | varuna-admin / varuna_dev |

### Sandboxes interopérabilité

| Service | URL | Credentials |
|---|---|---|
| HAPI FHIR | http://localhost:8090 | — |
| Orthanc UI | http://localhost:8042 | orthanc / orthanc |
| Orthanc DICOM | tcp://localhost:4242 | — |

---

## Premier login

1. Aller sur https://localhost:8443
2. Accepter le warning de certificat (auto-signé)
3. Cliquer **Login** — redirige vers Keycloak sur http://localhost:8180
4. Entrer `dr.martin / password`
5. Retour sur l'app, sur la page d'accueil (mode "cases" par défaut)

### Passer en mode explorer (browse fichiers)

La home page propose 3 vues. Le mode `explorer` permet de naviguer dans l'arborescence brute des dossiers (`Aperio/`, `Leica/`, …). À activer via la console DevTools :

```javascript
localStorage.setItem('varuna_home_view', 'explorer');
location.reload();
```

---

## Arrêt / redémarrage

### Arrêt propre

```bash
docker compose --profile prod --profile monitoring --profile mlops down
```

Les volumes (donc les données : Keycloak users, annotations, audit logs, MLflow runs) sont conservés. Pour repartir d'une base vide, ajouter `-v` (destructif).

### Redémarrage du PC

Rien à faire : les services ont `restart: unless-stopped`. Docker Desktop relance la stack automatiquement au démarrage. Vérifier avec `docker ps` que les 18 containers sont up.

### Redémarrage d'un seul service

```bash
docker compose restart backend
```

ou recréation complète (utile après changement de code) :

```bash
docker build -t ghcr.io/yanstart/varunapoc/backend:main ./backend
docker compose up -d --force-recreate --no-deps backend
```

---

## Troubleshooting

### "Port 80 already in use" sur Windows

`netstat -ano | grep ":80 "` montre PID 4 (System / HTTP.sys). Solutions :
- Définir `HTTP_PORT=8200` et `HTTPS_PORT=8443` dans `.env` (recommandé).
- Ou stopper le service Windows responsable (`Stop-Service -Name "W3SVC"` pour IIS, idem pour `WinRM`).

### Nginx restart en boucle avec `exec /docker-entrypoint-varuna.sh: no such file or directory`

Le shebang du script est en CRLF (artefact Windows). Normalement bloqué par `.gitattributes`, mais si reproduit, forcer LF via PowerShell :

```powershell
$path = "nginx\docker-entrypoint.sh"
$content = [IO.File]::ReadAllText((Resolve-Path $path))
[IO.File]::WriteAllText((Resolve-Path $path), $content -replace "`r`n", "`n")
```

### Frontend / nginx unhealthy malgré container running

Le healthcheck utilisait `localhost` qui résout en `::1` (IPv6) sur Alpine, alors que les services bindent uniquement IPv4. Corrigé en `127.0.0.1` dans `docker-compose.yml`. Si vous re-clonez et observez ce bug, vérifier que les healthchecks utilisent `http://127.0.0.1/...`.

### MLflow restart en boucle (`ModuleNotFoundError: psycopg2`)

L'image officielle MLflow n'inclut pas `psycopg2`. L'override fait `pip install` au boot — assurez-vous que l'`entrypoint` du bloc `mlflow` est bien présent dans `docker-compose.override.yml`. À terme, créer un Dockerfile custom.

### Login Keycloak réussit mais l'app reboucle vers la page de login

Token rejeté par le backend. Causes possibles :
- `OIDC_ISSUER_URL` mismatch avec l'`iss` du JWT. Vérifier `docker exec varuna-backend env | grep OIDC` et comparer avec `curl -s http://localhost:8180/realms/varuna/.well-known/openid-configuration | python -c "import sys, json; print(json.load(sys.stdin)['issuer'])"`. Les deux strings doivent matcher exactement.
- `OIDC_INTERNAL_URL` manquant côté backend : le backend ne peut pas fetcher JWKS depuis l'URL publique `localhost:8180` (résout vers lui-même dans le container). Cette variable doit pointer vers `http://keycloak:8080/realms/varuna`.

### Tiles d'une lame en 401 alors que la home page marche

Le viewer OpenSeadragon initialise `ajaxHeaders` une fois au démarrage. Si le token est rotated, les tiles continuent avec l'ancien header. Le code utilise `getTileAjaxHeaders` (callback par-tile) pour éviter ça. Si le bug persiste, vérifier que le bundle JS récent est servi (hash de fichier visible dans le HTML).

### Erreur "Failed to browse directory" en mode explorer

`utils/api.js#fetchBrowse` doit déléguer à `ApiService.browse()` (qui injecte le Bearer header). Sinon le fetch part sans `Authorization` → 401.

---

## Bonus : workflow de dev

Pour itérer sur le backend ou le frontend sans tout reconstruire :

### Frontend : Vite dev server (hot reload)

```bash
cd frontend
npm ci    # une fois
npm run dev
```

L'app tourne sur http://localhost:5173 et appelle l'API backend à http://localhost:8000. Le bundle est rebuild à chaque sauvegarde. Pour cela, le backend doit être exposé directement sur :8000 (ajouter `ports: ["8000:8000"]` au bloc `backend` de l'override) — sinon Vite ne peut pas joindre l'API.

### Backend : Uvicorn local hot-reload

```bash
cd backend
pip install -r requirements.txt    # une fois
python -m uvicorn main:app --reload --port 8000
```

Stopper le container `varuna-backend` avant pour éviter le conflit de port.

---

## Référence

- **Architecture détaillée :** [`docs/architecture/MODULAR_ARCHITECTURE.md`](../architecture/MODULAR_ARCHITECTURE.md)
- **Git workflow :** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- **Spec du projet :** [`docs/PROPOSAL_VARUNA_v2.md`](../PROPOSAL_VARUNA_v2.md)
