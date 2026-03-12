#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# VarunaPoC - PostgreSQL Restore Script
# ==============================================================================
# Restores a pg_dump backup into the Varuna PostgreSQL database using
# the production Docker Compose stack.
#
# Usage:
#   ./scripts/restore.sh <BACKUP_FILE>
#
# Arguments:
#   BACKUP_FILE  Path to a .dump file created by backup.sh
#
# Environment (sourced from .env.production):
#   POSTGRES_USER  Database user (default: varuna)
#   POSTGRES_DB    Database name (default: varuna)
# ==============================================================================

# --------------------------------------------------------------------------
# Usage check
# --------------------------------------------------------------------------
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <BACKUP_FILE>" >&2
    echo "" >&2
    echo "  BACKUP_FILE  Path to a .dump file created by backup.sh" >&2
    exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"

# --------------------------------------------------------------------------
# Load environment
# --------------------------------------------------------------------------
if [[ -f "${ENV_FILE}" ]]; then
    while IFS='=' read -r key value; do
        case "${key}" in
            POSTGRES_USER|POSTGRES_DB)
                value="${value#"${value%%[![:space:]]*}"}"
                value="${value%"${value##*[![:space:]]}"}"
                if [[ -n "${value}" ]]; then
                    export "${key}=${value}"
                fi
                ;;
        esac
    done < <(grep -E '^POSTGRES_(USER|DB)=' "${ENV_FILE}" 2>/dev/null || true)
fi

POSTGRES_USER="${POSTGRES_USER:-varuna}"
POSTGRES_DB="${POSTGRES_DB:-varuna}"

# --------------------------------------------------------------------------
# Validate inputs
# --------------------------------------------------------------------------
if [[ ! -f "${BACKUP_FILE}" ]]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}" >&2
    exit 1
fi

if [[ ! -s "${BACKUP_FILE}" ]]; then
    echo "ERROR: Backup file is empty: ${BACKUP_FILE}" >&2
    exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "ERROR: Compose file not found: ${COMPOSE_FILE}" >&2
    exit 1
fi

BACKUP_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"

echo "=== VarunaPoC PostgreSQL Restore ==="
echo "Database: ${POSTGRES_DB}"
echo "User:     ${POSTGRES_USER}"
echo "Source:   ${BACKUP_FILE} (${BACKUP_SIZE})"
echo ""

# --------------------------------------------------------------------------
# Confirm with user
# --------------------------------------------------------------------------
echo "WARNING: This will drop and recreate the '${POSTGRES_DB}' database."
echo "         All current data will be lost."
echo ""
read -r -p "Continue? [y/N] " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""

# --------------------------------------------------------------------------
# Stop backend to prevent connections during restore
# --------------------------------------------------------------------------
echo "Stopping backend service..."
docker compose -f "${COMPOSE_FILE}" stop backend migration || true

# --------------------------------------------------------------------------
# Drop and recreate database, then restore
# --------------------------------------------------------------------------
echo "Dropping existing database..."
docker compose -f "${COMPOSE_FILE}" exec -T db \
    psql -U "${POSTGRES_USER}" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

docker compose -f "${COMPOSE_FILE}" exec -T db \
    dropdb -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}"

echo "Creating empty database..."
docker compose -f "${COMPOSE_FILE}" exec -T db \
    createdb -U "${POSTGRES_USER}" -O "${POSTGRES_USER}" "${POSTGRES_DB}"

echo "Enabling PostGIS extension..."
docker compose -f "${COMPOSE_FILE}" exec -T db \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    -c "CREATE EXTENSION IF NOT EXISTS postgis;" > /dev/null

echo "Restoring from backup..."
if ! docker compose -f "${COMPOSE_FILE}" exec -T db \
    pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --no-owner --no-privileges \
    < "${BACKUP_FILE}"; then
    echo "WARNING: pg_restore completed with warnings (this is often normal)" >&2
fi

# --------------------------------------------------------------------------
# Restart backend
# --------------------------------------------------------------------------
echo ""
echo "Restarting backend service..."
docker compose -f "${COMPOSE_FILE}" start backend

# --------------------------------------------------------------------------
# Validate database health
# --------------------------------------------------------------------------
echo "Validating database health..."

MAX_RETRIES=10
RETRY=0
while [[ ${RETRY} -lt ${MAX_RETRIES} ]]; do
    if docker compose -f "${COMPOSE_FILE}" exec -T db \
        pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null 2>&1; then
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 2
done

if [[ ${RETRY} -ge ${MAX_RETRIES} ]]; then
    echo "ERROR: Database health check failed after ${MAX_RETRIES} retries" >&2
    exit 1
fi

# Quick validation: check that tables exist
TABLE_COUNT=$(docker compose -f "${COMPOSE_FILE}" exec -T db \
    psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t \
    -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
    | tr -d '[:space:]')

echo ""
echo "=== Restore Complete ==="
echo "Database: ${POSTGRES_DB}"
echo "Tables:   ${TABLE_COUNT} tables in public schema"
echo "Source:   ${BACKUP_FILE}"
