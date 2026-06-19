#!/bin/bash
# Проверка MOEX ISS из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== MOEX test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.moex.client import test_connection, MoexError

async def main():
    try:
        details = await test_connection()
        idx = details["index_latest"]
        print(f"OK: {idx['security']} {idx['value']} ({idx['date']})")
    except MoexError as exc:
        print("MOEX ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
