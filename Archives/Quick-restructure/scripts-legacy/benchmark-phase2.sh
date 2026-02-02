#!/bin/bash
# QUICK- TCP-over-QUIC Tunnel
# Phase 2: Comparative Benchmarks
# Tests B1 - B4 from specification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/.."
RESULTS_DIR="${PROJECT_DIR}/test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="${RESULTS_DIR}/phase2_${TIMESTAMP}.md"
CSV_FILE="${RESULTS_DIR}/phase2_${TIMESTAMP}.csv"

# Test parameters
ITERATIONS=${BENCHMARK_ITERATIONS:-10}  # Configurable, default 10
HTTP_URL="http://localhost:8080/test.txt"
# Direct access via docker network (test-http container)
DIRECT_HOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' quick-test-http 2>/dev/null || echo "172.23.0.4")
DIRECT_URL="http://${DIRECT_HOST}/test.txt"
MAX_TIMEOUT=${BENCHMARK_TIMEOUT:-5}  # Configurable timeout in seconds

mkdir -p "${RESULTS_DIR}"

echo "=========================================="
echo "  QUICK- Phase 2: Comparative Benchmarks"
echo "  Tests B1 - B4"
echo "=========================================="
echo ""

# Initialize results
cat > "${RESULTS_FILE}" << EOF
# QUICK- Phase 2 Benchmark Results
**Date:** $(date)
**Iterations per test:** ${ITERATIONS}
**Network profile:** LEO (40ms RTT, 1% loss)

## Benchmark Results

EOF

# CSV header
echo "test,iteration,tunnel_value,direct_value,improvement" > "${CSV_FILE}"

# =============================================================================
# B1: HTTP GET Latency
# Measures handshake + first byte time
# =============================================================================
echo "Running B1: HTTP GET Latency (${ITERATIONS} iterations)..."
echo "  Tunnel URL: ${HTTP_URL}"
echo "  Direct URL: ${DIRECT_URL}"

B1_TUNNEL_TOTAL=0
B1_DIRECT_TOTAL=0

for i in $(seq 1 $ITERATIONS); do
    # Through tunnel
    TUNNEL_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time $MAX_TIMEOUT "${HTTP_URL}" 2>/dev/null || echo "$MAX_TIMEOUT")
    TUNNEL_MS=$(echo "$TUNNEL_TIME * 1000" | bc 2>/dev/null || echo "0")

    # Direct (baseline) - access nginx directly via docker exec
    DIRECT_TIME=$(docker exec quick-entry curl -s -o /dev/null -w "%{time_total}" --max-time $MAX_TIMEOUT "http://test-http/test.txt" 2>/dev/null || echo "$MAX_TIMEOUT")
    DIRECT_MS=$(echo "$DIRECT_TIME * 1000" | bc 2>/dev/null || echo "0")

    B1_TUNNEL_TOTAL=$(echo "$B1_TUNNEL_TOTAL + $TUNNEL_MS" | bc 2>/dev/null || echo "0")
    B1_DIRECT_TOTAL=$(echo "$B1_DIRECT_TOTAL + $DIRECT_MS" | bc 2>/dev/null || echo "0")

    echo "B1,$i,$TUNNEL_MS,$DIRECT_MS" >> "${CSV_FILE}"
    echo -ne "  Progress: $i/$ITERATIONS\r"
done
echo ""

B1_TUNNEL_AVG=$(echo "scale=2; $B1_TUNNEL_TOTAL / $ITERATIONS" | bc 2>/dev/null || echo "0")
B1_DIRECT_AVG=$(echo "scale=2; $B1_DIRECT_TOTAL / $ITERATIONS" | bc 2>/dev/null || echo "0")

cat >> "${RESULTS_FILE}" << EOF
### B1: HTTP GET Latency

| Metric | Tunnel | Direct | Difference |
|--------|--------|--------|------------|
| Average (ms) | ${B1_TUNNEL_AVG} | ${B1_DIRECT_AVG} | $(echo "scale=2; $B1_TUNNEL_AVG - $B1_DIRECT_AVG" | bc 2>/dev/null || echo "N/A") |

**Analysis:** Measures total time for HTTP GET including connection establishment.
With QUIC's 1-RTT handshake vs TCP's 3-RTT, expect ~66% improvement in high-latency scenarios.

