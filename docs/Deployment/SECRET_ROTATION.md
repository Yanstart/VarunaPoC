# Secret Rotation Guide - VarunaPoC

This document lists all secrets used by VarunaPoC in production, explains how to rotate each one, and provides a recommended rotation schedule.

## Table of Contents

- [Secret Inventory](#secret-inventory)
- [Generating Strong Passwords](#generating-strong-passwords)
- [Rotation Procedures](#rotation-procedures)
  - [POSTGRES_PASSWORD](#postgres_password)
  - [REDIS_PASSWORD](#redis_password)
  - [KEYCLOAK_ADMIN_PASSWORD](#keycloak_admin_password)
  - [KEYCLOAK_DB_PASSWORD](#keycloak_db_password)
  - [GRAFANA_ADMIN_PASSWORD](#grafana_admin_password)
  - [TLS Certificates](#tls-certificates)
- [Rotation Schedule](#rotation-schedule)
- [Verification Checklist](#verification-checklist)

---

## Secret Inventory

| Variable | Service(s) | Profile | Required | Description |
|----------|-----------|---------|----------|-------------|
| `POSTGRES_PASSWORD` | db, migration, backend | core | Yes | PostgreSQL main database password |
| `REDIS_PASSWORD` | redis, backend, redis-exporter | core / monitoring | Yes | Redis cache authentication |
| `KEYCLOAK_ADMIN_PASSWORD` | keycloak | auth | Yes (with `--profile auth`) | Keycloak admin console password |
| `KEYCLOAK_DB_PASSWORD` | keycloak-db, keycloak | auth | Yes (with `--profile auth`) | Keycloak PostgreSQL database password |
| `GRAFANA_ADMIN_PASSWORD` | grafana | monitoring | Yes (with `--profile monitoring`) | Grafana admin UI password |
| TLS certificate + key | nginx | core | Yes (for HTTPS) | Located in `nginx/ssl/` |

All password variables use the `${VAR:?error}` syntax in `docker-compose.yml`, which means Docker Compose will refuse to start if any required secret is missing.

---

## Generating Strong Passwords

Use one of the following methods to generate a cryptographically secure password (minimum 32 characters recommended):

```bash
# Option 1: OpenSSL (recommended)
openssl rand -base64 32

# Option 2: /dev/urandom
tr -dc 'A-Za-z0-9!@#$%&*' < /dev/urandom | head -c 32; echo

# Option 3: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Requirements:**
- Minimum 24 characters, 32+ recommended
- Mix of uppercase, lowercase, digits, and symbols
- Avoid characters that break shell quoting in `.env` files: backtick, double quote, dollar sign, backslash
- Never reuse passwords across services

---

## Rotation Procedures

### General Workflow

For every secret rotation:

1. Generate a new password
2. Plan for brief downtime (or rolling restart if supported)
3. Update `.env.production` with the new value
4. Restart affected services
5. Verify connectivity
6. Record the rotation date in your ops log

### POSTGRES_PASSWORD

**Affected services:** db, migration, backend

**Steps:**

1. Generate a new password:
   ```bash
   openssl rand -base64 32
   ```

2. Connect to the running database and change the password:
   ```bash
   docker compose --profile prod --profile monitoring exec db \
     psql -U varuna -d varuna -c "ALTER USER varuna WITH PASSWORD 'NEW_PASSWORD_HERE';"  # pragma: allowlist secret
   ```

3. Update `.env.production`:
   ```
   POSTGRES_PASSWORD=NEW_PASSWORD_HERE
   ```

4. Restart services that use the database connection:
   ```bash
   docker compose --profile prod --profile monitoring --env-file .env.production \
     restart backend
   ```

5. Verify: see [Verification Checklist](#verification-checklist).

**Note:** The migration service only runs at startup, so it will use the new password on the next full deploy.

### REDIS_PASSWORD

**Affected services:** redis, backend, redis-exporter (monitoring profile)

**Steps:**

1. Generate a new password:
   ```bash
   openssl rand -base64 32
   ```

2. Update the password on the running Redis instance:
   ```bash
   docker compose --profile prod --profile monitoring exec redis \
     redis-cli -a 'OLD_PASSWORD' CONFIG SET requirepass 'NEW_PASSWORD_HERE'
   ```

3. Update `.env.production`:
   ```
   REDIS_PASSWORD=NEW_PASSWORD_HERE
   ```

4. Restart all services that connect to Redis:
   ```bash
   docker compose --profile prod --profile monitoring --env-file .env.production \
     restart backend

   # If monitoring profile is active:
   docker compose --profile prod --profile monitoring --env-file .env.production \
     --profile monitoring restart redis-exporter
   ```

5. Verify: see [Verification Checklist](#verification-checklist).

**Note:** Redis CONFIG SET applies immediately but does not persist across restarts. The `.env.production` update ensures the new password is used after any future restart.

### KEYCLOAK_ADMIN_PASSWORD

**Affected services:** keycloak

**Steps:**

1. Generate a new password:
   ```bash
   openssl rand -base64 32
   ```

2. Log in to the Keycloak admin console at `http://<host>:8180` with the current admin credentials.

3. Navigate to **Users** in the master realm, select the `admin` user, go to the **Credentials** tab, and set the new password.

4. Update `.env.production`:
   ```
   KEYCLOAK_ADMIN_PASSWORD=NEW_PASSWORD_HERE
   ```

5. No service restart is required since the password was changed through the UI. The `.env.production` value is only used for initial bootstrap or fresh container creation.

6. Verify: log in to `http://<host>:8180` with the new password.

### KEYCLOAK_DB_PASSWORD

**Affected services:** keycloak-db, keycloak

**Steps:**

1. Generate a new password:
   ```bash
   openssl rand -base64 32
   ```

2. Change the password in the Keycloak database:
   ```bash
   docker compose --profile prod --profile monitoring exec keycloak-db \
     psql -U keycloak -d keycloak -c "ALTER USER keycloak WITH PASSWORD 'NEW_PASSWORD_HERE';"  # pragma: allowlist secret
   ```

3. Update `.env.production`:
   ```
   KEYCLOAK_DB_PASSWORD=NEW_PASSWORD_HERE
   ```

4. Restart Keycloak (it reads the DB password from environment):
   ```bash
   docker compose --profile prod --profile monitoring --env-file .env.production \
     --profile auth restart keycloak
   ```

5. Verify: see [Verification Checklist](#verification-checklist).

### GRAFANA_ADMIN_PASSWORD

**Affected services:** grafana

**Steps:**

1. Generate a new password:
   ```bash
   openssl rand -base64 32
   ```

2. Change the password using the Grafana CLI inside the container:
   ```bash
   docker compose --profile prod --profile monitoring exec grafana \
     grafana cli admin reset-admin-password 'NEW_PASSWORD_HERE'
   ```

3. Update `.env.production`:
   ```
   GRAFANA_ADMIN_PASSWORD=NEW_PASSWORD_HERE
   ```

4. No restart is needed when using `grafana cli`. The `.env.production` value ensures consistency on fresh container creation.

5. Verify: log in to `http://<host>:3000` with username `admin` and the new password.

### TLS Certificates

**Affected service:** nginx

**Location:** `nginx/ssl/` (mounted read-only into the nginx container)

**Steps:**

1. Obtain the renewed certificate and key from your CA or internal PKI.

2. Replace the files:
   ```bash
   cp new-cert.pem nginx/ssl/cert.pem
   cp new-key.pem nginx/ssl/key.pem
   chmod 600 nginx/ssl/key.pem
   chmod 644 nginx/ssl/cert.pem
   ```

3. Reload nginx without downtime:
   ```bash
   docker compose --profile prod --profile monitoring exec nginx nginx -s reload
   ```

4. Verify:
   ```bash
   openssl s_client -connect localhost:443 -servername varuna.chu-ucl.be </dev/null 2>/dev/null \
     | openssl x509 -noout -dates
   ```

---

## Rotation Schedule

| Secret | Rotation Frequency | Notes |
|--------|--------------------|-------|
| `POSTGRES_PASSWORD` | Every 90 days | Critical -- protects patient annotation data |
| `REDIS_PASSWORD` | Every 90 days | Protects cached tile data and session state |
| `KEYCLOAK_ADMIN_PASSWORD` | Every 90 days | Admin access to identity provider |
| `KEYCLOAK_DB_PASSWORD` | Every 90 days | Database backing the identity provider |
| `GRAFANA_ADMIN_PASSWORD` | Every 90 days | Admin access to monitoring dashboards |
| TLS certificates | Annually (or per CA policy) | Set a reminder 30 days before expiry |

**Recommended approach:** Set a recurring calendar reminder at the start of each quarter (January, April, July, October) to rotate all passwords. Track rotations in your ops log or ticket system.

---

## Verification Checklist

After rotating any secret, verify the affected services are working correctly:

### Core Services (POSTGRES_PASSWORD, REDIS_PASSWORD)

```bash
# Check all containers are running and healthy
docker compose --profile prod --profile monitoring --env-file .env.production ps

# Backend health check
curl -f http://localhost/api/health

# Check backend logs for connection errors
docker compose --profile prod --profile monitoring logs --tail=50 backend | grep -i error

# Verify database connectivity
docker compose --profile prod --profile monitoring exec db \
  pg_isready -U varuna -d varuna

# Verify Redis connectivity
docker compose --profile prod --profile monitoring exec redis \
  redis-cli -a 'NEW_PASSWORD' ping
# Expected output: PONG
```

### Auth Services (KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_DB_PASSWORD)

```bash
# Keycloak health check
curl -f http://localhost:8180/health/ready

# Verify Keycloak admin login (get token)
curl -s -X POST http://localhost:8180/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=NEW_PASSWORD" \
  -d "grant_type=password" | python3 -m json.tool

# Check Keycloak logs
docker compose --profile prod --profile monitoring --profile auth logs --tail=50 keycloak | grep -i error
```

### Monitoring Services (GRAFANA_ADMIN_PASSWORD)

```bash
# Grafana health check
curl -f http://localhost:3000/api/health

# Verify Grafana admin login
curl -s -u admin:NEW_PASSWORD http://localhost:3000/api/org | python3 -m json.tool

# Verify Prometheus is scraping targets
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data['data']['activeTargets']:
    print(f\"{t['labels'].get('job','?'):30s} {t['health']}\")"
```

### TLS Certificates

```bash
# Check certificate validity dates
openssl s_client -connect localhost:443 -servername varuna.chu-ucl.be </dev/null 2>/dev/null \
  | openssl x509 -noout -dates -subject

# Verify no TLS errors in nginx logs
docker compose --profile prod --profile monitoring logs --tail=50 nginx | grep -i "ssl\|tls\|cert"
```

---

## Troubleshooting

### Service fails to start after rotation

1. Check that `.env.production` has no trailing whitespace or stray quotes around the password.
2. Verify the password was changed in the service **before** updating `.env.production` and restarting consumers.
3. Check logs: `docker compose --profile prod --profile monitoring logs <service>`.

### "authentication failed" errors in backend logs

The backend reads `POSTGRES_PASSWORD` and `REDIS_PASSWORD` from its environment. If the database password was changed but the backend was not restarted, it will still use the old password. Restart the backend:

```bash
docker compose --profile prod --profile monitoring --env-file .env.production restart backend
```

### Redis exporter shows connection errors after Redis password rotation

The redis-exporter must also be restarted after changing `REDIS_PASSWORD`:

```bash
docker compose --profile prod --profile monitoring --env-file .env.production \
  --profile monitoring restart redis-exporter
```
