#!/bin/bash

# VarunaPoC - Phase 2.1 Stop Script
# =============================================================================
# Stops Phase 2.1 deployment (network access, local slides)

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="docker-compose.phase2.1.yml"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "============================================================================="
echo "  VarunaPoC - Phase 2.1 Stop"
echo "============================================================================="
echo ""

cd "$PROJECT_ROOT"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Stop containers
log_info "Stopping Phase 2.1 containers..."
if docker-compose -f "$COMPOSE_FILE" down; then
    log_success "Containers stopped successfully"
else
    log_error "Failed to stop containers"
    exit 1
fi

# Optional: Remove volumes (commented out by default)
# log_info "Removing volumes..."
# docker-compose -f "$COMPOSE_FILE" down -v

# Optional: Remove images (commented out by default)
# log_info "Removing images..."
# docker-compose -f "$COMPOSE_FILE" down --rmi all

echo ""
log_success "Phase 2.1 deployment stopped"
echo ""
echo "To restart deployment:"
echo "  ./Scripts/Deployment/deploy-phase2.1.sh"
echo ""
