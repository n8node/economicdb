#!/bin/bash
# Заполнить volume next_static, если entrypoint не успел / после первого деплоя
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

count=$($COMPOSE exec -T frontend sh -c 'find /app/.next/static -type f 2>/dev/null | wc -l' | tr -d " ")
staging=$($COMPOSE exec -T frontend sh -c 'find /opt/static-staging -type f 2>/dev/null | wc -l' | tr -d " ")

echo "volume files: ${count}, staging files: ${staging}"

if [ "${staging:-0}" -eq 0 ]; then
  echo "ERROR: /opt/static-staging empty — rebuild frontend: docker compose build frontend"
  exit 1
fi

if [ "${count:-0}" -eq 0 ]; then
  echo "=== Copy static into volume ==="
  $COMPOSE exec -T frontend sh -c 'cp -a /opt/static-staging/. /app/.next/static/'
fi

count=$($COMPOSE exec -T frontend sh -c 'find /app/.next/static -type f 2>/dev/null | wc -l' | tr -d " ")
echo "volume files after fix: ${count}"

$COMPOSE exec nginx nginx -s reload 2>/dev/null || true

chunk=$(curl -s "https://${DOMAIN:-economicdb.com}/app" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN:-economicdb.com}${chunk}")
  echo "${chunk} -> ${code}"
fi
