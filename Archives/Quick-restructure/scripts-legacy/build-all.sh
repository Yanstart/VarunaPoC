#!/bin/bash
# Build all QUICK- implementations
# Usage: ./scripts/build-all.sh [implementation]
# Example: ./scripts/build-all.sh quiche-cloudflare

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

build_quiche_cloudflare() {
    log_info "Building quiche-cloudflare (Rust)..."
    cd "$PROJECT_ROOT/deployments/docker"
    docker compose -f docker-compose.build-all.yaml build quiche-cloudflare-entry quiche-cloudflare-exit
    log_info "quiche-cloudflare build complete"
}

build_quiche_google() {
    log_info "Building quiche-google (C++ with Bazel)..."
    cd "$PROJECT_ROOT/deployments/docker"
    docker compose -f docker-compose.build-all.yaml build quiche-google
    log_info "quiche-google build complete"
}

build_msquic() {
    log_info "Building msquic (C)..."
    cd "$PROJECT_ROOT/deployments/docker"
    docker compose -f docker-compose.build-all.yaml build msquic-entry msquic-exit
    log_info "msquic build complete"
}

build_quic_go() {
    log_info "Building quic-go (Go)..."
    cd "$PROJECT_ROOT/deployments/docker"
    docker compose -f docker-compose.build-all.yaml build quic-go-entry quic-go-exit
    log_info "quic-go build complete"
}

build_all() {
    log_info "Building all implementations..."
    build_quic_go        # Reference (fastest)
    build_quiche_cloudflare  # Primary
    build_msquic         # Secondary
    build_quiche_google  # Experimental (slowest due to Bazel)
    log_info "All builds complete!"
}

# Main
case "${1:-all}" in
    quiche-cloudflare|cf)
        build_quiche_cloudflare
        ;;
    quiche-google|google)
        build_quiche_google
        ;;
    msquic|ms)
        build_msquic
        ;;
    quic-go|go)
        build_quic_go
        ;;
    all)
        build_all
        ;;
    *)
        echo "Usage: $0 [quiche-cloudflare|quiche-google|msquic|quic-go|all]"
        exit 1
        ;;
esac
