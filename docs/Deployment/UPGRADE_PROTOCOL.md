# VarunaPoC - Upgrade and Rollback Protocol

**Version:** 1.0
**Date:** 2026-03-11
**Audience:** Hospital IT administrators

---

## Overview

This document describes how to upgrade VarunaPoC to a new version and how to
roll back if something goes wrong. Both operations are automated through scripts
in the `scripts/` directory and are designed for the Docker Compose production
deployment (`docker-compose.yml`).

---

## Pre-Upgrade Checklist

Before starting any upgrade:

- [ ] **Schedule a maintenance window** -- coordinate with the pathology lab so
      no one is actively reviewing slides during the upgrade.
- [ ] **Notify users** -- send an email or intranet announcement with the
      planned start time and expected duration (15-30 minutes).
- [ ] **Verify disk space** -- ensure at least 5 GB of free space for the
      database backup and new Docker images (`df -h`).
- [ ] **Confirm current version** -- note the running image tags so you know
      what to roll back to:
      ```bash
      docker compose --profile prod --profile monitoring --env-file .env.production ps --format '{{.Image}}'
      ```
- [ ] **Read the release notes** -- check the GitHub release page for the
      target version. Look for breaking changes, new environment variables,
      or required manual steps.
- [ ] **Test the backup script** -- run `./scripts/backup.sh` and verify the
      output file is non-empty.
- [ ] **Verify NAS mount** -- make sure `/mnt/chu-slides` (or your configured
      `SLIDES_HOST_PATH`) is mounted and accessible.
- [ ] **Ensure Docker is running** -- `docker info` should succeed.

---

## Upgrade Procedure

### Automated (recommended)

```bash
cd /path/to/VarunaPoC

# Upgrade to a specific version
./scripts/upgrade.sh v1.1.0
```

The script performs the following steps:

1. Validates configuration files (`.env.production`, compose file).
2. Creates a database backup via `scripts/backup.sh`.
3. Pulls the new backend and frontend images tagged with the target version.
4. Runs database migrations (`alembic upgrade head`) inside the migration
   container.
5. Recreates all services with the new image tag.
6. Waits for all health checks to pass (default timeout: 120 seconds,
   configurable via `HEALTH_TIMEOUT` environment variable).
7. Prints a success summary with rollback instructions.

### Manual (step by step)

If you prefer to run each step manually:

```bash
cd /path/to/VarunaPoC
source .env.production

COMPOSE_CMD="docker compose --profile prod --profile monitoring --env-file .env.production"
NEW_VERSION="v1.1.0"

# 1. Backup database
./scripts/backup.sh

# 2. Pull new images
docker pull ghcr.io/yanstart/varunapoc/backend:${NEW_VERSION}
docker pull ghcr.io/yanstart/varunapoc/frontend:${NEW_VERSION}

# 3. Run migrations
$COMPOSE_CMD run --rm -e BACKEND_IMAGE_TAG=${NEW_VERSION} migration

# 4. Recreate services
export BACKEND_IMAGE_TAG=${NEW_VERSION}
export FRONTEND_IMAGE_TAG=${NEW_VERSION}
$COMPOSE_CMD up -d --force-recreate --no-build

# 5. Verify health
$COMPOSE_CMD ps
curl -f http://localhost/api/health
```

---

## Rollback Procedure

### Automated (recommended)

```bash
cd /path/to/VarunaPoC

# Roll back to previous version with database restore
./scripts/rollback.sh v1.0.0 backups/varuna_db_20260311_020000.sql.gz

# Roll back images only (no database restore)
./scripts/rollback.sh v1.0.0 --no-db-restore
```

The script performs the following steps:

1. Stops all running services.
2. Starts only the database container.
3. Drops and recreates the database, then restores from the backup file.
4. Stops the database.
5. Pulls the old version images.
6. Starts all services with the old image tags.
7. Waits for health checks to pass.

### Manual (step by step)

```bash
cd /path/to/VarunaPoC
source .env.production

COMPOSE_CMD="docker compose --profile prod --profile monitoring --env-file .env.production"
OLD_VERSION="v1.0.0"
BACKUP_FILE="backups/varuna_db_20260311_020000.sql.gz"

# 1. Stop services
$COMPOSE_CMD down

# 2. Start database only
$COMPOSE_CMD up -d db
sleep 10  # Wait for DB readiness

# 3. Restore database
docker compose exec -T db psql -U varuna -d postgres \
    -c "DROP DATABASE IF EXISTS varuna;"
docker compose exec -T db psql -U varuna -d postgres \
    -c "CREATE DATABASE varuna OWNER varuna;"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U varuna -d varuna --quiet

# 4. Stop database
$COMPOSE_CMD down

# 5. Pull old images
docker pull ghcr.io/yanstart/varunapoc/backend:${OLD_VERSION}
docker pull ghcr.io/yanstart/varunapoc/frontend:${OLD_VERSION}

# 6. Restart with old version
export BACKEND_IMAGE_TAG=${OLD_VERSION}
export FRONTEND_IMAGE_TAG=${OLD_VERSION}
$COMPOSE_CMD up -d

# 7. Verify
$COMPOSE_CMD ps
curl -f http://localhost/api/health
```

