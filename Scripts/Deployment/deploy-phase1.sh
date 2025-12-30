#!/usr/bin/env bash
# VarunaPoC Phase 1 Deployment Script
#
# Purpose: Automated deployment for local validation testing
# Usage: ./deploy-phase1.sh
#
# This script:
# 1. Validates prerequisites (Docker, slides directory)
# 2. Builds Docker images
# 3. Starts services with health checks
# 4. Runs smoke tests
# 5. Displays access URLs

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
SLIDES_DIR="${PROJECT_ROOT}/Slides"
MAX_WAIT_TIME=120  # Maximum seconds to wait for services
HEALTH_CHECK_INTERVAL=5  # Seconds between health checks

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

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

rollback() {
    print_error "Deployment failed! Rolling back..."
    cd "${PROJECT_ROOT}"
    docker-compose -f "${COMPOSE_FILE}" down
    exit 1
}

# ============================================
# Prerequisite Checks
# ============================================

print_header "Phase 1: Prerequisite Checks"

# Check Docker
if ! check_command docker; then
    print_error "Docker is required. Please install Docker Desktop or Docker Engine."
    print_info "Download: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check Docker Compose
if ! check_command docker-compose && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is required."
    print_info "Docker Desktop includes Docker Compose."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

print_success "Docker is running"

# Check slides directory exists
if [ ! -d "${SLIDES_DIR}" ]; then
    print_error "Slides directory not found: ${SLIDES_DIR}"
    print_info "Please create the directory and add test slides:"
    print_info "  mkdir -p ${SLIDES_DIR}"
    print_info "Add .mrxs, .bif, or .tif files to this directory"
    exit 1
fi

print_success "Slides directory found: ${SLIDES_DIR}"

# Check if slides directory has content
MRXS_COUNT=$(find "${SLIDES_DIR}" -name "*.mrxs" 2>/dev/null | wc -l || echo 0)
BIF_COUNT=$(find "${SLIDES_DIR}" -name "*.bif" 2>/dev/null | wc -l || echo 0)
TIF_COUNT=$(find "${SLIDES_DIR}" -name "*.tif" -o -name "*.tiff" 2>/dev/null | wc -l || echo 0)

TOTAL_SLIDES=$((MRXS_COUNT + BIF_COUNT + TIF_COUNT))

if [ "${TOTAL_SLIDES}" -eq 0 ]; then
    print_warning "No slides found in ${SLIDES_DIR}"
    print_warning "Supported formats: .mrxs, .bif, .tif"
    print_info "Continuing anyway (you can test with empty directory)..."
else
    print_success "Found ${TOTAL_SLIDES} slide(s): ${MRXS_COUNT} MRXS, ${BIF_COUNT} BIF, ${TIF_COUNT} TIF"
fi

# Check compose file exists
if [ ! -f "${COMPOSE_FILE}" ]; then
    print_error "Docker Compose file not found: ${COMPOSE_FILE}"
    exit 1
fi

print_success "Docker Compose file found"

# ============================================
# Build Phase
# ============================================

print_header "Phase 2: Building Docker Images"

cd "${PROJECT_ROOT}"

print_info "Building backend image..."
if docker-compose -f "${COMPOSE_FILE}" build backend; then
    print_success "Backend image built successfully"
else
    print_error "Failed to build backend image"
    exit 1
fi

print_info "Building frontend image..."
if docker-compose -f "${COMPOSE_FILE}" build frontend; then
    print_success "Frontend image built successfully"
else
    print_error "Failed to build frontend image"
    exit 1
fi

# ============================================
# Deployment Phase
# ============================================

print_header "Phase 3: Starting Services"

print_info "Starting containers..."
if docker-compose -f "${COMPOSE_FILE}" up -d; then
    print_success "Containers started"
else
    print_error "Failed to start containers"
    exit 1
fi

# ============================================
# Health Check Phase
# ============================================

print_header "Phase 4: Waiting for Services"