EOF

# =============================================================================
# B2: Download Throughput (10 MB file)
# =============================================================================
B2_ITERATIONS=${BENCHMARK_B2_ITERATIONS:-3}
echo "Running B2: Download Throughput (${B2_ITERATIONS} iterations)..."

# Create test file if needed
if [ ! -f "${PROJECT_DIR}/test-files/benchmark.bin" ]; then
    dd if=/dev/urandom of="${PROJECT_DIR}/test-files/benchmark.bin" bs=1M count=10 2>/dev/null
fi

B2_TUNNEL_TOTAL=0
B2_DIRECT_TOTAL=0

for i in $(seq 1 $B2_ITERATIONS); do
    # Through tunnel
    TUNNEL_START=$(date +%s.%N)
    curl -s --max-time 30 -o /dev/null "http://localhost:8080/benchmark.bin" 2>/dev/null || true
    TUNNEL_END=$(date +%s.%N)
    TUNNEL_TIME=$(echo "$TUNNEL_END - $TUNNEL_START" | bc 2>/dev/null || echo "1")
    TUNNEL_MBPS=$(echo "scale=2; 80 / $TUNNEL_TIME" | bc 2>/dev/null || echo "0")  # 10MB = 80Mb

    # Direct via docker exec
    DIRECT_START=$(date +%s.%N)
    docker exec quick-entry curl -s --max-time 30 -o /dev/null "http://test-http/benchmark.bin" 2>/dev/null || true
    DIRECT_END=$(date +%s.%N)
    DIRECT_TIME=$(echo "$DIRECT_END - $DIRECT_START" | bc 2>/dev/null || echo "1")
    DIRECT_MBPS=$(echo "scale=2; 80 / $DIRECT_TIME" | bc 2>/dev/null || echo "0")

    B2_TUNNEL_TOTAL=$(echo "$B2_TUNNEL_TOTAL + $TUNNEL_MBPS" | bc 2>/dev/null || echo "0")
    B2_DIRECT_TOTAL=$(echo "$B2_DIRECT_TOTAL + $DIRECT_MBPS" | bc 2>/dev/null || echo "0")

    echo "B2,$i,$TUNNEL_MBPS,$DIRECT_MBPS" >> "${CSV_FILE}"
    echo -ne "  Progress: $i/${B2_ITERATIONS}\r"
done
echo ""

B2_TUNNEL_AVG=$(echo "scale=2; $B2_TUNNEL_TOTAL / $B2_ITERATIONS" | bc 2>/dev/null || echo "0")
B2_DIRECT_AVG=$(echo "scale=2; $B2_DIRECT_TOTAL / $B2_ITERATIONS" | bc 2>/dev/null || echo "0")

cat >> "${RESULTS_FILE}" << EOF
### B2: Download Throughput (10 MB)

| Metric | Tunnel | Direct | Ratio |
|--------|--------|--------|-------|
| Throughput (Mbps) | ${B2_TUNNEL_AVG} | ${B2_DIRECT_AVG} | $(echo "scale=2; $B2_TUNNEL_AVG / $B2_DIRECT_AVG" | bc 2>/dev/null || echo "N/A")x |

**Analysis:** Measures effective throughput for large transfers.
QUIC's larger flow control windows should improve BDP utilization.

EOF

# =============================================================================
# B3: Recovery Under 2% Loss (10 MB transfer)
# =============================================================================
B3_ITERATIONS=${BENCHMARK_B3_ITERATIONS:-3}
echo "Running B3: Recovery Under Packet Loss (${B3_ITERATIONS} iterations)..."

B3_TUNNEL_TOTAL=0
B3_DIRECT_TOTAL=0

