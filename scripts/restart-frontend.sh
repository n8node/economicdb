#!/bin/bash
# Пересборка frontend + reload nginx (убирает 502 после смены IP контейнера)
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ "${SKIP_BUILD:-0}" != "1" ]; then
  echo "=== Rebuild frontend ==="
  export BUILD_ID="${BUILD_ID:-$(git rev-parse --short HEAD 2>/dev/null || echo local)}"
  $COMPOSE build frontend
  $COMPOSE up -d --no-deps frontend
else
  echo "=== Skip frontend build (SKIP_BUILD=1) ==="
fi

echo "=== Wait for frontend (healthcheck or /app HTTP 200) ==="
for i in $(seq 1 60); do
  status=$($COMPOSE ps frontend --format '{{.Health}}' 2>/dev/null | head -1 || true)
  if [ "$status" = "healthy" ]; then
    echo "frontend healthy"
    break
  fi
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/app" || echo "000")
  if [ "$code" = "200" ]; then
    echo "frontend responds on /app (${code})"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "WARNING: frontend not ready after 5 min (health=${status:-unknown}, /app=${code})"
    $COMPOSE logs frontend --tail=40
    exit 1
  fi
  sleep 5
done

echo "=== Recreate nginx (fresh Docker DNS + config includes) ==="
bash scripts/validate-nginx-config.sh
$COMPOSE up -d --force-recreate --no-deps nginx

echo "=== Verify nginx (skip reload — container just started fresh) ==="
NGINX_RELOAD=0 bash scripts/nginx-wait.sh

echo "=== Ensure static assets are present ==="
bash scripts/fix-static-volume.sh

echo "=== Test /app ==="
curl -s -o /dev/null -w "https /app -> %{http_code}\n" "https://${DOMAIN}/app"
