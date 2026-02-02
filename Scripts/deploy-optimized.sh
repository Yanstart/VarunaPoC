#!/bin/bash
# VarunaPoC - Deployment Script (Phase 2.5 Optimized)
# Automated deployment with pre-flight checks
# Version: 1.0
# Date: 2025-12-31

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.optimized.yml"
ENV_FILE="${PROJECT_DIR}/backend/.env.production"
SLIDES_MOUNT="/mnt/chu-slides"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

log_info "Starting VarunaPoC deployment pre-flight checks..."

# Check Docker
check_command docker
DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
log_info "Docker version: $DOCKER_VERSION"

# Check docker-compose
check_command docker-compose
COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
log_info "Docker Compose version: $COMPOSE_VERSION"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]] && ! groups | grep -q docker; then
    log_error "This script requires root privileges or Docker group membership"
    log_info "Run with: sudo $0 or add user to docker group"
    exit 1
fi

# Check if slides directory is mounted
if [ ! -d "$SLIDES_MOUNT" ]; then
    log_warn "Slides directory not found at $SLIDES_MOUNT"
    log_warn "Please mount NAS storage: sudo mount -t cifs //imgsv-01-p/anapath_storage_nimble $SLIDES_MOUNT"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    log_info "Slides directory mounted at $SLIDES_MOUNT"
    SLIDE_COUNT=$(find "$SLIDES_MOUNT" -type f \( -name "*.mrxs" -o -name "*.bif" -o -name "*.tif" \) 2>/dev/null | wc -l)
    log_info "Found $SLIDE_COUNT slide files"
fi

# Check ports availability
REQUIRED_PORTS=(80 443 3000 9090 6379 8000)
for port in "${REQUIRED_PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warn "Port $port is already in use"
        netstat -tuln | grep ":$port "
    fi
done

# Check .env file
if [ ! -f "$ENV_FILE" ]; then
    log_warn ".env.production file not found"
    log_info "Creating from example..."
    if [ -f "${PROJECT_DIR}/backend/.env.example" ]; then
        cp "${PROJECT_DIR}/backend/.env.example" "$ENV_FILE"
        log_warn "Please edit $ENV_FILE with production values"
        exit 1
    else
        log_error "No .env.example file found"
        exit 1
    fi
else
    log_info ".env.production file exists"
fi

log_info "Pre-flight checks completed successfully"

# ============================================================================
# BUILD IMAGES
# ============================================================================

log_info "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build --no-cache

# ============================================================================
# PULL EXTERNAL IMAGES
# ============================================================================

log_info "Pulling external images..."
docker-compose -f "$COMPOSE_FILE" pull

# ============================================================================
# CREATE SSL CERTIFICATES (IF NOT EXISTS)
# ============================================================================

SSL_DIR="${PROJECT_DIR}/nginx/ssl"
if [ ! -f "$SSL_DIR/varuna.crt" ]; then
    log_warn "SSL certificates not found. Generating self-signed certificate..."
    mkdir -p "$SSL_DIR"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/varuna.key" \
        -out "$SSL_DIR/varuna.crt" \
        -subj "/C=BE/ST=Namur/L=Namur/O=CHU UCL Namur/CN=varuna.chu-ucl.be"
    log_info "Self-signed certificate created. Replace with production certificate for production use."
fi

# ============================================================================
# STOP EXISTING CONTAINERS
# ============================================================================

log_info "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true

# ============================================================================
# START SERVICES
# ============================================================================

log_info "Starting VarunaPoC services..."
docker-compose -f "$COMPOSE_FILE" up -d

# ============================================================================
# WAIT FOR SERVICES TO BE HEALTHY
# ============================================================================

log_info "Waiting for services to be healthy..."

wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$service.*healthy"; then
            log_info "$service is healthy"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "$service failed to become healthy"
    return 1
}

wait_for_service "redis"
wait_for_service "backend-1"
wait_for_service "backend-2"
wait_for_service "nginx"

# ============================================================================
# SMOKE TESTS
# ============================================================================

log_info "Running smoke tests..."

# Test backend health
if curl -f -s http://localhost/api/health > /dev/null; then
    log_info "Backend health check: OK"
else
    log_error "Backend health check: FAILED"
    docker-compose -f "$COMPOSE_FILE" logs backend-1
    exit 1
fi

# Test Redis
if docker exec varuna-redis redis-cli ping | grep -q PONG; then
    log_info "Redis connectivity: OK"
else
    log_error "Redis connectivity: FAILED"
    exit 1
fi

# Test Grafana
if curl -f -s http://localhost:3000/api/health > /dev/null; then
    log_info "Grafana health check: OK"
else
    log_warn "Grafana health check: FAILED (may take longer to start)"
fi

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

echo ""
log_info "================================================================"
log_info "VarunaPoC deployment completed successfully!"
log_info "================================================================"
echo ""
log_info "Services:"
log_info "  - Frontend:      http://localhost"
log_info "  - Backend API:   http://localhost/api"
log_info "  - Grafana:       http://localhost:3000 (admin/admin)"
log_info "  - Prometheus:    http://localhost:9090"
echo ""
log_info "Container status:"
docker-compose -f "$COMPOSE_FILE" ps
echo ""
log_info "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
log_info "To stop:      docker-compose -f $COMPOSE_FILE down"
echo ""
log_warn "IMPORTANT: Change Grafana admin password on first login!"
log_warn "IMPORTANT: Replace self-signed SSL certificate with production certificate!"
echo ""
