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

sleep 5
curl -sf https://economicdb.com/health && echo " OK" || echo "WARNING: health check failed"
echo "=== Done ==="
