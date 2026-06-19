#!/bin/bash
# Быстрая диагностика: 502, кеш, чанки, память
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

echo "=== Containers ==="
$COMPOSE ps

echo ""
echo "=== Memory / disk ==="
free -h 2>/dev/null || true
df -h / 2>/dev/null || true

echo ""
echo "=== HTTP ==="
for path in /health /app /adminus/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${path}" || echo "000")
  echo "${path} -> ${code}"
done

echo ""
echo "=== /app HTML deploy-id ==="
curl -s "${BASE}/app" | grep -o 'name="deploy-id" content="[^"]*"' || echo "deploy-id meta not found"

echo ""
echo "=== JS chunk from HTML ==="
html=$(curl -s "${BASE}/app")
chunk=$(echo "$html" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${chunk}")
  echo "${chunk} -> ${code}"
  if [ "$code" = "404" ]; then
    echo "FIX: bash scripts/fix-static-volume.sh"
  fi
else
  echo "no chunk in HTML"
fi

echo ""
echo "=== Cache-Control /app ==="
curl -s -D - -o /dev/null "${BASE}/app" | grep -iE '^(HTTP/|cache-control|pragma)' || true

echo ""
echo "=== Recent logs ==="
$COMPOSE logs nginx --tail=8 2>/dev/null || true
$COMPOSE logs frontend --tail=8 2>/dev/null || true

echo ""
echo "=== Static staging in image ==="
$COMPOSE exec -T frontend sh -c 'find /opt/static-staging -type f 2>/dev/null | wc -l' 2>/dev/null || echo "staging check failed"

echo ""
echo "=== Static volume (chunk count) ==="
$COMPOSE exec -T frontend sh -c 'find /app/.next/static -type f 2>/dev/null | wc -l' 2>/dev/null || echo "frontend exec failed"
