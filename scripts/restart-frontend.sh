#!/bin/bash
# Пересборка frontend + reload nginx (убирает 502 после смены IP контейнера)
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Rebuild frontend ==="
$COMPOSE up -d --build frontend

echo "=== Wait for frontend healthy ==="
for i in $(seq 1 60); do
  status=$($COMPOSE ps frontend --format '{{.Health}}' 2>/dev/null || true)
  if [ "$status" = "healthy" ]; then
    echo "frontend healthy"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "WARNING: frontend not healthy after 5 min"
    $COMPOSE logs frontend --tail=40
    exit 1
  fi
  sleep 5
done

echo "=== Reload nginx (refresh Docker DNS) ==="
$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo "=== Test /app ==="
curl -s -o /dev/null -w "https /app -> %{http_code}\n" "https://${DOMAIN:-economicdb.com}/app"
