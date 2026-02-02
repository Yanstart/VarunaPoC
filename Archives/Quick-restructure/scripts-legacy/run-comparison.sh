#!/bin/bash
# QUICK- Multi-Implementation Comparison Test Runner
# Runs comparison tests across QUICHE, msquic, and quic-go implementations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_DIR="$PROJECT_ROOT/deployments/comparison"
SCENARIOS_DIR="$PROJECT_ROOT/test/comparison/scenarios"
RESULTS_DIR="$PROJECT_ROOT/test-results"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SCENARIO="leo_nominal"
DURATION=300
WARMUP=30
RUN_ID=""

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --scenario SCENARIO   Test scenario (default: leo_nominal)"
    echo "                            Available: leo_nominal, geo_high_latency, leo_handover"
    echo "  -d, --duration SECONDS    Test duration in seconds (default: 300)"
    echo "  -w, --warmup SECONDS      Warmup period in seconds (default: 30)"
    echo "  -r, --run-id ID           Custom run ID (default: timestamp)"
    echo "  -l, --list                List available scenarios"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        Run with defaults (LEO nominal, 5 min)"
    echo "  $0 -s geo_high_latency    Run GEO high latency scenario"
    echo "  $0 -s leo_handover -d 600 Run handover scenario for 10 min"
}

