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

# Применить nginx с Docker DNS (если шаблон обновился)
if [ -f nginx/templates/https.conf.template ]; then
  DOMAIN="${DOMAIN:-economicdb.com}"
  # shellcheck disable=SC1091
  [ -f .env ] && source .env
  cp nginx/templates/https.conf.template nginx/conf.d/https.conf
  sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/https.conf
fi

$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

sleep 5
curl -sf https://economicdb.com/health && echo " health OK" || echo "WARNING: health failed"
curl -sf https://economicdb.com/app -o /dev/null && echo "/app OK" || echo "WARNING: /app failed"
echo "=== Done ==="
