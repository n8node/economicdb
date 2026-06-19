#!/bin/bash
set -euo pipefail

PROJECT_DIR="/opt/economicdb"
# shellcheck disable=SC1091
source "$PROJECT_DIR/.env"
DOMAIN="${DOMAIN:-economicdb.com}"

cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$PROJECT_DIR/nginx/ssl/"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$PROJECT_DIR/nginx/ssl/"

docker compose -f "$PROJECT_DIR/docker-compose.yml" \
    -f "$PROJECT_DIR/docker-compose.prod.yml" \
    exec nginx nginx -s reload

echo "SSL certificates updated and nginx reloaded"
