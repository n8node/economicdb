#!/bin/bash
# Проверка доступности Росстата (ИПЦ г/г) из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Rosstat test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.rosstat.client import test_connection, RosstatError

async def main():
    try:
        details = await test_connection()
        print("OK:", details)
    except RosstatError as exc:
        print("ROSSTAT ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
