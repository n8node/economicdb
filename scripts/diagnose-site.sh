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

HTTPS_BASE="https://${DOMAIN}"
HTTP_BASE="http://${DOMAIN}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Containers ==="
$COMPOSE ps

echo ""
echo "=== Memory / disk ==="
free -h 2>/dev/null || true
df -h / 2>/dev/null || true

echo ""
echo "=== HTTPS ==="
for path in /health /app /adminus/; do
  code=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code}" "${HTTPS_BASE}${path}" || echo "000")
  echo "${path} -> ${code}"
done

echo ""
echo "=== HTTP fallback ==="
for path in /health /app /adminus/; do
  code=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code}" "${HTTP_BASE}${path}" || echo "000")
  echo "http ${path} -> ${code}"
done

echo ""
echo "=== HTTPS protocol checks ==="
curl -sS --http1.1 --connect-timeout 10 -o /dev/null -w "https http/1.1 /health -> %{http_code}\n" "${HTTPS_BASE}/health" || true
curl -sS --connect-timeout 10 -o /dev/null -w "https default /health -> %{http_code}\n" "${HTTPS_BASE}/health" || true

echo ""
echo "=== Nginx listeners ==="
ss -ltnp 2>/dev/null | grep -E ':(80|443)\s' || true
$COMPOSE exec -T nginx sh -c "nginx -T 2>/dev/null | grep -n 'listen 443\\|http2\\|keepalive_timeout\\|Alt-Svc'" || true

echo ""
echo "=== HTTP redirect (expect 301) ==="
curl -sS --connect-timeout 10 -o /dev/null -w "http / -> %{http_code}\n" "${HTTP_BASE}/" || true

echo ""
echo "=== /deploy-id ==="
curl -s --connect-timeout 5 "${HTTPS_BASE}/deploy-id" || echo "deploy-id failed"

echo ""
echo "=== /app HTML deploy-id ==="
curl -s --connect-timeout 10 "${HTTPS_BASE}/app" | grep -o 'name="deploy-id" content="[^"]*"' || echo "deploy-id meta not found"

echo ""
echo "=== JS chunk from HTML ==="
html=$(curl -s --connect-timeout 10 "${HTTPS_BASE}/app")
chunk=$(echo "$html" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s --connect-timeout 10 -o /dev/null -w "%{http_code}" "${HTTPS_BASE}${chunk}")
  echo "${chunk} -> ${code}"
  if [ "$code" = "404" ]; then
    echo "FIX: bash scripts/fix-static-volume.sh"
  fi
else
  echo "no chunk in HTML"
fi

echo ""
echo "=== Cache-Control /app ==="
curl -s --connect-timeout 10 -D - -o /dev/null "${HTTPS_BASE}/app" | grep -iE '^(HTTP/|cache-control|pragma|strict-transport-security|alt-svc|connection)' || true

echo ""
echo "=== Recent logs ==="
$COMPOSE logs nginx --tail=8 2>/dev/null || true
$COMPOSE logs frontend --tail=8 2>/dev/null || true

echo ""
echo "=== Static assets in image ==="
$COMPOSE exec -T frontend sh -c 'find /app/.next/static -type f 2>/dev/null | wc -l' 2>/dev/null || echo "static check failed"

echo ""
echo "=== Public hard-navigation asset ==="
$COMPOSE exec -T frontend sh -c 'ls -la /app/public/macro-hard-navigation.js 2>/dev/null || echo missing' 2>/dev/null || true
curl -s --connect-timeout 10 "${HTTPS_BASE}/macro-hard-navigation.js" | grep -o '__macroHardNavigation' || echo "hard navigation marker not found"
