#!/bin/bash
# Переприменить HTTPS nginx с no-cache (WP, /app, /adminus, /dbfiles, /api)
set -euo pipefail

cd "$(dirname "$0")/.."

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

"$(dirname "$0")/apply-nginx-https.sh"

echo ""
echo "=== Verify Cache-Control on /app ==="
curl -sI "https://$DOMAIN/app" | grep -iE 'cache-control|pragma|expires' || true

echo ""
echo "=== Done (server) ==="
echo "В браузере один раз: очистить данные сайта economicdb.com или открыть в режиме инкognito."
