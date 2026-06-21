#!/bin/bash
# Деплой на сервере: последовательная сборка, без простоя nginx дольше нужного
set -euo pipefail

cd /opt/economicdb
git checkout -- .
git pull origin main

chmod +x scripts/*.sh
export BUILD_ID="$(git rev-parse --short HEAD 2>/dev/null || echo local)"
echo "=== BUILD_ID=${BUILD_ID} ==="

SERVICES="${1:-}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ -n "$SERVICES" ]; then
  $COMPOSE build $SERVICES
  $COMPOSE up -d $SERVICES
else
  echo "=== Build backend + worker + frontend (sequential) ==="
  $COMPOSE build backend
  $COMPOSE build worker
  $COMPOSE build frontend
  $COMPOSE build nginx
  $COMPOSE up -d backend worker
  $COMPOSE up -d --force-recreate --no-deps frontend
  # Wait for frontend, then recreate nginx — never recreate nginx before frontend is ready
  SKIP_BUILD=1 bash scripts/restart-frontend.sh
fi

if [ -f scripts/apply-nginx-https.sh ]; then
  ./scripts/apply-nginx-https.sh
fi

bash scripts/fix-static-volume.sh

sleep 3
curl -sf https://economicdb.com/health && echo " health OK" || echo "WARNING: health failed"
bash scripts/diagnose-site.sh
