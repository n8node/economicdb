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
FB_CLI=(run --rm --no-deps --entrypoint /filebrowser filebrowser)

fb_cli() {
  $COMPOSE "${FB_CLI[@]}" "$@"
}

echo "=== Configuring FileBrowser user (server must be stopped for DB access) ==="
$COMPOSE stop filebrowser 2>/dev/null || true

if ! fb_cli users find "$FILEBROWSER_USERNAME" --database /database/filebrowser.db >/dev/null 2>&1; then
  echo "Creating user ${FILEBROWSER_USERNAME}..."
  fb_cli users add "$FILEBROWSER_USERNAME" "$FILEBROWSER_PASSWORD" \
    --perm.admin \
    --database /database/filebrowser.db
else
  echo "Updating password for ${FILEBROWSER_USERNAME}..."
  fb_cli users update "$FILEBROWSER_USERNAME" \
    --password "$FILEBROWSER_PASSWORD" \
    --database /database/filebrowser.db
fi

echo "=== Starting FileBrowser ==="
$COMPOSE up -d filebrowser

"$(dirname "$0")/apply-nginx-https.sh"

echo
echo "=== FileBrowser ready ==="
echo "URL:  https://${DOMAIN:-economicdb.com}${FILEBROWSER_BASE_PATH}/"
echo "User: ${FILEBROWSER_USERNAME}"
echo "Edit .env: /srv/.env (root of project in UI)"
echo
echo "IMPORTANT: keep FILEBROWSER_PASSWORD secret; do not share the /dbfiles URL."
