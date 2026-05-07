#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# VarunaPoC - Rollback Script
# =============================================================================
# Rolls back VarunaPoC to a previous version and restores the database
# from a backup file.
#
# Steps:
#   1. Stop services
#   2. Restore database from backup
#   3. Pull the old version images
#   4. Restart services with old images
#   5. Verify health checks
#
# Usage:
#   ./scripts/rollback.sh <version-tag> <backup-file>
#   ./scripts/rollback.sh v1.0.0 backups/varuna_db_20260310_020000.sql.gz
#   ./scripts/rollback.sh v1.0.0 --no-db-restore   # Skip DB restore
# =============================================================================

# -- Parse arguments ----------------------------------------------------------
VERSION=""
BACKUP_FILE=""
NO_DB_RESTORE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-db-restore)
            NO_DB_RESTORE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 <version-tag> <backup-file>"
            echo "       $0 <version-tag> --no-db-restore"
            echo ""
            echo "Arguments:"
            echo "  version-tag     Version to roll back to (e.g., v1.0.0)"
            echo "  backup-file     Path to database backup (.sql.gz) created by backup.sh"
            echo ""
            echo "Options:"
            echo "  --no-db-restore   Skip database restore (only roll back images)"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            if [ -z "$VERSION" ]; then
                VERSION="$1"
            elif [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
            else
                echo "Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version-tag> <backup-file>" >&2
    echo "       $0 <version-tag> --no-db-restore" >&2
    exit 1
fi

if [ "$NO_DB_RESTORE" = false ] && [ -z "$BACKUP_FILE" ]; then
    echo "Error: backup file is required unless --no-db-restore is specified." >&2
    echo "Usage: $0 <version-tag> <backup-file>" >&2
    exit 1
fi

# -- Configuration ------------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-120}"

# -- Colors -------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC}    $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $1" >&2; }

# -- Banner -------------------------------------------------------------------
echo "============================================================================="
echo "  VarunaPoC - Rollback to ${VERSION}"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================================="
echo ""

# -- Preflight checks --------------------------------------------------------
log_info "Running pre-rollback checks..."

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: ${ENV_FILE}"
    exit 1
fi

if [ "$NO_DB_RESTORE" = false ]; then
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: ${BACKUP_FILE}"
        exit 1
    fi
    log_info "Backup file: ${BACKUP_FILE}"
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

COMPOSE_CMD="docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE}"

POSTGRES_USER="${POSTGRES_USER:-varuna}"
POSTGRES_DB="${POSTGRES_DB:-varuna}"

log_info "Target version: ${VERSION}"
echo ""

# =============================================================================
# STEP 1 - Stop services
# =============================================================================
log_info "Step 1/4: Stopping services..."

$COMPOSE_CMD down --remove-orphans || true

log_success "Services stopped"
echo ""

# =============================================================================
# STEP 2 - Restore database
# =============================================================================
if [ "$NO_DB_RESTORE" = true ]; then
    log_warn "Step 2/4: Skipping database restore (--no-db-restore)"
else
    log_info "Step 2/4: Restoring database from backup..."

    # Start only the database service for the restore
    $COMPOSE_CMD up -d db

    # Wait for database to be ready
    log_info "Waiting for database to accept connections..."
    SECONDS=0
    DB_READY=false
    while [ $SECONDS -lt 60 ]; do
        if $COMPOSE_CMD exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
            DB_READY=true
            break
        fi
        sleep 2
    done

    if [ "$DB_READY" = false ]; then
        log_error "Database did not become ready within 60 seconds."
        exit 1
    fi

    # Drop and recreate the database to ensure a clean restore
    log_info "Dropping and recreating database '${POSTGRES_DB}'..."
    $COMPOSE_CMD exec -T db psql -U "$POSTGRES_USER" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
        >/dev/null 2>&1 || true

    $COMPOSE_CMD exec -T db psql -U "$POSTGRES_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS \"${POSTGRES_DB}\";"

    $COMPOSE_CMD exec -T db psql -U "$POSTGRES_USER" -d postgres \
        -c "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";"

    # Enable PostGIS extension (required by the schema)
    $COMPOSE_CMD exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "CREATE EXTENSION IF NOT EXISTS postgis;" >/dev/null 2>&1 || true

    # Restore the backup
    log_info "Restoring backup..."
    gunzip -c "$BACKUP_FILE" | $COMPOSE_CMD exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" --quiet

    log_success "Database restored from ${BACKUP_FILE}"

    # Stop the database (it will be started again with the full stack)
    $COMPOSE_CMD down
fi
echo ""

# =============================================================================
# STEP 3 - Pull old version images
# =============================================================================
log_info "Step 3/4: Pulling images for version ${VERSION}..."

BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/yanstart/varunapoc/backend}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-ghcr.io/yanstart/varunapoc/frontend}"

docker pull "${BACKEND_IMAGE}:${VERSION}"
docker pull "${FRONTEND_IMAGE}:${VERSION}"

log_success "Images pulled for ${VERSION}"
echo ""

# =============================================================================
# STEP 4 - Restart services
# =============================================================================
log_info "Step 4/4: Starting services with version ${VERSION}..."

export BACKEND_IMAGE_TAG="${VERSION}"
export FRONTEND_IMAGE_TAG="${VERSION}"

COMPOSE_CMD="docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE}"
$COMPOSE_CMD up -d

# -- Health check verification ------------------------------------------------
log_info "Verifying health checks (timeout: ${HEALTH_TIMEOUT}s)..."

SECONDS=0
ALL_HEALTHY=false

while [ $SECONDS -lt "$HEALTH_TIMEOUT" ]; do
    UNHEALTHY=$($COMPOSE_CMD ps --format json 2>/dev/null | \
        python3 -c "
import sys, json
unhealthy = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    svc = json.loads(line)
    status = svc.get('Health', svc.get('Status', ''))
    name = svc.get('Service', svc.get('Name', ''))
    state = svc.get('State', '')
    if state == 'exited':
        continue
    if 'healthy' not in status.lower() and state == 'running':
        unhealthy.append(name)
print(','.join(unhealthy))
" 2>/dev/null || echo "unknown")

    if [ -z "$UNHEALTHY" ]; then
        ALL_HEALTHY=true
        break
    fi

    printf "\r  Waiting... %ds / %ds (pending: %s)   " "$SECONDS" "$HEALTH_TIMEOUT" "$UNHEALTHY"
    sleep 5
done

echo ""

if [ "$ALL_HEALTHY" = true ]; then
    log_success "All services are healthy"
else
    log_error "Some services did not become healthy within ${HEALTH_TIMEOUT}s"
    log_error "Pending: ${UNHEALTHY}"
    log_error ""
    log_error "Investigate with:"
    log_error "  ${COMPOSE_CMD} ps"
    log_error "  ${COMPOSE_CMD} logs <service>"
    exit 1
fi

echo ""

# =============================================================================
# SUCCESS SUMMARY
# =============================================================================
echo "============================================================================="
echo "  Rollback complete"
echo "============================================================================="
echo ""
log_success "VarunaPoC rolled back to version ${VERSION}"
if [ "$NO_DB_RESTORE" = false ]; then
    log_info "Database restored from: ${BACKUP_FILE}"
fi
echo ""
log_info "Verify the application:"
HTTP_PORT_VAL="${HTTP_PORT:-80}"
echo "  Frontend:   http://localhost:${HTTP_PORT_VAL}/"
echo "  API health: http://localhost:${HTTP_PORT_VAL}/api/health"
echo ""
