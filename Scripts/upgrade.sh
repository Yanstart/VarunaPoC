#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# VarunaPoC - Upgrade Script
# =============================================================================
# Upgrades VarunaPoC to a specified version tag.
#
# Steps:
#   1. Pre-upgrade validation (compose file, env, running services)
#   2. Backup database via scripts/backup.sh
#   3. Pull new images for the target version
#   4. Apply database migrations
#   5. Recreate services with new images
#   6. Verify health checks
#
# Usage:
#   ./scripts/upgrade.sh v1.1.0
#   ./scripts/upgrade.sh v1.1.0 --skip-backup   # Skip DB backup (not recommended)
#
# Rollback:
#   If the upgrade fails, use scripts/rollback.sh to restore the previous state.
# =============================================================================

# -- Parse arguments ----------------------------------------------------------
SKIP_BACKUP=false
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 <version-tag> [--skip-backup]"
            echo ""
            echo "Arguments:"
            echo "  version-tag     Target version (e.g., v1.1.0)"
            echo ""
            echo "Options:"
            echo "  --skip-backup   Skip database backup before upgrade (not recommended)"
            echo "  -h, --help      Show this help message"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            if [ -z "$VERSION" ]; then
                VERSION="$1"
            else
                echo "Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version-tag> [--skip-backup]" >&2
    echo "Example: $0 v1.1.0" >&2
    exit 1
fi

# -- Configuration ------------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.production.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_SCRIPT="${PROJECT_ROOT}/scripts/backup.sh"
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
echo "  VarunaPoC - Upgrade to ${VERSION}"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================================="
echo ""

# -- Preflight checks --------------------------------------------------------
log_info "Running pre-upgrade checks..."

if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: ${ENV_FILE}"
    exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

COMPOSE_CMD="docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE}"

# Record current image tags for rollback reference
CURRENT_BACKEND_TAG="${BACKEND_IMAGE_TAG:-main}"
CURRENT_FRONTEND_TAG="${FRONTEND_IMAGE_TAG:-main}"
log_info "Current image tags: backend=${CURRENT_BACKEND_TAG}, frontend=${CURRENT_FRONTEND_TAG}"
log_info "Target version: ${VERSION}"
echo ""

# =============================================================================
# STEP 1 - Backup database
# =============================================================================
if [ "$SKIP_BACKUP" = true ]; then
    log_warn "Skipping database backup (--skip-backup). Not recommended for production."
    BACKUP_FILE="(skipped)"
else
    log_info "Step 1/5: Backing up database..."
    if [ ! -x "$BACKUP_SCRIPT" ]; then
        log_error "Backup script not found or not executable: ${BACKUP_SCRIPT}"
        log_error "Run: chmod +x ${BACKUP_SCRIPT}"
        exit 1
    fi

    BACKUP_FILE="$("$BACKUP_SCRIPT")"
    if [ $? -ne 0 ] || [ -z "$BACKUP_FILE" ]; then
        log_error "Database backup failed. Aborting upgrade."
        exit 1
    fi

    # The backup script prints the path as the last line
    BACKUP_FILE="$(echo "$BACKUP_FILE" | tail -1)"
    log_success "Database backed up to: ${BACKUP_FILE}"
fi
echo ""

# =============================================================================
# STEP 2 - Pull new images
# =============================================================================
log_info "Step 2/5: Pulling images for version ${VERSION}..."

BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/yanstart/varunapoc/backend}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-ghcr.io/yanstart/varunapoc/frontend}"

docker pull "${BACKEND_IMAGE}:${VERSION}"
docker pull "${FRONTEND_IMAGE}:${VERSION}"
log_success "Images pulled for ${VERSION}"
echo ""

# =============================================================================
# STEP 3 - Apply database migrations
# =============================================================================
log_info "Step 3/5: Applying database migrations..."

$COMPOSE_CMD run --rm \
    -e "BACKEND_IMAGE_TAG=${VERSION}" \
    migration

log_success "Database migrations applied"
echo ""

# =============================================================================
# STEP 4 - Recreate services with new images
# =============================================================================
log_info "Step 4/5: Recreating services with version ${VERSION}..."

# Export the new image tag so compose picks it up
export BACKEND_IMAGE_TAG="${VERSION}"
export FRONTEND_IMAGE_TAG="${VERSION}"

COMPOSE_CMD="docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE}"
$COMPOSE_CMD up -d --force-recreate --no-build

log_success "Services recreated with version ${VERSION}"
echo ""

# =============================================================================
# STEP 5 - Health check verification
# =============================================================================
log_info "Step 5/5: Verifying health checks (timeout: ${HEALTH_TIMEOUT}s)..."

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
    log_error "To investigate:"
    log_error "  ${COMPOSE_CMD} ps"
    log_error "  ${COMPOSE_CMD} logs <service>"
    log_error ""
    log_error "To rollback:"
    log_error "  ./scripts/rollback.sh ${CURRENT_BACKEND_TAG} ${BACKUP_FILE}"
    exit 1
fi

echo ""

# =============================================================================
# SUCCESS SUMMARY
# =============================================================================
echo "============================================================================="
echo "  Upgrade complete"
echo "============================================================================="
echo ""
log_success "VarunaPoC upgraded to version ${VERSION}"
log_info "Previous version: backend=${CURRENT_BACKEND_TAG}, frontend=${CURRENT_FRONTEND_TAG}"
log_info "Backup file: ${BACKUP_FILE}"
echo ""
log_info "Verify the application:"
HTTP_PORT_VAL="${HTTP_PORT:-80}"
echo "  Frontend:   http://localhost:${HTTP_PORT_VAL}/"
echo "  API health: http://localhost:${HTTP_PORT_VAL}/api/health"
echo ""
log_info "To rollback if issues arise:"
echo "  ./scripts/rollback.sh ${CURRENT_BACKEND_TAG} ${BACKUP_FILE}"
echo ""
