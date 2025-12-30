#!/bin/bash

# VarunaPoC - Phase 2.2 Deployment Script
# =============================================================================
# Phase 2.2: Network access, CHU infrastructure slides
# Frontend: http://varun-p-01 (accessible from PC clients)
# Backend: http://varun-p-01:8000
# Slides: \\imgsv-01-p\anapath_storage_nimble (CHU network share)

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="docker-compose.phase2.2.yml"
ENV_FILE_BACKEND="backend/.env.phase2.2"
ENV_FILE_FRONTEND="frontend/.env.phase2.2"
NETWORK_SHARE_MOUNT="/mnt/chu-slides"
NETWORK_SHARE_UNC="\\\\imgsv-01-p\\anapath_storage_nimble"
SERVER_HOSTNAME="varun-p-01"
STORAGE_SERVER="imgsv-01-p"
REQUIRED_PORTS=(80 8000)

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

# Banner
echo "============================================================================="
echo "  VarunaPoC - Phase 2.2 Deployment"
echo "  Network Access + CHU Infrastructure Slides"
echo "============================================================================="
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# 1. Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi
log_success "Docker is installed and running"

# 2. Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi
log_success "Docker Compose is available"

# 3. Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $COMPOSE_FILE"
    exit 1
fi
log_success "Compose file found: $COMPOSE_FILE"

# 4. Check if environment files exist
if [ ! -f "$ENV_FILE_BACKEND" ]; then
    log_error "Backend environment file not found: $ENV_FILE_BACKEND"
    exit 1
fi
if [ ! -f "$ENV_FILE_FRONTEND" ]; then
    log_error "Frontend environment file not found: $ENV_FILE_FRONTEND"
    exit 1
fi
log_success "Environment files found"

# 5. Check if network share mount point exists
log_info "Checking network share mount: $NETWORK_SHARE_MOUNT"
if [ ! -d "$NETWORK_SHARE_MOUNT" ]; then
    log_error "Network share mount point does not exist: $NETWORK_SHARE_MOUNT"
    log_info "Create mount point:"
    log_info "  Linux: sudo mkdir -p $NETWORK_SHARE_MOUNT"
    log_info "  Windows: mkdir C:\\mnt\\chu-slides"
    exit 1
fi

# 6. Check if network share is mounted and accessible
if [ ! -r "$NETWORK_SHARE_MOUNT" ]; then
    log_error "Cannot read network share mount: $NETWORK_SHARE_MOUNT"
    log_error "Network share may not be mounted or insufficient permissions"
    log_info ""
    log_info "Mount network share (Linux):"
    log_info "  sudo mount -t cifs -o username=USER,password=PASS,vers=3.0,uid=1000,gid=1000 \\"
    log_info "    //imgsv-01-p/anapath_storage_nimble $NETWORK_SHARE_MOUNT"
    log_info ""
    log_info "Mount network share (Windows):"
    log_info "  net use Z: \\\\imgsv-01-p\\anapath_storage_nimble /user:DOMAIN\\USERNAME PASSWORD /persistent:yes"
    log_info "  mklink /D $NETWORK_SHARE_MOUNT Z:\\"
    log_info ""
    exit 1
fi

# Check if mount point has content
SLIDE_COUNT=$(find "$NETWORK_SHARE_MOUNT" -type f \( -iname "*.mrxs" -o -iname "*.bif" -o -iname "*.tif" -o -iname "*.tiff" \) 2>/dev/null | wc -l)
if [ "$SLIDE_COUNT" -eq 0 ]; then
    log_warning "No slides found in network share: $NETWORK_SHARE_MOUNT"
    log_warning "Network share may be empty or not properly mounted"

    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    log_success "Network share accessible: $NETWORK_SHARE_MOUNT (Found $SLIDE_COUNT slides)"
fi

# 7. Check hostname resolution (server)
log_info "Checking hostname resolution: $SERVER_HOSTNAME"
if ! ping -c 1 -W 2 "$SERVER_HOSTNAME" &> /dev/null; then
    log_warning "Cannot ping $SERVER_HOSTNAME"
    log_warning "Ensure DNS or /etc/hosts entry exists for $SERVER_HOSTNAME"

    if ! getent hosts "$SERVER_HOSTNAME" &> /dev/null; then
        log_error "Hostname $SERVER_HOSTNAME does not resolve"
        log_info "Add to /etc/hosts (Linux) or C:\\Windows\\System32\\drivers\\etc\\hosts (Windows):"
        log_info "  <SERVER_IP>  $SERVER_HOSTNAME"

        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    log_success "Hostname $SERVER_HOSTNAME is reachable"