list_scenarios() {
    echo "Available test scenarios:"
    echo ""
    for f in "$SCENARIOS_DIR"/*.json; do
        if [ -f "$f" ]; then
            name=$(basename "$f" .json)
            desc=$(jq -r '.description // "No description"' "$f")
            echo "  $name"
            echo "    $desc"
            echo ""
        fi
    done
}

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
        -s|--scenario)
            SCENARIO="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -w|--warmup)
            WARMUP="$2"
            shift 2
            ;;
        -r|--run-id)
            RUN_ID="$2"
            shift 2
            ;;
        -l|--list)
            list_scenarios
            exit 0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Generate run ID if not provided
if [ -z "$RUN_ID" ]; then
    RUN_ID="comparison-$(date +%Y%m%d-%H%M%S)"
fi

# Verify scenario file exists
SCENARIO_FILE="$SCENARIOS_DIR/$SCENARIO.json"
if [ ! -f "$SCENARIO_FILE" ]; then
    log_error "Scenario file not found: $SCENARIO_FILE"
    list_scenarios
    exit 1
fi

# Create results directory
RESULTS_RUN_DIR="$RESULTS_DIR/$RUN_ID"
mkdir -p "$RESULTS_RUN_DIR"

log_info "========================================"
log_info "QUICK- Multi-Implementation Comparison"
log_info "========================================"
log_info "Run ID:     $RUN_ID"
log_info "Scenario:   $SCENARIO"
log_info "Duration:   ${DURATION}s"
log_info "Warmup:     ${WARMUP}s"
log_info "Results:    $RESULTS_RUN_DIR"
log_info "========================================"

# Start infrastructure
log_info "Starting infrastructure..."
cd "$COMPOSE_DIR"

# Check if already running
if docker compose ps --quiet 2>/dev/null | grep -q .; then
    log_warning "Some services are already running. Stopping..."
    docker compose down --remove-orphans
fi

# Start database and monitoring first
log_info "Starting database and monitoring services..."
docker compose up -d timescaledb prometheus grafana

# Wait for TimescaleDB to be ready
log_info "Waiting for TimescaleDB to be ready..."
for i in {1..30}; do
    if docker compose exec -T timescaledb pg_isready -U quicktunnel >/dev/null 2>&1; then
        log_success "TimescaleDB is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "TimescaleDB failed to start"
        exit 1
    fi
    sleep 2
done

# Initialize schema
log_info "Initializing database schema..."
docker compose exec -T timescaledb psql -U quicktunnel -d quicktunnel -f /docker-entrypoint-initdb.d/001_metadata_schema.sql 2>/dev/null || true

# Start satellite simulator
log_info "Starting satellite network simulator..."
docker compose up -d satellite-sim

sleep 5

# Configure network scenario
log_info "Configuring network scenario: $SCENARIO"
SCENARIO_JSON=$(cat "$SCENARIO_FILE")
RTT_MS=$(echo "$SCENARIO_JSON" | jq -r '.network.rtt_ms // .network.base_rtt_ms // 40')
JITTER_MS=$(echo "$SCENARIO_JSON" | jq -r '.network.jitter_ms // .network.base_jitter_ms // 5')
LOSS_RATE=$(echo "$SCENARIO_JSON" | jq -r '.network.loss_rate // .network.base_loss_rate // 0.001')
BANDWIDTH_MBPS=$(echo "$SCENARIO_JSON" | jq -r '.network.bandwidth_mbps // 100')

# Apply network conditions via satellite-sim API
curl -s -X POST "http://localhost:8888/scenario" \
    -H "Content-Type: application/json" \
    -d "{
        \"rtt_ms\": $RTT_MS,
        \"jitter_ms\": $JITTER_MS,
        \"loss_rate\": $LOSS_RATE,
        \"bandwidth_mbps\": $BANDWIDTH_MBPS
    }" || log_warning "Failed to configure satellite-sim (may need manual configuration)"

# Start backend test services
log_info "Starting backend test services..."
docker compose up -d test-ssh test-http test-echo test-iperf

sleep 5

# Start all tunnel implementations
log_info "Starting tunnel implementations..."

# Set environment variables for run tracking
export RUN_ID
export SCENARIO

# Start QUICHE
log_info "Starting QUICHE (BBRv2) tunnel..."
docker compose up -d quiche-exit quiche-entry

# Start msquic
log_info "Starting msquic (CUBIC) tunnel..."
docker compose up -d msquic-exit msquic-entry

# Start quic-go
log_info "Starting quic-go (CUBIC) tunnel..."
docker compose up -d quicgo-exit quicgo-entry

# Wait for all services to be healthy
log_info "Waiting for all services to be ready..."
sleep 10

# Check service health
for service in quiche-entry quiche-exit msquic-entry msquic-exit quicgo-entry quicgo-exit; do
    if ! docker compose ps "$service" | grep -q "Up"; then
        log_error "Service $service is not running"
        docker compose logs "$service"
        exit 1
    fi
done

log_success "All services are running"

# Start metadata collector
log_info "Starting metadata collector..."
docker compose up -d metadata-collector

# Record test start in database
log_info "Recording test run in database..."
docker compose exec -T timescaledb psql -U quicktunnel -d quicktunnel -c "
INSERT INTO test_runs (run_id, impl_id, started_at, satellite_profile, network_scenario, status)
VALUES
    ('$RUN_ID-quiche', 'quiche-bbrv2', NOW(), '$SCENARIO', '$SCENARIO', 'running'),
    ('$RUN_ID-msquic', 'msquic-cubic', NOW(), '$SCENARIO', '$SCENARIO', 'running'),
    ('$RUN_ID-quicgo', 'quic-go-cubic', NOW(), '$SCENARIO', '$SCENARIO', 'running')
ON CONFLICT (run_id) DO NOTHING;
" 2>/dev/null || true

# Warmup period
log_info "Warmup period (${WARMUP}s)..."
sleep "$WARMUP"

# Run tests
log_info "Running comparison tests (${DURATION}s)..."
log_info "Access Grafana at http://localhost:3000 (admin/admin)"
log_info "Access Prometheus at http://localhost:9090"

# Start test traffic for each implementation
log_info "Generating test traffic..."

# Test SSH through each implementation
(
    log_info "Testing SSH through QUICHE..."
    timeout $DURATION sshpass -p testpass ssh -o StrictHostKeyChecking=no -p 2222 testuser@localhost "while true; do echo test; sleep 1; done" >/dev/null 2>&1 || true
) &

(
    log_info "Testing SSH through msquic..."
    timeout $DURATION sshpass -p testpass ssh -o StrictHostKeyChecking=no -p 2223 testuser@localhost "while true; do echo test; sleep 1; done" >/dev/null 2>&1 || true
) &

(
    log_info "Testing SSH through quic-go..."
    timeout $DURATION sshpass -p testpass ssh -o StrictHostKeyChecking=no -p 2224 testuser@localhost "while true; do echo test; sleep 1; done" >/dev/null 2>&1 || true
) &

# Test HTTP through each implementation
(
    log_info "Testing HTTP through QUICHE..."
    for i in $(seq 1 $((DURATION / 2))); do
        curl -s -o /dev/null "http://localhost:8080/" || true
        sleep 2
    done
) &

(
    log_info "Testing HTTP through msquic..."
    for i in $(seq 1 $((DURATION / 2))); do
        curl -s -o /dev/null "http://localhost:8081/" || true
        sleep 2
    done
) &

(
    log_info "Testing HTTP through quic-go..."
    for i in $(seq 1 $((DURATION / 2))); do
        curl -s -o /dev/null "http://localhost:8082/" || true
        sleep 2
    done
) &

# Wait for test duration
log_info "Waiting for tests to complete..."
sleep "$DURATION"

# Wait for background processes
wait

log_success "Tests completed"

# Mark test runs as completed
log_info "Marking test runs as completed..."
docker compose exec -T timescaledb psql -U quicktunnel -d quicktunnel -c "
UPDATE test_runs
SET ended_at = NOW(), status = 'completed'
WHERE run_id LIKE '$RUN_ID%';
" 2>/dev/null || true

# Export results
log_info "Exporting results..."

# Export Prometheus metrics snapshot
curl -s "http://localhost:9090/api/v1/query?query={__name__=~'quick_tunnel.*|quic_proxy.*'}" \
    > "$RESULTS_RUN_DIR/prometheus_final_metrics.json" || true

# Export comparison summary from TimescaleDB
docker compose exec -T timescaledb psql -U quicktunnel -d quicktunnel -t -A -c "
SELECT json_agg(t) FROM (
    SELECT
        impl_id,
        COUNT(DISTINCT conn_id) as total_connections,
        AVG(rtt_smoothed_ms) as avg_rtt_ms,
        MIN(rtt_min_ms) as min_rtt_ms,
        MAX(rtt_max_ms) as max_rtt_ms,
        SUM(bytes_sent) as total_bytes_sent,
        SUM(bytes_received) as total_bytes_received,
        SUM(packets_lost) as total_packets_lost,
        AVG(cwnd_bytes) as avg_cwnd_bytes
    FROM transport_metrics
    WHERE run_id LIKE '$RUN_ID%'
    GROUP BY impl_id
) t;
" > "$RESULTS_RUN_DIR/transport_summary.json" 2>/dev/null || true

docker compose exec -T timescaledb psql -U quicktunnel -d quicktunnel -t -A -c "
SELECT json_agg(t) FROM (
    SELECT
        impl_id,
        AVG(throughput_bps) / 1000000 as avg_throughput_mbps,
        AVG(goodput_bps) / 1000000 as avg_goodput_mbps,
        AVG(first_byte_latency_ms) as avg_first_byte_ms,
        AVG(handshake_latency_ms) as avg_handshake_ms,
        AVG(loss_rate) as avg_loss_rate,
        AVG(retransmission_rate) as avg_retrans_rate
    FROM performance_metrics
    WHERE run_id LIKE '$RUN_ID%'
    GROUP BY impl_id
) t;
" > "$RESULTS_RUN_DIR/performance_summary.json" 2>/dev/null || true

# Copy metadata files
log_info "Copying metadata files..."
docker cp quick-metadata-collector:/data "$RESULTS_RUN_DIR/metadata" 2>/dev/null || true

# Generate summary report
log_info "Generating summary report..."
cat > "$RESULTS_RUN_DIR/summary.txt" << EOF
QUICK- Multi-Implementation Comparison Results
===============================================

Run ID:     $RUN_ID
Scenario:   $SCENARIO
Duration:   ${DURATION}s
Warmup:     ${WARMUP}s
Timestamp:  $(date -Iseconds)

Network Conditions:
  RTT:        ${RTT_MS}ms
  Jitter:     ${JITTER_MS}ms
  Loss Rate:  ${LOSS_RATE}
  Bandwidth:  ${BANDWIDTH_MBPS} Mbps

Results stored in: $RESULTS_RUN_DIR

Files:
  - prometheus_final_metrics.json  : Final Prometheus metrics snapshot
  - transport_summary.json         : Transport layer metrics summary
  - performance_summary.json       : Performance metrics summary
  - metadata/                      : Raw metadata files from each implementation

Access Grafana dashboard for visualization:
  URL: http://localhost:3000
  Dashboard: QUIC Implementation Comparison
EOF

log_success "Results saved to $RESULTS_RUN_DIR"
log_info "Summary:"
cat "$RESULTS_RUN_DIR/summary.txt"

# Ask about cleanup
echo ""
read -p "Stop all services? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Stopping all services..."
    docker compose down
    log_success "All services stopped"
else
    log_info "Services are still running"
    log_info "To stop: cd $COMPOSE_DIR && docker compose down"
fi

log_success "Comparison test completed successfully"
