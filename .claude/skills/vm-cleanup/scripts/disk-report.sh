#!/bin/bash
# Disk usage report for VarunaPoC VM cleanup decisions
# Run: bash .claude/skills/vm-cleanup/scripts/disk-report.sh

set -euo pipefail

echo "=========================================="
echo "  VarunaPoC VM Disk Report"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "=========================================="

echo ""
echo "--- Filesystem Usage ---"
df -h / /data 2>/dev/null || df -h /

echo ""
echo "--- Docker Usage ---"
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker system df 2>/dev/null || echo "Docker not accessible"
else
    echo "Docker not available"
fi

echo ""
echo "--- Project Heavy Dirs ---"
for dir in \
    backend/venv \
    backend/.venv \
    frontend/node_modules \
    frontend/dist \
    frontend/test-results \
    frontend/e2e/test-results \
    frontend/e2e/playwright-report \
    native/quiche-cloudflare/target \
    .pytest_cache \
    .ruff_cache \
    Slides; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        printf "  %-45s %s\n" "$dir" "$size"
    fi
done

echo ""
echo "--- System Caches (root fs) ---"
for dir in /root/.cache /root/.cargo /root/.npm /root/.local; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        printf "  %-45s %s\n" "$dir" "$size"
    fi
done

echo ""
echo "--- Temp Files ---"
tmp_count=$(find /tmp -maxdepth 1 -type f 2>/dev/null | wc -l)
tmp_size=$(du -sh /tmp 2>/dev/null | cut -f1)
echo "  /tmp: $tmp_count files, $tmp_size total"

echo ""
ROOT_USE=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d '% ')
if [ "${ROOT_USE:-0}" -gt 80 ]; then
    echo "WARNING: Root filesystem at ${ROOT_USE}% - cleanup recommended"
else
    echo "Root filesystem at ${ROOT_USE}% - OK"
fi
echo "=========================================="
