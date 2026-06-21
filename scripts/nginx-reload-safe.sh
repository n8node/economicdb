#!/bin/bash
# Reload nginx if running; start/recreate only when container is down or crash-looping.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"

bash scripts/validate-nginx-config.sh

state=$($COMPOSE ps nginx --format '{{.State}}' 2>/dev/null | head -1 || true)

if [ "$state" = "running" ]; then
  echo "=== nginx reload (keep connections, resolver picks new upstream IPs) ==="
  bash scripts/nginx-wait.sh
elif [ "$state" = "restarting" ]; then
  echo "=== nginx crash loop detected — recreating container ==="
  $COMPOSE up -d --force-recreate --no-deps nginx
  bash scripts/nginx-wait.sh
else
  echo "=== nginx start (state=${state:-missing}) ==="
  $COMPOSE up -d --no-deps nginx
  bash scripts/nginx-wait.sh
fi
