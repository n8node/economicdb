#!/bin/bash
# Проверка ECB / Eurostat из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== ECB/Eurostat test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.ecb_eurostat.client import test_connection, EcbEurostatError

async def main():
    try:
        details = await test_connection()
        dep = details["key_rate_latest"]
        hicp = details["hicp_yoy_latest"]
        print(f"OK: ECB {dep['value']}% ({dep['date']}), HICP {hicp['value']}% ({hicp['date']})")
    except EcbEurostatError as exc:
        print("ECB/EUROSTAT ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