# Function to check if service is healthy
check_service_health() {
    local service_name=$1
    local url=$2

    if curl -f -s "${url}" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Wait for backend
print_info "Waiting for backend to be healthy..."
ELAPSED=0
while [ ${ELAPSED} -lt ${MAX_WAIT_TIME} ]; do
    if check_service_health "backend" "http://localhost:8000/api/health"; then
        print_success "Backend is healthy"
        break
    fi

    if [ ${ELAPSED} -eq ${MAX_WAIT_TIME} ]; then
        print_error "Backend health check timeout after ${MAX_WAIT_TIME}s"
        print_info "Checking logs..."
        docker-compose -f "${COMPOSE_FILE}" logs backend
        rollback
    fi

    echo -n "."
    sleep ${HEALTH_CHECK_INTERVAL}
    ELAPSED=$((ELAPSED + HEALTH_CHECK_INTERVAL))
done

# Wait for frontend
print_info "Waiting for frontend to be healthy..."
ELAPSED=0
while [ ${ELAPSED} -lt ${MAX_WAIT_TIME} ]; do
    if check_service_health "frontend" "http://localhost:80/"; then
        print_success "Frontend is healthy"
        break
    fi

    if [ ${ELAPSED} -eq ${MAX_WAIT_TIME} ]; then
        print_error "Frontend health check timeout after ${MAX_WAIT_TIME}s"
        print_info "Checking logs..."
        docker-compose -f "${COMPOSE_FILE}" logs frontend
        rollback
    fi

    echo -n "."
    sleep ${HEALTH_CHECK_INTERVAL}
    ELAPSED=$((ELAPSED + HEALTH_CHECK_INTERVAL))
done

# ============================================
# Smoke Tests
# ============================================

print_header "Phase 5: Running Smoke Tests"

# Test 1: Backend health endpoint
print_info "Test 1: Backend health check"
if curl -f -s http://localhost:8000/api/health | grep -q "healthy"; then
    print_success "Backend health endpoint OK"
else
    print_error "Backend health endpoint failed"
    rollback
fi

# Test 2: Backend root endpoint
print_info "Test 2: Backend root endpoint"
if curl -f -s http://localhost:8000/ | grep -q "VarunaPoC Backend"; then
    print_success "Backend root endpoint OK"
else
    print_error "Backend root endpoint failed"
    rollback
fi

# Test 3: Frontend loads
print_info "Test 3: Frontend loads"
if curl -f -s http://localhost:80/ | grep -q "html"; then
    print_success "Frontend loads OK"
else
    print_error "Frontend failed to load"
    rollback
fi

# Test 4: API documentation available
print_info "Test 4: API documentation"
if curl -f -s http://localhost:8000/docs > /dev/null; then
    print_success "API documentation available"
else
    print_warning "API documentation not accessible (non-critical)"
fi

# ============================================
# Success Summary
# ============================================

print_header "Deployment Successful!"

echo ""
print_success "VarunaPoC Phase 1 is now running!"
echo ""

echo -e "${GREEN}Access URLs:${NC}"
echo -e "  ${BLUE}Frontend:${NC}      http://localhost"
echo -e "  ${BLUE}Backend API:${NC}   http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}      http://localhost:8000/docs"
echo ""

echo -e "${GREEN}Container Status:${NC}"
docker-compose -f "${COMPOSE_FILE}" ps
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:          ${YELLOW}docker-compose -f ${COMPOSE_FILE} logs -f${NC}"
echo -e "  View backend logs:  ${YELLOW}docker-compose -f ${COMPOSE_FILE} logs -f backend${NC}"
echo -e "  View frontend logs: ${YELLOW}docker-compose -f ${COMPOSE_FILE} logs -f frontend${NC}"
echo -e "  Stop services:      ${YELLOW}./Scripts/Deployment/stop-phase1.sh${NC}"
echo ""

print_info "Slide detection: Navigate to http://localhost and browse ${SLIDES_DIR}"
echo ""

exit 0
