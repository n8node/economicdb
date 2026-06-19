#!/bin/bash
# Починить FileBrowser за nginx (/dbfiles): baseurl + nginx reload
set -euo pipefail

cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source .env

FILEBROWSER_USERNAME="${FILEBROWSER_USERNAME:-admin}"
FILEBROWSER_BASE_PATH="${FILEBROWSER_BASE_PATH:-/dbfiles}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
FB_CLI=(run --rm --no-deps --entrypoint /filebrowser filebrowser)

fb_cli() {
  $COMPOSE "${FB_CLI[@]}" "$@"
}

echo "=== Fix FileBrowser base URL ==="
$COMPOSE stop filebrowser
fb_cli config set --baseurl "$FILEBROWSER_BASE_PATH" --database /database/filebrowser.db
$COMPOSE up -d filebrowser

"$(dirname "$0")/apply-nginx-https.sh"

DOMAIN="${DOMAIN:-economicdb.com}"
echo ""
echo "=== Check HTML asset paths (must start with ${FILEBROWSER_BASE_PATH}/) ==="
curl -sf "https://${DOMAIN}${FILEBROWSER_BASE_PATH}/" | grep -oE 'src="[^"]+"' | head -5 || echo "WARNING: could not fetch FileBrowser HTML"

echo ""
echo "Open: https://${DOMAIN}${FILEBROWSER_BASE_PATH}/"
echo "Login: ${FILEBROWSER_USERNAME}"
