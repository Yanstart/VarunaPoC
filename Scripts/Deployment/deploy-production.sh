#!/bin/bash

# VarunaPoC - Production Deployment Script
# =============================================================================
# Unified production deployment with profile support (auth, monitoring).
# Usage:
#   ./Scripts/Deployment/deploy-production.sh              # Core services only
#   ./Scripts/Deployment/deploy-production.sh --profile auth
#   ./Scripts/Deployment/deploy-production.sh --profile monitoring
#   ./Scripts/Deployment/deploy-production.sh --all        # All profiles
#   ./Scripts/Deployment/deploy-production.sh --pull       # Pull images first
#   ./Scripts/Deployment/deploy-production.sh --build      # Build from source

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.production"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-120}"

# Parsed arguments
PROFILES=()
DO_PULL=false
DO_BUILD=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILES+=("$2")
            shift 2
            ;;
        --all)
            PROFILES=("auth" "monitoring")
            shift
            ;;
        --pull)
            DO_PULL=true
            shift
            ;;
        --build)
            DO_BUILD=true
            shift
            ;;
        --timeout)
            HEALTH_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile <name>   Enable a compose profile (auth, monitoring)"
            echo "  --all              Enable all profiles (auth + monitoring)"
            echo "  --pull             Pull latest images before starting"
            echo "  --build            Build images from source instead of pulling"
            echo "  --timeout <secs>   Health check timeout (default: 120)"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build compose command with profiles
COMPOSE_CMD="docker compose -f $COMPOSE_FILE --env-file $ENV_FILE"
for profile in "${PROFILES[@]}"; do
    COMPOSE_CMD="$COMPOSE_CMD --profile $profile"
done

# Banner
echo "============================================================================="
echo "  VarunaPoC - Production Deployment"
echo "  Unified deployment for hospital environments"
echo "============================================================================="
echo ""
if [ ${#PROFILES[@]} -gt 0 ]; then
    log_info "Profiles: ${PROFILES[*]}"
else
    log_info "Profiles: core only (no optional profiles)"
fi
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# =============================================================================
# PRE-DEPLOYMENT CHECKS
# =============================================================================
log_info "Running pre-deployment checks..."

# 1. Docker version check (24+)
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker 24+."
    exit 1
fi

DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0")
DOCKER_MAJOR=$(echo "$DOCKER_VERSION" | cut -d. -f1)
if [ "$DOCKER_MAJOR" -lt 24 ] 2>/dev/null; then
    log_warning "Docker version $DOCKER_VERSION detected. Recommended: 24+."
else
    log_success "Docker $DOCKER_VERSION installed"
fi

# 2. Docker Compose V2 check
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose V2 is not available. Please install docker-compose-plugin."
    exit 1
fi
log_success "Docker Compose V2 available"

# 3. Environment file check
if [ ! -f "$ENV_FILE" ]; then
    log_error "$ENV_FILE not found. Create it from the template:"
    log_error "  cp .env.production.example .env.production"
    log_error "  # Then fill in POSTGRES_PASSWORD, REDIS_PASSWORD, etc."
    exit 1
fi
log_success "$ENV_FILE found"

# 4. Compose file check
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "$COMPOSE_FILE not found. Are you in the project root?"
    exit 1
fi
log_success "$COMPOSE_FILE found"

# 5. Required variables check
source "$ENV_FILE"
MISSING_VARS=()
if [ -z "$POSTGRES_PASSWORD" ]; then
    MISSING_VARS+=("POSTGRES_PASSWORD")
fi
if [ -z "$REDIS_PASSWORD" ]; then
    MISSING_VARS+=("REDIS_PASSWORD")
fi

# Check profile-specific variables
for profile in "${PROFILES[@]}"; do
    case $profile in
        auth)
            [ -z "$KEYCLOAK_ADMIN_PASSWORD" ] && MISSING_VARS+=("KEYCLOAK_ADMIN_PASSWORD")
            [ -z "$KEYCLOAK_DB_PASSWORD" ] && MISSING_VARS+=("KEYCLOAK_DB_PASSWORD")
            ;;
        monitoring)
            [ -z "$GRAFANA_ADMIN_PASSWORD" ] && MISSING_VARS+=("GRAFANA_ADMIN_PASSWORD")
            ;;
    esac
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log_error "Required variables not set in $ENV_FILE:"
    for var in "${MISSING_VARS[@]}"; do
        log_error "  - $var"
    done
    exit 1
fi
log_success "Required environment variables set"

# 6. Port availability check
HTTP_PORT_VAL="${HTTP_PORT:-80}"
HTTPS_PORT_VAL="${HTTPS_PORT:-443}"
REQUIRED_PORTS=("$HTTP_PORT_VAL" "$HTTPS_PORT_VAL")

for profile in "${PROFILES[@]}"; do
    case $profile in
        auth) REQUIRED_PORTS+=("8180") ;;
        monitoring) REQUIRED_PORTS+=("9090" "3000") ;;
    esac
done

for port in "${REQUIRED_PORTS[@]}"; do
    if ss -tlnp 2>/dev/null | grep -q ":${port} " || \
       netstat -tlnp 2>/dev/null | grep -q ":${port} "; then
        # Check if it's our own container using the port
        if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps 2>/dev/null | grep -q "0.0.0.0:${port}"; then
            log_info "Port $port in use by existing VarunaPoC container (will be replaced)"
        else
            log_warning "Port $port is already in use by another process"
        fi
    fi
