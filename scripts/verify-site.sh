#!/bin/bash
# Проверка с сервера: сайт жив, заголовки no-cache на месте
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

BASE="https://${DOMAIN}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Reload nginx (refresh upstream DNS) ==="
$COMPOSE exec nginx nginx -s reload 2>/dev/null || true
sleep 2

check() {
  local path="$1"
  local label="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${path}")
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "307" ]; then
    echo "OK   ${label} (${code})"
  else
    echo "FAIL ${label} (${code})"
  fi
}

echo ""
echo "=== HTTP status ==="
check "/" "WordPress /"
check "/app" "Product /app"
check "/health" "API health"
check "/dbfiles/" "FileBrowser"

echo ""
echo "=== Cache-Control (GET, must be no-store for HTML pages) ==="
for path in "/app" "/dbfiles/" "/"; do
  echo "--- ${path} ---"
  curl -s -D - -o /dev/null "${BASE}${path}" | grep -iE '^(HTTP/|cache-control|pragma|expires)' || true
done

echo ""
echo "=== /app JS chunk sample (must exist, immutable cache OK) ==="
html=$(curl -s "${BASE}/app")
chunk=$(echo "$html" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${chunk}")
  echo "chunk ${chunk} -> ${code}"
else
  echo "WARNING: no JS chunk found in /app HTML"
  echo "$html" | head -3
fi

echo ""
if curl -s -o /dev/null -w "%{http_code}" "${BASE}/app" | grep -q 502; then
  echo "502 on /app: run ./scripts/restart-frontend.sh"
else
  echo "Server OK. If browser still broken: clear site data for ${DOMAIN} once."
fi
