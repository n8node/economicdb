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
        cpi = details["cpi_yoy_latest"]
        ind = details["industrial_yoy_latest"]
        print(f"OK: ИПЦ {cpi['value']}% ({cpi['date']}), пром. {ind['value']}% ({ind['date']})")
    except RosstatError as exc:
        print("ROSSTAT ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