fi

# 8. Check storage server accessibility
log_info "Checking storage server accessibility: $STORAGE_SERVER"
if ! ping -c 1 -W 2 "$STORAGE_SERVER" &> /dev/null; then
    log_warning "Cannot ping storage server: $STORAGE_SERVER"
    log_warning "Ensure network connectivity to CHU storage infrastructure"

    if ! getent hosts "$STORAGE_SERVER" &> /dev/null; then
        log_error "Storage server $STORAGE_SERVER does not resolve"
        log_info "Add to /etc/hosts or check DNS configuration"

        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    log_success "Storage server $STORAGE_SERVER is reachable"
fi

# 9. Check if required ports are available
log_info "Checking required ports availability..."
for port in "${REQUIRED_PORTS[@]}"; do
    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        log_warning "Port $port is already in use"
        log_info "Checking if it's our container..."

        CONTAINER=$(docker ps --filter "publish=$port" --format "{{.Names}}" 2>/dev/null || true)
        if [ -n "$CONTAINER" ]; then
            log_warning "Port $port is used by container: $CONTAINER"
            log_info "This may be from a previous deployment. Continuing..."
        else
            log_error "Port $port is in use by another process"
            log_info "Check with: sudo netstat -tulnp | grep :$port (Linux) or netstat -ano | findstr :$port (Windows)"

            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_success "Port $port is available"
    fi
done

# 10. Check firewall status (informational)
log_info "Firewall check (informational)..."
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        log_warning "UFW firewall is active"
        log_info "Ensure ports 80, 8000, and 445 (SMB) are allowed:"
        log_info "  sudo ufw allow 80/tcp"
        log_info "  sudo ufw allow 8000/tcp"
        log_info "  sudo ufw allow 445/tcp"
    fi
elif command -v firewall-cmd &> /dev/null; then
    if sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
        log_warning "Firewalld is active"
        log_info "Ensure ports 80, 8000, and 445 (SMB) are allowed:"
        log_info "  sudo firewall-cmd --permanent --add-port=80/tcp"
        log_info "  sudo firewall-cmd --permanent --add-port=8000/tcp"
        log_info "  sudo firewall-cmd --permanent --add-service=samba"
        log_info "  sudo firewall-cmd --reload"
    fi
fi

# Pre-deployment summary
echo ""
echo "============================================================================="
echo "  Pre-Deployment Summary"
echo "============================================================================="
echo "  Compose File:     $COMPOSE_FILE"
echo "  Network Share:    $NETWORK_SHARE_UNC"
echo "  Mount Point:      $NETWORK_SHARE_MOUNT ($SLIDE_COUNT slides found)"
echo "  Server Hostname:  $SERVER_HOSTNAME"
echo "  Storage Server:   $STORAGE_SERVER"
echo "  Frontend URL:     http://$SERVER_HOSTNAME"
echo "  Backend URL:      http://$SERVER_HOSTNAME:8000"
echo "  Ports:            80 (frontend), 8000 (backend), 445 (SMB)"
echo "============================================================================="
echo ""

read -p "Proceed with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Deployment cancelled by user"
    exit 0
fi

# Stop existing containers
log_info "Stopping existing Phase 2.2 containers (if any)..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
log_success "Existing containers stopped"

# Build images
log_info "Building Docker images..."
if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
    log_success "Docker images built successfully"
else
    log_error "Failed to build Docker images"
    exit 1
fi

# Start containers
log_info "Starting Phase 2.2 containers..."
if docker-compose -f "$COMPOSE_FILE" up -d; then
    log_success "Containers started successfully"
else
    log_error "Failed to start containers"
    exit 1
fi

# Wait for services to be healthy
log_info "Waiting for services to be healthy (max 90 seconds - network latency)..."
TIMEOUT=90
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    BACKEND_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' varuna-backend-phase2.2 2>/dev/null || echo "starting")
    FRONTEND_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' varuna-frontend-phase2.2 2>/dev/null || echo "starting")

    if [ "$BACKEND_HEALTHY" = "healthy" ] && [ "$FRONTEND_HEALTHY" = "healthy" ]; then
        log_success "All services are healthy"
        break
    fi

    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done
echo ""

