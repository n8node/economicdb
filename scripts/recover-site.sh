#!/bin/bash
# Экстренное восстановление: sync, nginx conf, recreate nginx, health check.
set -euo pipefail

cd /opt/economicdb

BRANCH="${DEPLOY_BRANCH:-main}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Recover: sync origin/${BRANCH} ==="
git fetch origin "$BRANCH"
git reset --hard "origin/${BRANCH}"
chmod +x scripts/*.sh

echo "=== Recover: nginx config ==="
bash scripts/generate-nginx-https-conf.sh
bash scripts/validate-nginx-config.sh

echo "=== Recover: recreate nginx ==="
$COMPOSE build nginx
$COMPOSE up -d --force-recreate --no-deps nginx
bash scripts/nginx-wait.sh

echo "=== Recover: verify ==="
sleep 2
curl -sf https://economicdb.com/health && echo " health OK" || {
  echo "ERROR: health check failed"
  $COMPOSE ps
  $COMPOSE logs nginx --tail=40
  exit 1
}

bash scripts/diagnose-site.sh