done
log_success "Port check completed"

# 7. Slides mount check
SLIDES_PATH="${SLIDES_HOST_PATH:-/mnt/chu-slides}"
if [ -d "$SLIDES_PATH" ]; then
    SLIDE_COUNT=$(find "$SLIDES_PATH" -maxdepth 1 -type f 2>/dev/null | head -5 | wc -l)
    log_success "Slides mount found at $SLIDES_PATH ($SLIDE_COUNT+ files)"
else
    log_warning "Slides directory $SLIDES_PATH not found. Backend will start but slides won't be available."
fi

echo ""

# =============================================================================
# PULL / BUILD IMAGES
# =============================================================================
if [ "$DO_PULL" = true ]; then
    log_info "Pulling latest images..."
    $COMPOSE_CMD pull
    log_success "Images pulled"
    echo ""
fi

if [ "$DO_BUILD" = true ]; then
    log_info "Building images from source..."
    $COMPOSE_CMD build
    log_success "Images built"
    echo ""
fi

# =============================================================================
# DEPLOY
# =============================================================================
log_info "Starting services..."
$COMPOSE_CMD up -d
log_success "Services started"
echo ""

# =============================================================================
# HEALTH CHECK LOOP
# =============================================================================
log_info "Waiting for services to become healthy (timeout: ${HEALTH_TIMEOUT}s)..."

SECONDS=0
ALL_HEALTHY=false

while [ $SECONDS -lt "$HEALTH_TIMEOUT" ]; do
    # Get service health status
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
    # Skip migration (expected to exit) and exited services
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
    log_success "All services are healthy!"
else
    log_warning "Some services may not be fully healthy yet. Check with:"
    log_warning "  $COMPOSE_CMD ps"
fi

echo ""

# =============================================================================
# SMOKE TESTS
# =============================================================================
log_info "Running smoke tests..."

SMOKE_PASS=0
SMOKE_FAIL=0

# Test health endpoint
if curl -sf "http://localhost:${HTTP_PORT_VAL}/health" > /dev/null 2>&1; then
    log_success "Nginx health check: OK"
    SMOKE_PASS=$((SMOKE_PASS + 1))
else
    log_warning "Nginx health check: FAILED (may need SSL)"
    SMOKE_FAIL=$((SMOKE_FAIL + 1))
fi

# Test API health
if curl -sf "http://localhost:${HTTP_PORT_VAL}/api/health" > /dev/null 2>&1; then
    log_success "Backend API health: OK"
    SMOKE_PASS=$((SMOKE_PASS + 1))
else
    log_warning "Backend API health: FAILED"
    SMOKE_FAIL=$((SMOKE_FAIL + 1))
fi

# Test frontend
if curl -sf "http://localhost:${HTTP_PORT_VAL}/" > /dev/null 2>&1; then
    log_success "Frontend: OK"
    SMOKE_PASS=$((SMOKE_PASS + 1))
else
    log_warning "Frontend: FAILED"
    SMOKE_FAIL=$((SMOKE_FAIL + 1))
fi

# Profile-specific tests
for profile in "${PROFILES[@]}"; do
    case $profile in
        auth)
            if curl -sf "http://localhost:8180/" > /dev/null 2>&1; then
                log_success "Keycloak: OK"
                SMOKE_PASS=$((SMOKE_PASS + 1))
            else
                log_warning "Keycloak: FAILED (may still be starting)"
                SMOKE_FAIL=$((SMOKE_FAIL + 1))
            fi
            ;;
        monitoring)
            if curl -sf "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
                log_success "Prometheus: OK"
                SMOKE_PASS=$((SMOKE_PASS + 1))
            else
                log_warning "Prometheus: FAILED"
                SMOKE_FAIL=$((SMOKE_FAIL + 1))
            fi
            if curl -sf "http://localhost:3000/api/health" > /dev/null 2>&1; then
                log_success "Grafana: OK"
                SMOKE_PASS=$((SMOKE_PASS + 1))
            else
                log_warning "Grafana: FAILED"
                SMOKE_FAIL=$((SMOKE_FAIL + 1))
            fi
            ;;
    esac
done

echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo "============================================================================="
echo "  Deployment Summary"
echo "============================================================================="
echo ""
log_info "Smoke tests: ${SMOKE_PASS} passed, ${SMOKE_FAIL} failed"
echo ""
log_info "Service URLs:"
echo "  Frontend:   http://localhost:${HTTP_PORT_VAL}/"
echo "  API:        http://localhost:${HTTP_PORT_VAL}/api/health"
echo "  HTTPS:      https://varuna.chu-ucl.be/"

for profile in "${PROFILES[@]}"; do
    case $profile in
        auth)
            echo "  Keycloak:   http://localhost:8180/"
            ;;
        monitoring)
            echo "  Prometheus: http://localhost:9090/"
            echo "  Grafana:    http://localhost:3000/ (admin/${GRAFANA_ADMIN_PASSWORD:0:3}...)"
            ;;
    esac
done

echo ""
log_info "Useful commands:"
echo "  $COMPOSE_CMD ps          # Service status"
echo "  $COMPOSE_CMD logs -f     # Follow logs"
echo "  $COMPOSE_CMD down        # Stop all services"
echo ""

if [ "$SMOKE_FAIL" -gt 0 ]; then
    log_warning "Some smoke tests failed. Check logs for details."
    exit 1
fi

log_success "Deployment complete!"
