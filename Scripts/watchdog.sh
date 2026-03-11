#!/usr/bin/env bash
# VarunaPoC External Uptime Watchdog
#
# Checks /api/health endpoint and alerts on consecutive failures.
# Runs independently of the monitoring stack (Prometheus/Grafana).
#
# Usage:
#   ./watchdog.sh                    # Run once (for cron)
#   WATCHDOG_LOOP=1 ./watchdog.sh    # Run continuously (for systemd)
#
# Cron example (every 5 minutes):
#   */5 * * * * /opt/varuna/scripts/watchdog.sh >> /var/log/varuna-watchdog.log 2>&1
#
# Environment variables:
#   VARUNA_URL          Base URL to check (default: https://localhost)
#   WATCHDOG_THRESHOLD  Consecutive failures before alert (default: 3)
#   WATCHDOG_INTERVAL   Seconds between checks in loop mode (default: 300)
#   WATCHDOG_LOOP       Set to 1 for continuous mode (default: single check)
#   ALERT_EMAIL         Email address for alerts (optional)
#   ALERT_WEBHOOK       Webhook URL for alerts (Slack/Teams, optional)
#   MAINTENANCE_FILE    If this file exists, skip checks (default: /tmp/varuna-maintenance)

set -euo pipefail

VARUNA_URL="${VARUNA_URL:-https://localhost}"
THRESHOLD="${WATCHDOG_THRESHOLD:-3}"
INTERVAL="${WATCHDOG_INTERVAL:-300}"
LOOP="${WATCHDOG_LOOP:-0}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"
MAINTENANCE_FILE="${MAINTENANCE_FILE:-/tmp/varuna-maintenance}"
STATE_FILE="/tmp/varuna-watchdog-failures"

check_health() {
    # Check maintenance mode
    if [ -f "$MAINTENANCE_FILE" ]; then
        echo "$(date -Iseconds) MAINTENANCE: Checks suspended (${MAINTENANCE_FILE} exists)"
        return 0
    fi

    local http_code
    http_code=$(curl -sk -o /dev/null -w '%{http_code}' \
        --connect-timeout 10 --max-time 30 \
        "${VARUNA_URL}/api/health" 2>/dev/null || echo "000")

    if [ "$http_code" = "200" ]; then
        echo "$(date -Iseconds) OK: ${VARUNA_URL}/api/health returned ${http_code}"
        # Reset failure counter
        echo "0" > "$STATE_FILE"
        return 0
    fi

    # Increment failure counter
    local failures=0
    if [ -f "$STATE_FILE" ]; then
        failures=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
    fi
    failures=$((failures + 1))
    echo "$failures" > "$STATE_FILE"

    echo "$(date -Iseconds) FAIL: ${VARUNA_URL}/api/health returned ${http_code} (${failures}/${THRESHOLD})"

    if [ "$failures" -ge "$THRESHOLD" ]; then
        send_alert "$http_code" "$failures"
    fi
}

send_alert() {
    local http_code="$1"
    local failures="$2"
    local message="VarunaPoC DOWN: ${VARUNA_URL}/api/health returned ${http_code} (${failures} consecutive failures)"

    echo "$(date -Iseconds) ALERT: ${message}"

    # Email alert
    if [ -n "$ALERT_EMAIL" ] && command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "ALERT: VarunaPoC is DOWN" "$ALERT_EMAIL"
        echo "$(date -Iseconds) Alert sent to ${ALERT_EMAIL}"
    fi

    # Webhook alert (Slack/Teams compatible)
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -sk -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\": \"${message}\"}" \
            --max-time 10 >/dev/null 2>&1 || true
        echo "$(date -Iseconds) Alert sent to webhook"
    fi
}

# Initialize state file
if [ ! -f "$STATE_FILE" ]; then
    echo "0" > "$STATE_FILE"
fi

if [ "$LOOP" = "1" ]; then
    echo "$(date -Iseconds) Watchdog starting (loop mode, interval=${INTERVAL}s, threshold=${THRESHOLD})"
    while true; do
        check_health
        sleep "$INTERVAL"
    done
else
    check_health
fi
