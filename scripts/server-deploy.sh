#!/bin/bash
# Деплой на сервере: git pull + rebuild (make не нужен)
set -euo pipefail

cd /opt/economicdb
git pull origin main

chmod +x scripts/*.sh
export BUILD_ID="$(git rev-parse --short HEAD 2>/dev/null || echo local)"
echo "=== BUILD_ID=${BUILD_ID} ==="

SERVICES="${1:-}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ -n "$SERVICES" ]; then
  $COMPOSE up -d --build $SERVICES
else
  $COMPOSE up -d --build backend frontend worker
fi

if [ -f scripts/apply-nginx-https.sh ]; then
  ./scripts/apply-nginx-https.sh
fi

bash scripts/restart-frontend.sh

sleep 5
curl -sf https://economicdb.com/health && echo " health OK" || echo "WARNING: health failed"
curl -sf https://economicdb.com/app -o /dev/null && echo "/app OK" || echo "WARNING: /app failed — run bash scripts/verify-site.sh"
echo "=== Done ==="
echo "Browser: Ctrl+Shift+R if old UI; or clear site data for economicdb.com once."
