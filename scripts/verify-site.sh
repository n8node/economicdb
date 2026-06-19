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

check() {
  local path="$1"
  local label="$2"
  local code
  code=$(curl -sf -o /dev/null -w "%{http_code}" "${BASE}${path}" || echo "000")
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "307" ]; then
    echo "OK   ${label} (${code})"
  else
    echo "FAIL ${label} (${code})"
  fi
}

echo "=== HTTP status ==="
check "/" "WordPress /"
check "/app" "Product /app"
check "/health" "API health"
check "/dbfiles/" "FileBrowser"

echo ""
echo "=== Cache-Control (must be no-store for HTML pages) ==="
for path in "/app" "/dbfiles/" "/"; do
  echo "--- ${path} ---"
  curl -sI "${BASE}${path}" | grep -iE '^(cache-control|pragma|expires|HTTP/)' || true
done

echo ""
echo "=== /app JS chunk sample (must exist, immutable cache OK) ==="
chunk=$(curl -sf "${BASE}/app" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -sf -o /dev/null -w "%{http_code}" "${BASE}${chunk}" || echo "000")
  echo "chunk ${chunk} -> ${code}"
else
  echo "WARNING: no JS chunk found in /app HTML"
fi

echo ""
echo "=== If all OK above but browser broken: clear site data for ${DOMAIN} (one time) ==="
