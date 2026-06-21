#!/bin/bash
# Проверка nginx -t в одноразовом контейнере (до recreate/reload).
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="${COMPOSE:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"

echo "=== nginx -t (validate) ==="
$COMPOSE run --rm --no-deps nginx nginx -t
echo "nginx config OK"
