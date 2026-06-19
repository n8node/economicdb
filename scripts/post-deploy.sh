#!/bin/bash
# Полный post-deploy после git pull
set -euo pipefail

cd "$(dirname "$0")/.."

chmod +x scripts/*.sh

export BUILD_ID="$(git rev-parse --short HEAD 2>/dev/null || echo local)"
echo "=== BUILD_ID=${BUILD_ID} ==="

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
$COMPOSE up -d --build backend frontend worker

if [ -f scripts/apply-nginx-https.sh ]; then
  ./scripts/apply-nginx-https.sh
fi

bash scripts/restart-frontend.sh
bash scripts/verify-site.sh

echo ""
echo "=== Browser ==="
echo "If /app still broken: Ctrl+Shift+R or clear site data for economicdb.com once."
