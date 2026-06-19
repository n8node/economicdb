#!/bin/bash
# Проверка доступности OECD SDMX (HICP EU г/г) из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== OECD test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.oecd.client import test_connection, OecdError

async def main():
    try:
        details = await test_connection()
        print("OK:", details)
    except OecdError as exc:
        print("OECD ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
