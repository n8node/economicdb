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
echo "=== HTTPS protocol checks ==="
curl -sS --http1.1 --connect-timeout 10 -o /dev/null -w "https http/1.1 /health -> %{http_code}\n" "${BASE}/health" || true
curl -sS --connect-timeout 10 -o /dev/null -w "https default /health -> %{http_code}\n" "${BASE}/health" || true

echo ""
echo "=== Nginx listeners ==="
ss -ltnp 2>/dev/null | grep -E ':(80|443)\s' || true
$COMPOSE exec -T nginx sh -c "nginx -T 2>/dev/null | grep -n 'listen 443\\|http2'" || true

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
echo "=== Static volume (/data/next-static) ==="
$COMPOSE exec -T frontend sh -c 'find /data/next-static -type f 2>/dev/null | wc -l' 2>/dev/null || echo "volume check failed"

echo ""
echo "=== Symlink /app/.next/static ==="
$COMPOSE exec -T frontend sh -c 'ls -la /app/.next/static 2>/dev/null || echo missing' 2>/dev/null || true
