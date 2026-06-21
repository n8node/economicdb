#!/bin/bash
# Применить HTTPS nginx из шаблона и reload (no-cache для /app, WP и т.д.)
set -euo pipefail

cd "$(dirname "$0")/.."

bash scripts/generate-nginx-https-conf.sh
bash scripts/validate-nginx-config.sh
bash scripts/nginx-wait.sh

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

echo "=== HTTPS nginx applied for ${DOMAIN} ==="