if [ $ELAPSED -ge $TIMEOUT ]; then
    log_warning "Health check timeout reached. Services may still be starting."
    log_info "Network latency may cause slower startup. Check logs:"
    log_info "  docker-compose -f $COMPOSE_FILE logs"
fi

# Post-deployment tests
echo ""
log_info "Running post-deployment tests..."

# Test 1: Backend health check (localhost)
log_info "Test 1: Backend health check (localhost)..."
if curl -f -s http://localhost:8000/api/health > /dev/null; then
    log_success "Backend health check passed (localhost)"
else
    log_error "Backend health check failed (localhost)"
    log_info "Check logs: docker logs varuna-backend-phase2.2"
fi

# Test 2: Frontend access (localhost)
log_info "Test 2: Frontend access (localhost)..."
if curl -f -s http://localhost:80 > /dev/null; then
    log_success "Frontend accessible (localhost)"
else
    log_error "Frontend not accessible (localhost)"
    log_info "Check logs: docker logs varuna-frontend-phase2.2"
fi

# Test 3: Backend health check (network hostname)
log_info "Test 3: Backend health check (network hostname: $SERVER_HOSTNAME)..."
if curl -f -s http://$SERVER_HOSTNAME:8000/api/health > /dev/null 2>&1; then
    log_success "Backend accessible via network hostname"
else
    log_warning "Cannot access backend via network hostname: http://$SERVER_HOSTNAME:8000"
    log_info "This may be a DNS or firewall issue. Test from PC client."
fi

# Test 4: Slides API (network share)
log_info "Test 4: Slides API (network share access)..."
SLIDES_RESPONSE=$(curl -s http://localhost:8000/api/slides/ 2>/dev/null || echo "")
if [ -n "$SLIDES_RESPONSE" ]; then
    log_success "Slides API responding (network share accessible)"
else
    log_warning "Slides API returned empty response"
    log_info "Check if network share is properly mounted in container"
    log_info "Verify with: docker exec varuna-backend-phase2.2 ls -la /slides"
fi

# Test 5: Network share mount verification
log_info "Test 5: Verifying network share mount in container..."
CONTAINER_SLIDE_COUNT=$(docker exec varuna-backend-phase2.2 find /slides -type f \( -iname "*.mrxs" -o -iname "*.bif" -o -iname "*.tif" -o -iname "*.tiff" \) 2>/dev/null | wc -l || echo "0")
if [ "$CONTAINER_SLIDE_COUNT" -gt 0 ]; then
    log_success "Network share mounted in container: $CONTAINER_SLIDE_COUNT slides accessible"
else
    log_error "No slides accessible in container"
    log_info "Check volume mount in docker-compose.phase2.2.yml"
    log_info "Verify host mount: ls -la $NETWORK_SHARE_MOUNT"
fi

# Display container status
echo ""
log_info "Container status:"
docker-compose -f "$COMPOSE_FILE" ps

# Deployment complete
echo ""
echo "============================================================================="
echo "  Phase 2.2 Deployment Complete"
echo "============================================================================="
log_success "Frontend: http://$SERVER_HOSTNAME"
log_success "Backend:  http://$SERVER_HOSTNAME:8000"
log_success "API Docs: http://$SERVER_HOSTNAME:8000/docs"
log_success "Slides:   $NETWORK_SHARE_UNC → $NETWORK_SHARE_MOUNT"
echo ""
echo "Next Steps:"
echo "  1. Test from PC client:"
echo "     - Open browser: http://$SERVER_HOSTNAME"
echo "     - Check API: curl http://$SERVER_HOSTNAME:8000/api/health"
echo ""
echo "  2. If network access fails:"
echo "     - Check firewall (ports 80, 8000, 445)"
echo "     - Check DNS/hosts file for $SERVER_HOSTNAME and $STORAGE_SERVER"
echo "     - Check VLAN configuration"
echo "     - Check SMB/CIFS connectivity"
echo "     - See docs/Deployment/NETWORK_TROUBLESHOOTING.md"
echo ""
echo "  3. If slides not loading:"
echo "     - Verify network share mount: ls -la $NETWORK_SHARE_MOUNT"
echo "     - Check container mount: docker exec varuna-backend-phase2.2 ls /slides"
echo "     - Check SMB credentials and permissions"
echo ""
echo "  4. View logs:"
echo "     docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "  5. Stop deployment:"
echo "     ./Scripts/Deployment/stop-phase2.2.sh"
echo "============================================================================="
