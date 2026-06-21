#!/bin/bash
# Проверить Next static/public assets внутри standalone image.
# next_static volume удалён: stale chunks не должны переживать rebuild.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

count=$($COMPOSE exec -T frontend sh -c 'find /app/.next/static -type f 2>/dev/null | wc -l' | tr -d " ")
public_nav=$($COMPOSE exec -T frontend sh -c 'test -f /app/public/macro-hard-navigation.js && echo yes || echo no' | tr -d " ")

echo "next static files: ${count}"
echo "hard navigation asset: ${public_nav}"

if [ "${count:-0}" -eq 0 ]; then
  echo "ERROR: /app/.next/static empty — rebuild frontend image"
  exit 1
fi

if [ "${public_nav:-no}" != "yes" ]; then
  echo "ERROR: /app/public/macro-hard-navigation.js missing — rebuild frontend image"
  exit 1
fi

$COMPOSE exec -T nginx nginx -s reload 2>/dev/null || NGINX_RELOAD=1 bash scripts/nginx-wait.sh

DOMAIN="${DOMAIN:-economicdb.com}"
chunk=$(curl -s "https://${DOMAIN}/app" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}${chunk}")
  echo "${chunk} -> ${code}"
fi
