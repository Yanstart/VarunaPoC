#!/bin/bash
# QUICK- TCP-over-QUIC Tunnel
# Demo Startup Script
# Starts the complete infrastructure for Phase 1 & 2 testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."

# Ports used by QUICK- project
QUICK_PORTS="2222 3001 8080 8443 8888 9000 9090 9091"

echo "=========================================="
echo "  QUICK- TCP-over-QUIC Tunnel"
echo "  Demo Environment Setup"
echo "=========================================="
echo ""

cd "${PROJECT_DIR}"

# =============================================================================
# Step 0: Clean up conflicting containers and free ports
# =============================================================================
echo "[0/5] Cleaning up conflicting containers and ports..."

# Stop all QUICK- related containers first
echo "  Stopping QUICK- containers..."
docker-compose down 2>/dev/null || true

# List of container name patterns that might conflict
CONFLICTING_PATTERNS=(
    "quick-"
    "quic-"
    "varuna-"
)

# Stop containers matching patterns that use our ports
for pattern in "${CONFLICTING_PATTERNS[@]}"; do
    containers=$(docker ps -a --filter "name=${pattern}" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        echo "  Stopping containers matching '${pattern}'..."
        for container in $containers; do
            # Check if container uses any of our ports
            ports_used=$(docker port "$container" 2>/dev/null || true)
            for port in $QUICK_PORTS; do
                if echo "$ports_used" | grep -q ":${port}" 2>/dev/null; then
                    echo "    Stopping $container (uses port $port)..."
                    docker stop "$container" 2>/dev/null || true
                    break
                fi
            done
        done
    fi
done

# Additional cleanup: stop any container using our specific ports
echo "  Checking for containers using required ports..."
for port in $QUICK_PORTS; do
    # Find container using this port
    container=$(docker ps --format "{{.Names}}" --filter "publish=${port}" 2>/dev/null | head -1)
    if [ -n "$container" ]; then
        echo "    Port $port is used by '$container', stopping it..."
        docker stop "$container" 2>/dev/null || true
    fi
done

# Clean up any orphaned quick- containers
echo "  Removing stopped QUICK- containers..."
docker rm $(docker ps -a --filter "name=quick-" --filter "status=exited" -q) 2>/dev/null || true
docker rm $(docker ps -a --filter "name=quick-" --filter "status=created" -q) 2>/dev/null || true

echo "  Port cleanup complete."
echo ""

# Step 1: Generate certificates if needed
if [ ! -f "certs/ca.crt" ]; then
    echo "[1/5] Generating TLS certificates..."
    chmod +x scripts/generate-certs.sh
    ./scripts/generate-certs.sh
else
    echo "[1/5] TLS certificates already exist"
fi

# Step 2: Create test files
echo "[2/5] Creating test files..."
mkdir -p test-files
if [ ! -f "test-files/large.bin" ]; then
    dd if=/dev/urandom of=test-files/large.bin bs=1M count=10 2>/dev/null
    echo "  Created large.bin (10 MB)"
fi
if [ ! -f "test-files/benchmark.bin" ]; then
    dd if=/dev/urandom of=test-files/benchmark.bin bs=1M count=10 2>/dev/null
    echo "  Created benchmark.bin (10 MB)"
fi

# Step 3: Build and start Docker containers
echo "[3/5] Starting Docker containers..."

# Determine which profile to use (default: go)
PROFILE="${TUNNEL_PROFILE:-go}"
echo "  Using tunnel implementation: $PROFILE"

docker-compose --profile "$PROFILE" build --parallel
docker-compose --profile "$PROFILE" up -d

# Step 4: Wait for services
echo "[4/5] Waiting for services to be ready..."
sleep 10

# Verify services
echo ""
echo "=========================================="
echo "  Service Status"
echo "=========================================="
docker-compose --profile "$PROFILE" ps

echo ""
echo "=========================================="
echo "  Available Endpoints"
echo "=========================================="
echo ""
echo "  Tunnel Entry Points:"
echo "    SSH:   localhost:2222  -> test-ssh:2222"
echo "    HTTP:  localhost:8080  -> test-http:80"
echo "    Echo:  localhost:9000  -> test-echo:9000"
echo ""
echo "  Monitoring:"
echo "    Entry Metrics: http://localhost:9091/metrics"
echo "    Exit Metrics:  http://localhost:9090/metrics"
echo "    Prometheus:    http://localhost:9090"
echo "    Grafana:       http://localhost:3001 (admin/admin)"
echo ""
echo "  Network Emulation:"
echo "    Profile: LEO (40ms delay, 1% loss, 150 Mbps)"
echo ""
echo "=========================================="
echo "  Quick Tests"
echo "=========================================="
echo ""
echo "  # Test HTTP through tunnel (PowerShell):"
echo "  Invoke-WebRequest -Uri http://localhost:8080/test.txt"
echo ""
echo "  # Test HTTP through tunnel (bash/curl):"
echo "  curl http://localhost:8080/test.txt"
echo ""
echo "  # Test SSH through tunnel (requires OpenSSH):"
echo "  ssh -p 2222 testuser@localhost  # password: testpass"
echo ""
echo "  # Test from inside Docker (recommended):"
echo "  docker exec -it quick-entry sh -c 'curl http://test-http/test.txt'"
echo ""
echo "  # Run Phase 1 tests:"
echo "  ./scripts/test-phase1.sh"
echo ""
echo "  # Run Phase 2 benchmarks:"
echo "  ./scripts/benchmark-phase2.sh"
echo ""
echo "  # Switch tunnel implementation:"
echo "  TUNNEL_PROFILE=quiche ./scripts/start-demo.sh  # Use QUICHE/BBR"
echo "  TUNNEL_PROFILE=msquic ./scripts/start-demo.sh  # Use msquic/CUBIC"
echo ""
echo "=========================================="
echo "  Demo Ready!"
echo "=========================================="
