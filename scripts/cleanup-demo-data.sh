#!/bin/bash
# Удаляет demo/mock данные и оставляет только ряды реальных провайдеров.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

$COMPOSE exec -T backend python -m app.maintenance.cleanup_demo_data

echo "=== Cleanup complete ==="
echo "Run provider sync from /adminus/providers if some provider was disabled during cleanup."
