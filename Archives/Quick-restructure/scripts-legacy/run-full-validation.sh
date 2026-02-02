#!/bin/bash
# QUICK- Full Validation Test Suite
# Runs all tests across all implementations and scenarios
#
# Usage: ./scripts/run-full-validation.sh [options]
#
# Options:
#   --impl <name>     Test only specific implementation (quiche, msquic, quic-go, quiche-cloudflare)
#   --scenario <name> Test only specific scenario (leo, meo, geo, etc.)
#   --quick           Run quick tests only (skip stress tests)
#   --report          Generate HTML report at end
#   --help            Show this help message

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_ROOT/Validation/results/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$RESULTS_DIR/validation.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default options
IMPL_FILTER=""
SCENARIO_FILTER=""
QUICK_MODE=false
GENERATE_REPORT=false

# Available implementations and scenarios
IMPLEMENTATIONS=("quiche" "msquic" "quic-go" "quiche-cloudflare")
SCENARIOS=(
    "leo_nominal" "starlink_nominal" "oneweb_nominal"
    "meo_nominal"
    "geo_nominal" "geo_rain_fade"
    "ka_band_rain_moderate" "ku_band_rain_heavy"
    "solar_storm" "maritime_mobile" "aero_inflight"
)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --impl)
            IMPL_FILTER="$2"
            shift 2
            ;;
        --scenario)
            SCENARIO_FILTER="$2"
            shift 2
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --help)
            head -n 15 "$0" | tail -n 12
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$1"; }
log_warn() { log "WARN" "${YELLOW}$1${NC}"; }
log_error() { log "ERROR" "${RED}$1${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose not found"
        exit 1
    fi

    log_success "Prerequisites OK"
}

# Start infrastructure
start_infrastructure() {
    log_info "Starting test infrastructure..."
    cd "$PROJECT_ROOT/deployments/docker"

    # Create networks and volumes
    docker network create quick-management 2>/dev/null || true
    docker network create quick-tunnel 2>/dev/null || true
    docker network create quick-backend 2>/dev/null || true
    docker network create quick-client 2>/dev/null || true
    docker network create quick-satellite 2>/dev/null || true

    docker volume create quick-prometheus-data 2>/dev/null || true
    docker volume create quick-grafana-data 2>/dev/null || true
    docker volume create quick-timescaledb-data 2>/dev/null || true
    docker volume create quick-test-results 2>/dev/null || true
    docker volume create quick-pcap-captures 2>/dev/null || true

    # Start base infrastructure
    docker compose -f docker-compose.base.yaml \
                   -f docker-compose.backends.yaml \
                   -f docker-compose.monitoring.yaml \
                   -f docker-compose.satellite-simulation.yaml \
                   up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    log_success "Infrastructure started"
}

# Check if implementation is available
check_implementation() {
    local impl="$1"
    local result=0

    case $impl in
        quiche)
            docker compose -f docker-compose.quiche.yaml ps --quiet 2>/dev/null | grep -q . || result=1
            ;;
        msquic)
            docker compose -f docker-compose.msquic.yaml ps --quiet 2>/dev/null | grep -q . || result=1
            ;;
        quic-go)
            docker compose -f docker-compose.quicgo.yaml ps --quiet 2>/dev/null | grep -q . || result=1
            ;;
        quiche-cloudflare)
            docker compose -f docker-compose.quiche-cloudflare.yaml ps --quiet 2>/dev/null | grep -q . || result=1
            ;;
    esac

    return $result
}

# Start implementation
start_implementation() {
    local impl="$1"
    log_info "Starting implementation: $impl"

    cd "$PROJECT_ROOT/deployments/docker"

    case $impl in
        quiche)
            docker compose -f docker-compose.base.yaml -f docker-compose.quiche.yaml up -d
            ;;
        msquic)
            docker compose -f docker-compose.base.yaml -f docker-compose.msquic.yaml up -d
            ;;
        quic-go)
            docker compose -f docker-compose.base.yaml -f docker-compose.quicgo.yaml up -d
            ;;
        quiche-cloudflare)
            docker compose -f docker-compose.base.yaml -f docker-compose.quiche-cloudflare.yaml up -d
            ;;
    esac

    sleep 10
    log_success "Implementation $impl started"
}

