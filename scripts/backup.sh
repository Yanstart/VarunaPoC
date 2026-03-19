#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# VarunaPoC - Database Backup Script
# =============================================================================
# Creates a PostgreSQL dump of the Varuna database from the running
# Docker Compose production stack.
#
# Usage:
#   ./scripts/backup.sh                     # Backup to default directory
#   ./scripts/backup.sh /path/to/backups    # Backup to custom directory
#
# Output:
#   Prints the absolute path of the created backup file to stdout (last line).
# =============================================================================

# -- Configuration ------------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_DIR="${1:-${PROJECT_ROOT}/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# -- Colors -------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}    $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $1" >&2; }

# -- Preflight ----------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
    log_error "$ENV_FILE not found. Cannot determine database credentials."
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

POSTGRES_USER="${POSTGRES_USER:-varuna}"
POSTGRES_DB="${POSTGRES_DB:-varuna}"

# Compose command
COMPOSE_CMD="docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE}"

# Verify the db container is running
if ! $COMPOSE_CMD ps db --format '{{.State}}' 2>/dev/null | grep -q "running"; then
    log_error "Database container is not running. Start services first."
    exit 1
fi

# -- Create backup directory --------------------------------------------------
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="${BACKUP_DIR}/varuna_db_${TIMESTAMP}.sql.gz"

# -- Dump database ------------------------------------------------------------
log_info "Backing up database '${POSTGRES_DB}' ..."
$COMPOSE_CMD exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --no-owner --no-acl | gzip > "$BACKUP_FILE"

if [ ! -s "$BACKUP_FILE" ]; then
    log_error "Backup file is empty. pg_dump may have failed."
    rm -f "$BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log_info "Backup complete: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Print path so callers can capture it
echo "$BACKUP_FILE"
