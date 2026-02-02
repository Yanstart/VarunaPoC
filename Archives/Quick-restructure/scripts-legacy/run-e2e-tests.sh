#!/bin/bash
# =============================================================================
# QUICK- E2E Test Suite
# Tests automatises pour tous les scenarios satellite
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
SCENARIOS_DIR="$DEPLOY_DIR/infrastructure/satellite-sim/scenarios"
RESULTS_DIR="$DEPLOY_DIR/tests/results/e2e-$(date +%Y%m%d-%H%M%S)"
IMPLEMENTATION="${1:-quiche-cloudflare}"
SCENARIO_FILTER="${2:-all}"
DURATION="${3:-30}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

mkdir -p "$RESULTS_DIR"

# Header
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         QUICK- E2E Test Suite - All Scenarios                  ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║ Implementation: ${YELLOW}$IMPLEMENTATION${BLUE}                                   ║${NC}"
echo -e "${BLUE}║ Duration/test:  ${YELLOW}${DURATION}s${BLUE}                                          ║${NC}"
echo -e "${BLUE}║ Results:        ${YELLOW}$RESULTS_DIR${BLUE}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Liste des scenarios
SCENARIOS=$(ls "$SCENARIOS_DIR"/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json$//')

if [ "$SCENARIO_FILTER" != "all" ]; then
    SCENARIOS=$(echo "$SCENARIOS" | grep -E "$SCENARIO_FILTER" || true)
fi

TOTAL=$(echo "$SCENARIOS" | wc -w)
PASSED=0
FAILED=0
SKIPPED=0

# Resultats JSON
echo "{" > "$RESULTS_DIR/summary.json"
echo "  \"implementation\": \"$IMPLEMENTATION\"," >> "$RESULTS_DIR/summary.json"
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> "$RESULTS_DIR/summary.json"
echo "  \"duration_per_test\": $DURATION," >> "$RESULTS_DIR/summary.json"
echo "  \"results\": [" >> "$RESULTS_DIR/summary.json"

FIRST=true

for scenario in $SCENARIOS; do
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Testing: ${YELLOW}$scenario${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    SCENARIO_RESULT="$RESULTS_DIR/$scenario"
    mkdir -p "$SCENARIO_RESULT"

    # Lire les parametres du scenario
    SCENARIO_FILE="$SCENARIOS_DIR/$scenario.json"
    DELAY=$(jq -r '.delay // "50ms"' "$SCENARIO_FILE")
    JITTER=$(jq -r '.jitter // "10ms"' "$SCENARIO_FILE")
    LOSS=$(jq -r '.loss // "1%"' "$SCENARIO_FILE")
    RATE=$(jq -r '.rate // "100mbit"' "$SCENARIO_FILE")

    echo "  Parameters: delay=$DELAY, jitter=$JITTER, loss=$LOSS, rate=$RATE"

    # Appliquer le scenario via l'API satellite-sim
    if curl -sf -X POST "http://localhost:8888/preset/$scenario" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Scenario applied"
    else
        # Essayer avec les parametres bruts
        if curl -sf -X POST "http://localhost:8888/apply" \
            -H "Content-Type: application/json" \
            -d "{\"delay\":\"$DELAY\",\"jitter\":\"$JITTER\",\"loss\":\"$LOSS\",\"rate\":\"$RATE\"}" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} Scenario applied (manual)"
        else
            echo -e "  ${YELLOW}⚠${NC} Cannot apply scenario (satellite-sim not running?)"
            ((SKIPPED++))
            continue
        fi
    fi

    sleep 2  # Attendre stabilisation

    # Test HTTP throughput
    echo "  Running HTTP throughput test..."
    HTTP_START=$(date +%s%N)
    HTTP_RESULT=$(curl -sf -w "%{time_total},%{speed_download}" -o /dev/null \
        "http://localhost:8080/test-files/1mb.bin" 2>/dev/null || echo "0,0")
    HTTP_TIME=$(echo "$HTTP_RESULT" | cut -d',' -f1)
    HTTP_SPEED=$(echo "$HTTP_RESULT" | cut -d',' -f2)
    HTTP_SPEED_MBPS=$(echo "scale=2; $HTTP_SPEED * 8 / 1000000" | bc 2>/dev/null || echo "0")

    # Test latency (10 pings)
    echo "  Running latency test..."
    LATENCIES=""
    for i in $(seq 1 10); do
        LAT=$(curl -sf -w "%{time_connect}" -o /dev/null "http://localhost:8080/" 2>/dev/null || echo "0")
        LATENCIES="$LATENCIES $LAT"
    done
    AVG_LATENCY=$(echo "$LATENCIES" | tr ' ' '\n' | grep -v '^$' | awk '{sum+=$1; count++} END {if(count>0) print sum/count*1000; else print 0}')

    # Test de stabilite (30s de transferts)
    echo "  Running stability test (${DURATION}s)..."
    STABILITY_RESULT=$(timeout ${DURATION}s bash -c '
        SUCCESS=0
        FAIL=0
        for i in $(seq 1 100); do
            if curl -sf -o /dev/null "http://localhost:8080/test-files/10kb.bin" 2>/dev/null; then
                ((SUCCESS++))
            else
                ((FAIL++))
            fi
            sleep 0.3
        done
        echo "$SUCCESS,$FAIL"
    ' 2>/dev/null || echo "0,100")

    STABILITY_SUCCESS=$(echo "$STABILITY_RESULT" | cut -d',' -f1)
    STABILITY_FAIL=$(echo "$STABILITY_RESULT" | cut -d',' -f2)
    STABILITY_RATE=$(echo "scale=2; $STABILITY_SUCCESS * 100 / ($STABILITY_SUCCESS + $STABILITY_FAIL)" | bc 2>/dev/null || echo "0")

    # Determiner le statut
    STATUS="PASSED"
    if [ "$(echo "$STABILITY_RATE < 80" | bc)" == "1" ]; then
        STATUS="FAILED"
        ((FAILED++))
    else
        ((PASSED++))
    fi

    # Afficher les resultats
    if [ "$STATUS" == "PASSED" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  ${RED}✗ FAILED${NC}"
    fi
    echo "    HTTP Speed:    ${HTTP_SPEED_MBPS} Mbps"
    echo "    Avg Latency:   ${AVG_LATENCY} ms"
    echo "    Stability:     ${STABILITY_RATE}%"

    # Sauvegarder les resultats
    cat > "$SCENARIO_RESULT/results.json" << EOF
{
  "scenario": "$scenario",
  "status": "$STATUS",
  "parameters": {
    "delay": "$DELAY",
    "jitter": "$JITTER",
    "loss": "$LOSS",
    "rate": "$RATE"
  },
  "metrics": {
    "http_speed_mbps": $HTTP_SPEED_MBPS,
    "avg_latency_ms": $AVG_LATENCY,
    "stability_percent": $STABILITY_RATE,
    "requests_success": $STABILITY_SUCCESS,
    "requests_failed": $STABILITY_FAIL
  },
  "timestamp": "$(date -Iseconds)"
}
EOF

    # Ajouter au JSON global
    if [ "$FIRST" != "true" ]; then
        echo "," >> "$RESULTS_DIR/summary.json"
    fi
    FIRST=false
    cat "$SCENARIO_RESULT/results.json" >> "$RESULTS_DIR/summary.json"
done

# Finaliser le JSON
echo "" >> "$RESULTS_DIR/summary.json"
echo "  ]," >> "$RESULTS_DIR/summary.json"
echo "  \"summary\": {" >> "$RESULTS_DIR/summary.json"
echo "    \"total\": $TOTAL," >> "$RESULTS_DIR/summary.json"
echo "    \"passed\": $PASSED," >> "$RESULTS_DIR/summary.json"
echo "    \"failed\": $FAILED," >> "$RESULTS_DIR/summary.json"
echo "    \"skipped\": $SKIPPED" >> "$RESULTS_DIR/summary.json"
echo "  }" >> "$RESULTS_DIR/summary.json"
echo "}" >> "$RESULTS_DIR/summary.json"

# Resume final
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    E2E Test Summary                            ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║ Total:   ${YELLOW}$TOTAL${BLUE}                                                  ║${NC}"
echo -e "${BLUE}║ Passed:  ${GREEN}$PASSED${BLUE}                                                  ║${NC}"
echo -e "${BLUE}║ Failed:  ${RED}$FAILED${BLUE}                                                   ║${NC}"
echo -e "${BLUE}║ Skipped: ${YELLOW}$SKIPPED${BLUE}                                                  ║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║ Results: $RESULTS_DIR${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Code de sortie
if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