---

## Testing After Upgrade

After the upgrade script completes successfully, run through this verification
checklist:

- [ ] **Health endpoint** -- `curl http://localhost/api/health` returns 200.
- [ ] **Frontend loads** -- open `http://localhost/` in a browser, confirm the
      viewer appears.
- [ ] **Open a slide** -- select a slide from the list and confirm tiles load
      correctly.
- [ ] **Annotations** -- create and save an annotation, then reload the page
      to verify persistence.
- [ ] **Monitoring (if enabled)** -- check Grafana dashboards at
      `http://localhost:3000/` for errors.
- [ ] **Check logs** -- `docker compose logs --tail=50 backend` should not
      show unexpected errors.

---

## Version Compatibility Matrix

| VarunaPoC Version | PostgreSQL | PostGIS  | Redis   | OpenSlide | Migration Required |
|-------------------|------------|----------|---------|-----------|--------------------|
| v0.1.0            | 16.x      | 3.4      | 7.x     | 4.0.x     | Baseline           |
| v0.2.0            | 16.x      | 3.4      | 7.x     | 4.0.x     | Yes (alembic)      |
| v1.0.0+           | 16.x      | 3.4      | 7.x     | 4.0.x     | Yes (alembic)      |

**Notes:**

- PostgreSQL major version upgrades (e.g., 16 to 17) require a separate
  `pg_upgrade` procedure -- they are not covered by this script.
- Redis is used as a volatile cache. No data migration is needed between Redis
  versions.
- OpenSlide is bundled inside the backend Docker image; it upgrades
  automatically with the image.

---

## Environment Variables

The scripts read their configuration from `.env.production` in the project root.
Key variables:

| Variable             | Default                                     | Description                          |
|----------------------|---------------------------------------------|--------------------------------------|
| `BACKEND_IMAGE`      | `ghcr.io/yanstart/varunapoc/backend`        | Backend Docker image                 |
| `BACKEND_IMAGE_TAG`  | `main`                                      | Backend image tag                    |
| `FRONTEND_IMAGE`     | `ghcr.io/yanstart/varunapoc/frontend`       | Frontend Docker image                |
| `FRONTEND_IMAGE_TAG` | `main`                                      | Frontend image tag                   |
| `POSTGRES_USER`      | `varuna`                                    | PostgreSQL username                  |
| `POSTGRES_DB`        | `varuna`                                    | PostgreSQL database name             |
| `HEALTH_TIMEOUT`     | `120`                                       | Seconds to wait for health checks    |

---

## Backup Management

Backups are stored in the `backups/` directory at the project root by default.

```bash
# Create a manual backup
./scripts/backup.sh

# Create a backup in a custom directory
./scripts/backup.sh /mnt/backup/varuna

# List existing backups
ls -lh backups/
```

**Retention:** Implement a cron job to clean up old backups:

```cron
# Keep backups for 30 days
0 3 * * * find /path/to/VarunaPoC/backups -name "*.sql.gz" -mtime +30 -delete
```

---

## Emergency Contacts

| Role                     | Contact                           |
|--------------------------|-----------------------------------|
| IT Infrastructure        | infrastructure@chuuclnamur.be     |
| Storage Team (NAS)       | storage-admins@chuuclnamur.be     |
| Pathology Lab            | anapath@chuuclnamur.be            |
| Application Maintainer   | (see repository CODEOWNERS)       |

---

## Troubleshooting

### Upgrade script fails during image pull

**Cause:** Network issue or incorrect image tag.

```bash
# Verify the tag exists on the registry
docker manifest inspect ghcr.io/yanstart/varunapoc/backend:v1.1.0

# Check Docker login
docker login ghcr.io
```

### Migration fails

**Cause:** Schema conflict or missing dependency.

```bash
# Check migration logs
docker compose --profile prod --profile monitoring --env-file .env.production logs migration

# Roll back to previous version
./scripts/rollback.sh <previous-version> <backup-file>
```

### Services not healthy after upgrade

**Cause:** Application error in the new version, missing environment variable,
or resource constraints.

```bash
# Check which services are unhealthy
docker compose --profile prod --profile monitoring --env-file .env.production ps

# Check logs of unhealthy service
docker compose --profile prod --profile monitoring --env-file .env.production logs backend

# Roll back
./scripts/rollback.sh <previous-version> <backup-file>
```

### Database restore fails

**Cause:** Corrupted backup file or version mismatch.

```bash
# Verify backup file integrity
gunzip -t backups/varuna_db_20260311_020000.sql.gz

# Try restoring to a temporary database first
docker compose exec -T db psql -U varuna -d postgres \
    -c "CREATE DATABASE varuna_test OWNER varuna;"
gunzip -c backups/varuna_db_20260311_020000.sql.gz | \
    docker compose exec -T db psql -U varuna -d varuna_test --quiet
```
