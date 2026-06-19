#!/bin/bash
# Отключить кэш WordPress в nginx (после смены HTTP→HTTPS)
set -euo pipefail

cd /opt/economicdb
set -a
# shellcheck disable=SC1091
source .env
set +a

DOMAIN="${DOMAIN:-economicdb.com}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Apply HTTPS nginx with no-cache headers ==="
cp nginx/templates/https.conf.template nginx/conf.d/https.conf
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/https.conf

$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo ""
echo "=== Verify Cache-Control on install page ==="
curl -sI "https://$DOMAIN/wp-admin/install.php" | grep -iE 'cache-control|pragma|expires' || true

echo ""
echo "=== Done (server) ==="
echo "Browsers still need one-time cleanup for economicdb.com — see instructions in chat."
