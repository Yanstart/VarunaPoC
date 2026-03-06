# Procedure demarrage complet (dev)

## Prerequis

- Docker running
- Backend venv avec dependencies (`pip install -r requirements.txt`)
- Frontend node_modules (`npm ci`)
- OpenSlide patche installe (voir 001-openslide-bif-left-patch.md)

## Ordre de demarrage

### 1. Stack Docker dev (DB + Keycloak)

```bash
cd /data/VarunaPoC
docker compose -f docker-compose.dev.yml up -d
```

Attendre que Keycloak soit ready (~60s) :
```bash
curl -s http://localhost:8180/realms/varuna/.well-known/openid-configuration | head -1
```

### 2. Migrations DB

```bash
cd /data/VarunaPoC/backend
source venv/bin/activate
python -m alembic upgrade head
```

### 3. Backend

```bash
cd /data/VarunaPoC/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verifier : `curl -s http://localhost:8000/api/health`

### 4. Frontend

```bash
cd /data/VarunaPoC/frontend
npm run dev
```

Verifier : `http://localhost:5173`

## Configuration auth

Dans `backend/.env` :
```env
AUTH_ENABLED=true
OIDC_ISSUER_URL=http://localhost:8180/realms/varuna
OIDC_CLIENT_ID=varuna-viewer
OIDC_AUDIENCE=varuna-viewer
OIDC_ROLE_CLAIM=realm_access.roles
```

## Comptes de test

Les mots de passe sont hashes dans le realm-export.json.
Apres chaque `docker compose down -v` (reset volumes), il faut les reinitialiser :

```bash
# Obtenir un admin token
ADMIN_TOKEN=$(curl -s -X POST \
  "http://localhost:8180/realms/master/protocol/openid-connect/token" \
  -d "username=admin&password=admin&grant_type=password&client_id=admin-cli" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Lister les users du realm varuna
USERS=$(curl -s "http://localhost:8180/admin/realms/varuna/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

# Reset password pour chaque user
for username in dr.martin nurse.dupont admin viewer; do
  USER_ID=$(echo "$USERS" | python3 -c "
import sys,json
users=json.load(sys.stdin)
print(next(u['id'] for u in users if u['username']=='$username'))
")
  curl -s -X PUT \
    "http://localhost:8180/admin/realms/varuna/users/$USER_ID/reset-password" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"type":"password","value":"test123","temporary":false}'
  echo "$username: password reset to test123"
done
```

| User | Mot de passe | Role |
|------|-------------|------|
| dr.martin | test123 | MEDECIN |
| nurse.dupont | test123 | INFIRMIER |
| admin | test123 | ADMIN_TECHNIQUE |
| viewer | test123 | LECTURE_SEULE |

## Arret

```bash
# Frontend/Backend : Ctrl+C
# Docker :
docker compose -f docker-compose.dev.yml down      # garde les volumes
docker compose -f docker-compose.dev.yml down -v    # reset complet
```

## Ne PAS demarrer

- Les GitHub Actions runners (`varuna-runner`) — reserves au pipeline CI
