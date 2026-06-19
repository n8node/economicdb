#!/bin/bash
# Включение веб-файлового менеджера FileBrowser за nginx (/dbfiles).
# Запуск на сервере: cd /opt/economicdb && ./scripts/enable-filebrowser.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy from .env.example and set FILEBROWSER_PASSWORD."
  exit 1
fi

# shellcheck disable=SC1091
source .env

if [ -z "${FILEBROWSER_PASSWORD:-}" ] || [ "$FILEBROWSER_PASSWORD" = "CHANGE_ME_strong_filebrowser_password" ]; then
  echo "ERROR: Set a strong FILEBROWSER_PASSWORD in .env before enabling FileBrowser."
  exit 1
fi

FILEBROWSER_USERNAME="${FILEBROWSER_USERNAME:-admin}"
FILEBROWSER_BASE_PATH="${FILEBROWSER_BASE_PATH:-/dbfiles}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Starting FileBrowser ==="
$COMPOSE up -d filebrowser

echo "=== Setting FileBrowser login ==="
sleep 3
if $COMPOSE exec -T filebrowser filebrowser users ls --database /database/filebrowser.db 2>/dev/null | grep -q "$FILEBROWSER_USERNAME"; then
  $COMPOSE exec -T filebrowser filebrowser users update "$FILEBROWSER_USERNAME" \
    --password "$FILEBROWSER_PASSWORD" \
    --database /database/filebrowser.db
else
  $COMPOSE exec -T filebrowser filebrowser users add "$FILEBROWSER_USERNAME" "$FILEBROWSER_PASSWORD" \
    --perm.admin \
    --database /database/filebrowser.db
fi

if [ -f nginx/templates/https.conf.template ]; then
  DOMAIN="${DOMAIN:-economicdb.com}"
  cp nginx/templates/https.conf.template nginx/conf.d/https.conf
  sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/https.conf
fi

echo "=== Reloading nginx ==="
$COMPOSE up -d nginx
$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo
echo "=== FileBrowser ready ==="
echo "URL:  https://${DOMAIN:-economicdb.com}${FILEBROWSER_BASE_PATH}/"
echo "User: ${FILEBROWSER_USERNAME}"
echo "Edit .env: /srv/.env (root of project in UI)"
echo
echo "IMPORTANT: keep FILEBROWSER_PASSWORD secret; do not share the /dbfiles URL."
