# Secrets Management

Operational guide for managing sensitive credentials (database passwords, API keys, etc.) in VarunaPoC production deployments.

## Overview

VarunaPoC supports two secrets backends:

| Backend | When to use |
|---------|-------------|
| Docker Secrets (file-based) | Docker Swarm or Compose v2 in production |
| Environment variables | Local development, CI/CD pipelines |

The `backend/core/secrets.py` module resolves secrets transparently — it checks `/run/secrets/{name}` first and falls back to the environment variable of the same name.

---

## Docker Secrets

### How it works

Docker mounts each secret as a read-only file under `/run/secrets/` inside the container. The file content is the secret value.

### Creating secrets

```bash
# From a literal value (interactive — value not stored in shell history)
printf 'MyStr0ngPassw0rd' | docker secret create db_password -

# From a file
docker secret create db_password ./secrets/db_password.txt

# Verify
docker secret ls
```

### Referencing secrets in Compose

```yaml
# Top-level secrets block — declare where files live on the host
secrets:
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt

services:
  db:
    image: postgis/postgis:16-3.4
    secrets:
      - db_password
    environment:
      # The service reads the secret via get_secret("db_password")
      # No plaintext password in environment variables
      POSTGRES_DB: varuna
      POSTGRES_USER: varuna
```

See `docker-compose.production.yml` for the concrete example in the `db` service.

### Secret file security

- Store secret files outside the repository (never commit them).
- Permissions should be `600` (owner read/write only).
- On shared servers, use a dedicated service account.

```bash
mkdir -p ./secrets
chmod 700 ./secrets
echo -n 'MyStr0ngPassw0rd' > ./secrets/db_password.txt
chmod 600 ./secrets/db_password.txt
```

---

## HashiCorp Vault integration

For larger deployments or when secrets must be rotated automatically, HashiCorp Vault provides a centralized secrets store.

**Reference:** https://developer.hashicorp.com/vault/docs

### Pattern: Vault Agent sidecar

The recommended pattern is a Vault Agent container that fetches secrets at startup and writes them as files to a shared volume. The application reads those files exactly as it would Docker Secrets — no application code change required.

```
┌─────────────────────────────────────────────┐
│  Pod / Compose project                       │
│                                              │
│  ┌──────────────┐    /run/secrets/           │
│  │  vault-agent │──> db_password             │
│  │  (sidecar)   │──> redis_password          │
│  └──────────────┘         │                  │
│                           v                  │
│  ┌──────────────┐   reads files              │
│  │   backend    │<──────────────             │
│  └──────────────┘                            │
└─────────────────────────────────────────────┘
```

**Vault Agent configuration sketch:**

```hcl
# vault-agent.hcl
vault {
  address = "https://vault.hospital.local:8200"
}

auto_auth {
  method "approle" {
    config = {
      role_id_file_path   = "/vault/role-id"
      secret_id_file_path = "/vault/secret-id"
    }
  }
}

template {
  contents    = "{{ with secret \"secret/varuna/db_password\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/run/secrets/db_password"
}

template {
  contents    = "{{ with secret \"secret/varuna/redis_password\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/run/secrets/redis_password"
}
```

Because the output path matches `/run/secrets/{name}`, `get_secret()` picks it up with no further changes.

---

## Migration path from environment variables

Current state: passwords are passed as `${POSTGRES_PASSWORD}` and `${REDIS_PASSWORD}` environment variables from `.env.production`.

Target state: secrets are mounted as files; env vars are removed or left empty.

### Step-by-step migration

1. **Generate secret files** on the deployment host:
   ```bash
   mkdir -p ./secrets && chmod 700 ./secrets
   printf '%s' "$POSTGRES_PASSWORD" > ./secrets/db_password.txt
   printf '%s' "$REDIS_PASSWORD"    > ./secrets/redis_password.txt
   chmod 600 ./secrets/*.txt
   ```

2. **Update `.env.production`** — remove or blank the plaintext variables:
   ```bash
   # Remove these lines:
   # POSTGRES_PASSWORD=...
   # REDIS_PASSWORD=...
   ```

3. **Deploy** with the updated `docker-compose.production.yml` that declares the `secrets:` block.

4. **Verify** the backend resolves secrets correctly:
   ```bash
   docker compose -f docker-compose.production.yml exec backend \
       python -c "from backend.core.secrets import get_secret; print(bool(get_secret('db_password')))"
   # Expected output: True
   ```

5. **Remove** the old `.env.production` lines from version control history if they were ever committed (use `git filter-repo` or contact your security officer).

---

## Security considerations

- Never log secret values. `get_secret()` returns the raw string — callers are responsible for not printing it.
- Rotate secrets at least every 90 days (HIPAA requirement for access credentials).
- Audit which services have access to which secrets via `docker secret inspect`.
- In Docker Swarm mode, secrets are encrypted at rest and in transit between nodes.

---

## See also

- `backend/core/secrets.py` — implementation
- `docker-compose.production.yml` — compose secrets example
- `docs/Deployment/DEPLOYMENT_GUIDE.md` — full deployment guide
- Docker Secrets reference: https://docs.docker.com/engine/swarm/secrets/
- HashiCorp Vault: https://developer.hashicorp.com/vault/docs
