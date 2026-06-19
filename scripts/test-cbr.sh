#!/bin/bash
# Проверка доступности ЦБ РФ из backend-контейнера
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== DNS from backend ==="
$COMPOSE exec -T backend python -c "import socket; print('www.cbr.ru ->', socket.gethostbyname('www.cbr.ru'))"

echo ""
echo "=== CBR test from backend ==="
$COMPOSE exec -T backend python - <<'PY'
import asyncio
from app.integrations.cbr.client import test_connection, CbrError

async def main():
    try:
        details = await test_connection()
        print("OK:", details)
    except CbrError as exc:
        print("CBR ERROR:", exc.code, exc.message)
        raise SystemExit(1)

asyncio.run(main())
PY
