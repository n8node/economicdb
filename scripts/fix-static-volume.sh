#!/bin/bash
# Заполнить volume next_static и проверить symlink
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

count=$($COMPOSE exec -T frontend sh -c 'find /data/next-static -type f 2>/dev/null | wc -l' | tr -d " ")
staging=$($COMPOSE exec -T frontend sh -c 'find /opt/static-staging -type f 2>/dev/null | wc -l' | tr -d " ")

echo "volume files: ${count}, staging files: ${staging}"

if [ "${staging:-0}" -eq 0 ]; then
  echo "ERROR: /opt/static-staging empty — rebuild frontend image"
  exit 1
fi

$COMPOSE exec -T frontend sh -c '
  set -eu
  mkdir -p /data/next-static
  rm -rf /data/next-static/*
  cp -a /opt/static-staging/. /data/next-static/
  mkdir -p /app/.next
  if [ -e /app/.next/static ] && [ ! -L /app/.next/static ]; then
    rm -rf /app/.next/static
  fi
  ln -sfn /data/next-static /app/.next/static
  find /data/next-static -type f | wc -l
'

count=$($COMPOSE exec -T frontend sh -c 'find /data/next-static -type f 2>/dev/null | wc -l' | tr -d " ")
echo "volume files after fix: ${count}"

if [ "${count:-0}" -eq 0 ]; then
  echo "ERROR: static volume still empty"
  exit 1
fi

$COMPOSE exec nginx nginx -s reload 2>/dev/null || true

DOMAIN="${DOMAIN:-economicdb.com}"
chunk=$(curl -s "https://${DOMAIN}/app" | grep -oE '/_next/static/[^"]+\.js' | head -1 || true)
if [ -n "$chunk" ]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}${chunk}")
  echo "${chunk} -> ${code}"
fi
