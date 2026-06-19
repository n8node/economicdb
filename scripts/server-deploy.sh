#!/bin/bash
# Деплой на сервере: git pull + rebuild (make не нужен)
set -euo pipefail

cd /opt/economicdb
git pull origin main

SERVICES="${1:-}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ -n "$SERVICES" ]; then
  $COMPOSE up -d --build $SERVICES
else
  $COMPOSE up -d --build
fi

# Применить nginx с Docker DNS и no-cache (если шаблон обновился)
if [ -f scripts/apply-nginx-https.sh ]; then
  chmod +x scripts/apply-nginx-https.sh
  ./scripts/apply-nginx-https.sh
fi

sleep 5
curl -sf https://economicdb.com/health && echo " health OK" || echo "WARNING: health failed"
curl -sf https://economicdb.com/app -o /dev/null && echo "/app OK" || echo "WARNING: /app failed"
echo "=== Done ==="
