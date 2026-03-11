#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# VarunaPoC - PostgreSQL Backup Script
# ==============================================================================
# Creates a timestamped pg_dump of the Varuna PostgreSQL database using
# the production Docker Compose stack.
#
# Usage:
#   ./scripts/backup.sh [BACKUP_DIR]
#
# Arguments:
#   BACKUP_DIR  Directory to store backups (default: ./backups)
#
# Environment (sourced from .env.production):
#   POSTGRES_USER  Database user (default: varuna)
#   POSTGRES_DB    Database name (default: varuna)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"

# --------------------------------------------------------------------------
# Load environment
# --------------------------------------------------------------------------
if [[ -f "${ENV_FILE}" ]]; then
    # Source only POSTGRES_* variables (ignore lines with spaces-only values)
    while IFS='=' read -r key value; do
        case "${key}" in
            POSTGRES_USER|POSTGRES_DB)
                value="${value#"${value%%[![:space:]]*}"}"  # trim leading
                value="${value%"${value##*[![:space:]]}"}"  # trim trailing
                if [[ -n "${value}" ]]; then
                    export "${key}=${value}"
                fi
                ;;
        esac
    done < <(grep -E '^POSTGRES_(USER|DB)=' "${ENV_FILE}" 2>/dev/null || true)
fi

POSTGRES_USER="${POSTGRES_USER:-varuna}"
POSTGRES_DB="${POSTGRES_DB:-varuna}"
BACKUP_DIR="${1:-${PROJECT_ROOT}/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/varuna_${TIMESTAMP}.dump"

# --------------------------------------------------------------------------
# Validate compose file
# --------------------------------------------------------------------------
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "ERROR: Compose file not found: ${COMPOSE_FILE}" >&2
    exit 1
fi

# --------------------------------------------------------------------------
# Create backup directory
# --------------------------------------------------------------------------
mkdir -p "${BACKUP_DIR}"

echo "=== VarunaPoC PostgreSQL Backup ==="
echo "Database: ${POSTGRES_DB}"
echo "User:     ${POSTGRES_USER}"
echo "Target:   ${BACKUP_FILE}"
echo ""

# --------------------------------------------------------------------------
# Run pg_dump via docker compose exec
# --------------------------------------------------------------------------
echo "Starting backup..."

if ! docker compose -f "${COMPOSE_FILE}" exec -T db \
    pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc -Z6 \
    > "${BACKUP_FILE}"; then
    echo "ERROR: pg_dump failed" >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# --------------------------------------------------------------------------
# Validate output
# --------------------------------------------------------------------------
if [[ ! -s "${BACKUP_FILE}" ]]; then
    echo "ERROR: Backup file is empty" >&2
    rm -f "${BACKUP_FILE}"
    exit 1
fi

BACKUP_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"

echo ""
echo "=== Backup Complete ==="
echo "File: ${BACKUP_FILE}"
echo "Size: ${BACKUP_SIZE}"
