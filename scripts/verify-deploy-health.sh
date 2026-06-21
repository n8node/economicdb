#!/bin/bash
# Финальная проверка после деплоя: nginx running + HTTPS endpoints.
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
BASE="https://${DOMAIN}"

nginx_state=$($COMPOSE ps nginx --format '{{.State}}' 2>/dev/null | head -1 || true)
nginx_health=$($COMPOSE ps nginx --format '{{.Health}}' 2>/dev/null | head -1 || true)
echo "nginx: state=${nginx_state:-?} health=${nginx_health:-?}"
if [ "$nginx_state" != "running" ]; then
  echo "ERROR: nginx state is ${nginx_state:-unknown}, expected running"
  $COMPOSE ps nginx 2>/dev/null || true
  $COMPOSE logs nginx --tail=40 2>/dev/null || true
  exit 1
fi

failed=0
for path in /health /app /; do
  code=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code}" "${BASE}${path}" || echo "000")
  echo "${path} -> ${code}"
  if [ "$code" = "000" ] || [ "${code:0:1}" = "5" ]; then
    failed=1
  fi
done

if [ "$failed" -eq 1 ]; then
  echo "ERROR: deploy health check failed"
  exit 1
fi

echo "=== Deploy health OK ==="
