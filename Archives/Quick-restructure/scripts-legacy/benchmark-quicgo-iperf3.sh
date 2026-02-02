#!/bin/bash
# =============================================================================
# quic-go iperf3 Benchmark Script
# =============================================================================
# Tests throughput through the quic-go tunnel using iperf3
#
# Prerequisites:
#   docker compose -f deployments/docker/docker-compose.base.yaml \
#     -f deployments/docker/docker-compose.backends.yaml \
#     -f deployments/docker/docker-compose.quicgo.yaml \
#     -f deployments/docker/docker-compose.satellite-simulation.yaml up -d
#
# Usage:
#   ./scripts/benchmark-quicgo-iperf3.sh [scenario]
#
# Scenarios: direct, leo, meo, geo
# =============================================================================

set -e

SCENARIO=${1:-direct}
DURATION=${2:-30}
RESULTS_DIR="Validation/implementations/quic-go/benchmarks"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create results directory
mkdir -p "$RESULTS_DIR"

log "quic-go iperf3 Benchmark"
log "========================"
log "Scenario: $SCENARIO"
log "Duration: ${DURATION}s"
echo

# Check containers are running
log "Checking infrastructure..."
if ! docker ps | grep -q quick-quicgo-entry; then
    error "quicgo-entry not running. Start with:"
    echo "  docker compose -f deployments/docker/docker-compose.base.yaml \\"
    echo "    -f deployments/docker/docker-compose.backends.yaml \\"
    echo "    -f deployments/docker/docker-compose.quicgo.yaml up -d"
    exit 1
fi

if ! docker ps | grep -q quick-test-iperf; then
    error "test-iperf not running. Start with:"
    echo "  docker compose -f deployments/docker/docker-compose.backends.yaml up -d"
    exit 1
fi

if ! docker ps | grep -q quick-iperf-client; then
    error "iperf-client not running. Start with:"
    echo "  docker compose -f deployments/docker/docker-compose.satellite-simulation.yaml up -d"
    exit 1
fi

success "All containers running"

# Apply satellite scenario if needed
apply_scenario() {
    local scenario=$1
    case $scenario in
        direct)
            log "Direct connection (no simulation)"
            ;;
        leo)
            log "Applying LEO scenario (40ms RTT, 0.5% loss)"
            curl -s -X POST "http://localhost:8888/preset/leo_nominal" || warn "Satellite sim not available"
            ;;
        meo)
            log "Applying MEO scenario (120ms RTT, 0.3% loss)"
            curl -s -X POST "http://localhost:8888/preset/meo_nominal" || warn "Satellite sim not available"
            ;;
        geo)
            log "Applying GEO scenario (600ms RTT, 0.1% loss)"
            curl -s -X POST "http://localhost:8888/preset/geo_nominal" || warn "Satellite sim not available"
            ;;
        *)
            warn "Unknown scenario: $scenario, using direct"
            ;;
    esac
}

# Run iperf3 test
run_iperf_test() {
    local name=$1
    local target=$2
    local port=$3
    local duration=$4
    local output_file=$5

    log "Running: $name"
    log "  Target: $target:$port"
    log "  Duration: ${duration}s"

    # TCP test (upload)
    log "  TCP Upload..."
    docker exec quick-iperf-client iperf3 -c "$target" -p "$port" -t "$duration" -J \
        > "$output_file.tcp-upload.json" 2>/dev/null || true

    # TCP test (download)
    log "  TCP Download..."
    docker exec quick-iperf-client iperf3 -c "$target" -p "$port" -t "$duration" -R -J \
        > "$output_file.tcp-download.json" 2>/dev/null || true

    # Parse results
    if [ -f "$output_file.tcp-upload.json" ]; then
        local upload_bps=$(jq -r '.end.sum_sent.bits_per_second // 0' "$output_file.tcp-upload.json" 2>/dev/null || echo 0)
        local upload_mbps=$(echo "scale=2; $upload_bps / 1000000" | bc 2>/dev/null || echo "N/A")
        success "  Upload: ${upload_mbps} Mbps"
    fi

    if [ -f "$output_file.tcp-download.json" ]; then
        local download_bps=$(jq -r '.end.sum_received.bits_per_second // 0' "$output_file.tcp-download.json" 2>/dev/null || echo 0)
        local download_mbps=$(echo "scale=2; $download_bps / 1000000" | bc 2>/dev/null || echo "N/A")
        success "  Download: ${download_mbps} Mbps"
    fi
}