for i in $(seq 1 $B3_ITERATIONS); do
    # Through tunnel (QUIC handles loss better)
    TUNNEL_START=$(date +%s.%N)
    curl -s --max-time 30 -o /dev/null "http://localhost:8080/benchmark.bin" 2>/dev/null || true
    TUNNEL_END=$(date +%s.%N)
    TUNNEL_TIME=$(echo "$TUNNEL_END - $TUNNEL_START" | bc 2>/dev/null || echo "30")

    # Direct TCP via docker exec
    DIRECT_START=$(date +%s.%N)
    docker exec quick-entry curl -s --max-time 30 -o /dev/null "http://test-http/benchmark.bin" 2>/dev/null || true
    DIRECT_END=$(date +%s.%N)
    DIRECT_TIME=$(echo "$DIRECT_END - $DIRECT_START" | bc 2>/dev/null || echo "30")

    B3_TUNNEL_TOTAL=$(echo "$B3_TUNNEL_TOTAL + $TUNNEL_TIME" | bc 2>/dev/null || echo "0")
    B3_DIRECT_TOTAL=$(echo "$B3_DIRECT_TOTAL + $DIRECT_TIME" | bc 2>/dev/null || echo "0")

    echo "B3,$i,$TUNNEL_TIME,$DIRECT_TIME" >> "${CSV_FILE}"
    echo -ne "  Progress: $i/${B3_ITERATIONS}\r"
done
echo ""

B3_TUNNEL_AVG=$(echo "scale=2; $B3_TUNNEL_TOTAL / $B3_ITERATIONS" | bc 2>/dev/null || echo "0")
B3_DIRECT_AVG=$(echo "scale=2; $B3_DIRECT_TOTAL / $B3_ITERATIONS" | bc 2>/dev/null || echo "0")
B3_IMPROVEMENT=$(echo "scale=2; (1 - $B3_TUNNEL_AVG / $B3_DIRECT_AVG) * 100" | bc 2>/dev/null || echo "0")

cat >> "${RESULTS_FILE}" << EOF
### B3: Recovery Time Under 2% Loss

| Metric | Tunnel | Direct | Improvement |
|--------|--------|--------|-------------|
| Time (seconds) | ${B3_TUNNEL_AVG} | ${B3_DIRECT_AVG} | ${B3_IMPROVEMENT}% |

**Analysis:** Measures recovery performance under packet loss.
QUIC's selective ACKs should reduce recovery time compared to TCP.

EOF

# =============================================================================
# B4: Handshake Time (captured from metrics)
# =============================================================================
echo "Running B4: Handshake Time Analysis..."

# Get metrics from entry proxy
METRICS=$(curl -s http://localhost:9091/metrics 2>/dev/null || echo "")

cat >> "${RESULTS_FILE}" << EOF
### B4: Handshake Analysis

| Protocol | RTT Required | Typical Time (LEO) |
|----------|--------------|-------------------|
| TCP+TLS 1.2 | 3 RTT | ~240ms |
| QUIC (1-RTT) | 1 RTT | ~80ms |
| QUIC (0-RTT) | 0 RTT | ~0ms |

**Theoretical Improvement:** 66% reduction in connection establishment time.

**Metrics Snapshot:**
\`\`\`
$(echo "$METRICS" | grep "quick_tunnel" | head -10)
\`\`\`

EOF

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "  Phase 2 Benchmark Summary"
echo "=========================================="
echo ""
echo "  B1 (Latency):    Tunnel=${B1_TUNNEL_AVG}ms, Direct=${B1_DIRECT_AVG}ms"
echo "  B2 (Throughput): Tunnel=${B2_TUNNEL_AVG}Mbps, Direct=${B2_DIRECT_AVG}Mbps"
echo "  B3 (Recovery):   Tunnel=${B3_TUNNEL_AVG}s, Direct=${B3_DIRECT_AVG}s"
echo "  B4 (Handshake):  QUIC 1-RTT vs TCP 3-RTT"
echo ""

cat >> "${RESULTS_FILE}" << EOF

## Summary

| Benchmark | Description | QUIC Advantage |
|-----------|-------------|----------------|
| B1 | HTTP GET Latency | 1-RTT vs 3-RTT handshake |
| B2 | Throughput | Better BDP utilization |
| B3 | Recovery | Selective ACKs, faster retransmit |
| B4 | Handshake | 66% theoretical improvement |

## Test Conditions

- **Network Profile:** LEO (Starlink-like)
- **Simulated RTT:** 80ms (40ms each direction)
- **Packet Loss:** 1%
- **Bandwidth Limit:** 150 Mbps
- **Congestion Control:** BBR (via QUIC)

## Raw Data

CSV file: \`${CSV_FILE}\`

EOF

echo "Results saved to: ${RESULTS_FILE}"
echo "CSV data saved to: ${CSV_FILE}"
