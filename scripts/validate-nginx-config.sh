#!/bin/bash
# Проверка nginx -t в одноразовом контейнере (до recreate/reload).
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"

echo "=== nginx -t (validate) ==="
if $COMPOSE run --rm --no-deps nginx nginx -t; then
  echo "nginx config OK"
  exit 0
fi

echo "=== nginx validate retry: ensuring upstream containers are running ==="
$COMPOSE up -d postgres redis backend frontend wordpress >/dev/null
$COMPOSE run --rm --no-deps nginx nginx -t
echo "nginx config OK"
