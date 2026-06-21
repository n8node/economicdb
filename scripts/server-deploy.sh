#!/bin/bash
# Деплой на сервере: последовательная сборка, без простоя nginx дольше нужного
set -euo pipefail

cd /opt/economicdb

BRANCH="${DEPLOY_BRANCH:-main}"
echo "=== Sync repo to origin/${BRANCH} ==="
OLD_REV="$(git rev-parse HEAD)"
git fetch origin "$BRANCH"
# Deploy server: discard local edits to tracked files (nginx conf.d is regenerated below).
git reset --hard "origin/${BRANCH}"
NEW_REV="$(git rev-parse HEAD)"

if [ "$OLD_REV" = "$NEW_REV" ]; then
  echo "Already up to date ($(git rev-parse --short HEAD))"
else
  echo "Updating $(git rev-parse --short "$OLD_REV")..$(git rev-parse --short "$NEW_REV")"
  git log --oneline --no-decorate "${OLD_REV}..${NEW_REV}"
  git diff --stat "${OLD_REV}" "${NEW_REV}"
fi

chmod +x scripts/*.sh
export BUILD_ID="$(git rev-parse --short HEAD 2>/dev/null || echo local)"
echo "=== BUILD_ID=${BUILD_ID} ==="

# Конфиг nginx на диск до recreate контейнера — избегаем crash loop на старом conf
bash scripts/generate-nginx-https-conf.sh
bash scripts/validate-nginx-config.sh

SERVICES="${1:-}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

if [ -n "$SERVICES" ]; then
  $COMPOSE build $SERVICES
  $COMPOSE up -d $SERVICES
else
  echo "=== Build backend + worker + frontend (sequential) ==="
  $COMPOSE build backend
  $COMPOSE build worker
  $COMPOSE build frontend
  $COMPOSE build nginx
  $COMPOSE up -d backend worker
  $COMPOSE up -d --force-recreate --no-deps frontend
  # Wait for frontend, then recreate nginx — never recreate nginx before frontend is ready
  SKIP_BUILD=1 bash scripts/restart-frontend.sh
fi

bash scripts/verify-deploy-health.sh
bash scripts/diagnose-site.sh