# Apply scenario
apply_scenario "$SCENARIO"
sleep 2

TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_PREFIX="$RESULTS_DIR/iperf3-$SCENARIO-$TIMESTAMP"

echo
log "=== Test 1: Direct to iperf server (baseline) ==="
run_iperf_test "Direct (no tunnel)" "test-iperf" "5201" "$DURATION" "$OUTPUT_PREFIX-direct"

echo
log "=== Test 2: Through quic-go tunnel ==="
run_iperf_test "Via quic-go tunnel" "quicgo-entry" "5201" "$DURATION" "$OUTPUT_PREFIX-tunnel"

echo
log "=== Results Summary ==="

# Extract and compare results
extract_mbps() {
    local file=$1
    local field=$2
    if [ -f "$file" ]; then
        local bps=$(jq -r "$field // 0" "$file" 2>/dev/null || echo 0)
        echo "scale=2; $bps / 1000000" | bc 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

DIRECT_UP=$(extract_mbps "$OUTPUT_PREFIX-direct.tcp-upload.json" '.end.sum_sent.bits_per_second')
DIRECT_DOWN=$(extract_mbps "$OUTPUT_PREFIX-direct.tcp-download.json" '.end.sum_received.bits_per_second')
TUNNEL_UP=$(extract_mbps "$OUTPUT_PREFIX-tunnel.tcp-upload.json" '.end.sum_sent.bits_per_second')
TUNNEL_DOWN=$(extract_mbps "$OUTPUT_PREFIX-tunnel.tcp-download.json" '.end.sum_received.bits_per_second')

echo
echo "| Test           | Upload (Mbps) | Download (Mbps) |"
echo "|----------------|---------------|-----------------|"
printf "| Direct         | %13s | %15s |\n" "$DIRECT_UP" "$DIRECT_DOWN"
printf "| quic-go tunnel | %13s | %15s |\n" "$TUNNEL_UP" "$TUNNEL_DOWN"

# Calculate overhead
if [ "$DIRECT_UP" != "0" ] && [ "$TUNNEL_UP" != "0" ]; then
    OVERHEAD_UP=$(echo "scale=1; 100 - ($TUNNEL_UP / $DIRECT_UP * 100)" | bc 2>/dev/null || echo "N/A")
    echo
    log "Tunnel overhead (upload): ${OVERHEAD_UP}%"
fi

if [ "$DIRECT_DOWN" != "0" ] && [ "$TUNNEL_DOWN" != "0" ]; then
    OVERHEAD_DOWN=$(echo "scale=1; 100 - ($TUNNEL_DOWN / $DIRECT_DOWN * 100)" | bc 2>/dev/null || echo "N/A")
    log "Tunnel overhead (download): ${OVERHEAD_DOWN}%"
fi

echo
log "Results saved to: $RESULTS_DIR/"
ls -la "$OUTPUT_PREFIX"*.json 2>/dev/null || true

# Generate markdown report
REPORT_FILE="$RESULTS_DIR/iperf3-report-$SCENARIO-$TIMESTAMP.md"
cat > "$REPORT_FILE" << EOF
# quic-go iperf3 Benchmark Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Scenario**: $SCENARIO
**Duration**: ${DURATION}s per test

## Results

| Test | Upload (Mbps) | Download (Mbps) |
|------|---------------|-----------------|
| Direct (baseline) | $DIRECT_UP | $DIRECT_DOWN |
| quic-go tunnel | $TUNNEL_UP | $TUNNEL_DOWN |

## Overhead

- Upload: ${OVERHEAD_UP:-N/A}%
- Download: ${OVERHEAD_DOWN:-N/A}%

## Environment

- Implementation: quic-go (Go)
- Congestion Control: NewReno/CUBIC
- QUIC Library: quic-go/quic-go
- Scenario: $SCENARIO

## Raw Data

- Direct upload: \`$OUTPUT_PREFIX-direct.tcp-upload.json\`
- Direct download: \`$OUTPUT_PREFIX-direct.tcp-download.json\`
- Tunnel upload: \`$OUTPUT_PREFIX-tunnel.tcp-upload.json\`
- Tunnel download: \`$OUTPUT_PREFIX-tunnel.tcp-download.json\`
EOF

success "Report generated: $REPORT_FILE"
