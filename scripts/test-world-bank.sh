#!/bin/bash
# Проверка World Bank API из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== World Bank test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.world_bank.client import test_connection, WorldBankError

async def main():
    try:
        details = await test_connection()
        gdp = details["gdp_yoy_latest"]
        print(f"OK: ВВП РФ {gdp['value']}% ({gdp['date']})")
    except WorldBankError as exc:
        print("WORLD BANK ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
