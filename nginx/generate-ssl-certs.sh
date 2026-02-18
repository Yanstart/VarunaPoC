#!/usr/bin/env bash
# Generate self-signed SSL certificates for VarunaPoC development/testing.
# For production, replace with real certificates from your CA or Let's Encrypt.
#
# Usage:
#   ./nginx/generate-ssl-certs.sh
#   docker compose -f docker-compose.production.yml up -d
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="${SCRIPT_DIR}/ssl"

mkdir -p "${SSL_DIR}"

if [ -f "${SSL_DIR}/varuna.crt" ] && [ -f "${SSL_DIR}/varuna.key" ]; then
    echo "[INFO] Certificates already exist in ${SSL_DIR}/"
    echo "       Delete them first if you want to regenerate."
    exit 0
fi

echo "[INFO] Generating self-signed SSL certificate..."

openssl req -x509 -nodes \
    -days 365 \
    -newkey rsa:2048 \
    -keyout "${SSL_DIR}/varuna.key" \
    -out "${SSL_DIR}/varuna.crt" \
    -subj "/C=BE/ST=Namur/L=Yvoir/O=CHU UCL Namur/OU=Anatomopathologie/CN=varuna.chu-ucl.be" \
    -addext "subjectAltName=DNS:varuna.chu-ucl.be,DNS:localhost,IP:127.0.0.1"

chmod 600 "${SSL_DIR}/varuna.key"
chmod 644 "${SSL_DIR}/varuna.crt"

echo "[OK] Certificates generated:"
echo "     ${SSL_DIR}/varuna.crt"
echo "     ${SSL_DIR}/varuna.key"
echo ""
echo "For production, replace these with certificates from your CA."