# Run scenario test
run_scenario_test() {
    local impl="$1"
    local scenario="$2"
    local result_file="$RESULTS_DIR/${impl}_${scenario}.json"

    log_info "Testing $impl with scenario $scenario..."

    # Apply scenario
    curl -s -X POST "http://localhost:8888/scenario/$scenario" > /dev/null

    # Wait for conditions to stabilize
    sleep 5

    # Run tests via orchestrator
    docker exec quick-orchestrator python /app/run_test.py "$scenario" --impl "$impl" > "$result_file" 2>&1

    if grep -q "error" "$result_file"; then
        log_error "Test failed: $impl / $scenario"
        return 1
    else
        log_success "Test passed: $impl / $scenario"
        return 0
    fi
}

# Run physics simulation
run_physics_simulation() {
    local scenario="$1"
    local duration="${2:-120}"

    log_info "Running physics simulation: $scenario for ${duration}s"

    docker exec quick-sat-sim-entry python /app/physics/satellite_physics.py \
        --scenario "$scenario" \
        --duration "$duration" > "$RESULTS_DIR/physics_${scenario}.log" 2>&1 &

    local pid=$!
    log_info "Physics simulation started (PID: $pid)"
    echo $pid
}

# Generate report
generate_report() {
    log_info "Generating validation report..."

    local report_file="$RESULTS_DIR/report.html"

    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>QUICK- Validation Report</title>
    <style>
        body { font-family: -apple-system, sans-serif; margin: 40px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #4CAF50; color: white; }
        .pass { background: #dff0d8; }
        .fail { background: #f2dede; }
        .summary { margin: 20px 0; padding: 15px; background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>QUICK- Tunnel Validation Report</h1>
EOF

    echo "<p>Generated: $(date)</p>" >> "$report_file"
    echo "<div class='summary'><h2>Test Summary</h2>" >> "$report_file"

    # Count results
    local total=$(ls -1 "$RESULTS_DIR"/*.json 2>/dev/null | wc -l)
    local passed=$(grep -l '"error"' "$RESULTS_DIR"/*.json 2>/dev/null | wc -l)
    local failed=$((total - passed))

    echo "<p>Total Tests: $total | Passed: $passed | Failed: $failed</p>" >> "$report_file"
    echo "</div>" >> "$report_file"

    echo "<h2>Test Results</h2><table><tr><th>Implementation</th><th>Scenario</th><th>Status</th></tr>" >> "$report_file"

    for file in "$RESULTS_DIR"/*.json; do
        if [[ -f "$file" ]]; then
            local name=$(basename "$file" .json)
            local impl=$(echo "$name" | cut -d_ -f1)
            local scenario=$(echo "$name" | cut -d_ -f2-)
            if grep -q '"error"' "$file"; then
                echo "<tr class='fail'><td>$impl</td><td>$scenario</td><td>FAIL</td></tr>" >> "$report_file"
            else
                echo "<tr class='pass'><td>$impl</td><td>$scenario</td><td>PASS</td></tr>" >> "$report_file"
            fi
        fi
    done

    echo "</table></body></html>" >> "$report_file"

    log_success "Report generated: $report_file"
}

# Main execution
main() {
    mkdir -p "$RESULTS_DIR"

    echo -e "${BLUE}"
    echo "============================================"
    echo "  QUICK- Full Validation Test Suite"
    echo "============================================"
    echo -e "${NC}"

    log_info "Results directory: $RESULTS_DIR"

    check_prerequisites
    start_infrastructure

    # Filter implementations if specified
    local impls_to_test=()
    if [[ -n "$IMPL_FILTER" ]]; then
        impls_to_test=("$IMPL_FILTER")
    else
        impls_to_test=("${IMPLEMENTATIONS[@]}")
    fi

    # Filter scenarios if specified
    local scenarios_to_test=()
    if [[ -n "$SCENARIO_FILTER" ]]; then
        scenarios_to_test=("$SCENARIO_FILTER")
    elif [[ "$QUICK_MODE" == true ]]; then
        scenarios_to_test=("leo_nominal" "meo_nominal" "geo_nominal")
    else
        scenarios_to_test=("${SCENARIOS[@]}")
    fi

    # Run tests
    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    for impl in "${impls_to_test[@]}"; do
        log_info "===== Testing implementation: $impl ====="

        start_implementation "$impl"

        for scenario in "${scenarios_to_test[@]}"; do
            ((total_tests++))

            if run_scenario_test "$impl" "$scenario"; then
                ((passed_tests++))
            else
                ((failed_tests++))
            fi
        done
    done

    # Summary
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Validation Complete${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "Total Tests:  $total_tests"
    echo -e "${GREEN}Passed:       $passed_tests${NC}"
    echo -e "${RED}Failed:       $failed_tests${NC}"
    echo ""
    echo "Results: $RESULTS_DIR"

    if [[ "$GENERATE_REPORT" == true ]]; then
        generate_report
    fi

    if [[ $failed_tests -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
