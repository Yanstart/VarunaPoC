#!/usr/bin/env bash
# VarunaPoC Phase 1 Stop Script
#
# Purpose: Clean shutdown of Phase 1 Docker deployment
# Usage: ./stop-phase1.sh [OPTIONS]
#
# Options:
#   --clean     Remove containers and images (full cleanup)
#   --volumes   Also remove volumes (WARNING: deletes cached data)
#
# Examples:
#   ./stop-phase1.sh                 # Stop containers only
#   ./stop-phase1.sh --clean         # Stop and remove containers + images
#   ./stop-phase1.sh --clean --volumes  # Full cleanup including volumes

set -euo pipefail

# ============================================
# Color codes for output
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Configuration
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.phase1.yml"

# Parse command line options
REMOVE_IMAGES=false
REMOVE_VOLUMES=false

for arg in "$@"; do
    case $arg in
        --clean)
            REMOVE_IMAGES=true
            shift
            ;;
        --volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Usage: $0 [--clean] [--volumes]"
            exit 1
            ;;
    esac
done

# ============================================
# Helper Functions
# ============================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ============================================
# Validate Environment
# ============================================

print_header "Stopping VarunaPoC Phase 1"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

# Check if compose file exists
if [ ! -f "${COMPOSE_FILE}" ]; then
    print_error "Docker Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

cd "${PROJECT_ROOT}"

# ============================================
# Check Container Status
# ============================================

print_info "Checking container status..."

# Check if containers are running
BACKEND_RUNNING=$(docker ps -q -f name=varuna-backend-phase1 || echo "")
FRONTEND_RUNNING=$(docker ps -q -f name=varuna-frontend-phase1 || echo "")

if [ -z "${BACKEND_RUNNING}" ] && [ -z "${FRONTEND_RUNNING}" ]; then
    print_warning "No Phase 1 containers are currently running"
else
    if [ -n "${BACKEND_RUNNING}" ]; then
        print_info "Backend container is running"
    fi
    if [ -n "${FRONTEND_RUNNING}" ]; then
        print_info "Frontend container is running"
    fi
fi

# ============================================
# Stop Services
# ============================================

print_header "Stopping Services"

print_info "Stopping containers..."
if docker-compose -f "${COMPOSE_FILE}" stop; then
    print_success "Containers stopped"
else
    print_error "Failed to stop containers"
    exit 1
fi

# ============================================
# Remove Containers
# ============================================

print_info "Removing containers..."
if docker-compose -f "${COMPOSE_FILE}" rm -f; then
    print_success "Containers removed"
else
    print_error "Failed to remove containers"
    exit 1
fi

# ============================================
# Optional: Remove Images
# ============================================

if [ "${REMOVE_IMAGES}" = true ]; then
    print_header "Removing Images"

    print_info "Removing backend image..."
    BACKEND_IMAGE=$(docker images -q varunapoc-backend || echo "")
    if [ -n "${BACKEND_IMAGE}" ]; then
        if docker rmi "${BACKEND_IMAGE}"; then
            print_success "Backend image removed"
        else
            print_warning "Failed to remove backend image (may be in use)"
        fi
    else
        print_info "Backend image not found (already removed)"
    fi

    print_info "Removing frontend image..."
    FRONTEND_IMAGE=$(docker images -q varunapoc-frontend || echo "")
    if [ -n "${FRONTEND_IMAGE}" ]; then
        if docker rmi "${FRONTEND_IMAGE}"; then
            print_success "Frontend image removed"
        else
            print_warning "Failed to remove frontend image (may be in use)"
        fi
    else
        print_info "Frontend image not found (already removed)"
    fi

    # Clean up dangling images
    print_info "Cleaning up dangling images..."
    DANGLING=$(docker images -f "dangling=true" -q || echo "")
    if [ -n "${DANGLING}" ]; then
        docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true
        print_success "Dangling images cleaned up"
    else
        print_info "No dangling images to clean"
    fi
fi

# ============================================
# Optional: Remove Volumes
# ============================================

if [ "${REMOVE_VOLUMES}" = true ]; then
    print_header "Removing Volumes"

    print_warning "This will remove all cached data!"
    read -p "Are you sure? (yes/no): " -r
    echo

    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        print_info "Removing volumes..."
        if docker-compose -f "${COMPOSE_FILE}" down -v; then
            print_success "Volumes removed"
        else
            print_error "Failed to remove volumes"
        fi
    else
        print_info "Volume removal cancelled"
    fi
fi

# ============================================
# Optional: Remove Network
# ============================================

print_info "Checking for Phase 1 network..."
NETWORK_EXISTS=$(docker network ls -q -f name=varuna-phase1-network || echo "")

if [ -n "${NETWORK_EXISTS}" ]; then
    print_info "Removing Phase 1 network..."
    if docker network rm varuna-phase1-network 2>/dev/null; then
        print_success "Network removed"
    else
        print_warning "Network could not be removed (may still be in use)"
    fi
else
    print_info "Network already removed"
fi

# ============================================
# Success Summary
# ============================================

print_header "Cleanup Complete"

echo ""
print_success "VarunaPoC Phase 1 has been stopped"
echo ""

if [ "${REMOVE_IMAGES}" = true ]; then
    print_info "Images have been removed"
fi

if [ "${REMOVE_VOLUMES}" = true ]; then
    print_info "Volumes have been removed"
fi

echo ""
echo -e "${BLUE}Current Docker Status:${NC}"
echo ""
echo -e "${YELLOW}Containers:${NC}"
docker ps -a --filter "name=varuna" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "No VarunaPoC containers found"
echo ""

echo -e "${YELLOW}Images:${NC}"
docker images --filter "reference=varunapoc*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" || echo "No VarunaPoC images found"
echo ""

echo -e "${BLUE}To restart:${NC}"
echo -e "  ${YELLOW}./Scripts/Deployment/deploy-phase1.sh${NC}"
echo ""

exit 0
