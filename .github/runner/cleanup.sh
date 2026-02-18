#!/usr/bin/env bash
# Weekly cleanup for self-hosted runner environment
# Recommended: add to crontab
#   crontab -e
#   0 3 * * 0 /data/VarunaPoC/.github/runner/cleanup.sh >> /var/log/runner-cleanup.log 2>&1
set -euo pipefail

echo "=== Runner cleanup: $(date -Iseconds) ==="

echo "Pruning Docker images older than 7 days..."
docker image prune -af --filter "until=168h"

echo "Pruning buildx cache older than 7 days..."
docker buildx prune -af --filter "until=168h" 2>/dev/null || true

echo "Pruning unused volumes..."
docker volume prune -f

echo "Pruning unused networks..."
docker network prune -f

echo "=== Cleanup complete ==="
docker system df
