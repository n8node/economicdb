#!/bin/bash
# Проверка доступности IMF DataMapper (ВВП Китая real YoY) из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== IMF test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.imf.client import test_connection, ImfError

async def main():
    try:
        details = await test_connection()
        print("OK:", details)
    except ImfError as exc:
        print("IMF ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
