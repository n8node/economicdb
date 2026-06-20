#!/bin/bash
# Применить HTTPS nginx из шаблона и reload (no-cache для /app, WP и т.д.)
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f nginx/templates/https.conf.template ]; then
  echo "ERROR: nginx/templates/https.conf.template not found"
  exit 1
fi

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

cp nginx/templates/https.conf.template nginx/conf.d/https.conf
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/https.conf

cp nginx/templates/default.http-redirect.conf nginx/conf.d/default.conf
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/default.conf

$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo "=== HTTPS nginx applied for ${DOMAIN} ==="
