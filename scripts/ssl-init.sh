#!/bin/bash
# Первичный выпуск Let's Encrypt для economicdb.com
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Run first-deploy.sh or copy .env.example first."
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

DOMAIN="${DOMAIN:-economicdb.com}"
EMAIL="${CERTBOT_EMAIL:-admin@economicdb.com}"

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Stopping nginx for ACME standalone ==="
$COMPOSE stop nginx || true

echo "=== Requesting certificate for $DOMAIN and www.$DOMAIN ==="
certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

echo "=== Copying certificates ==="
mkdir -p nginx/ssl
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" nginx/ssl/
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" nginx/ssl/
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

echo "=== Enabling HTTPS in nginx ==="
# Удалить лишние *.conf из conf.d (иначе conflicting server name на :80)
rm -f nginx/conf.d/default.http-bootstrap.conf
rm -f nginx/conf.d/default.http-redirect.conf

cp nginx/templates/https.conf.template nginx/conf.d/https.conf
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/https.conf

cp nginx/templates/default.http-redirect.conf nginx/conf.d/default.conf

echo "=== Starting nginx ==="
$COMPOSE up -d nginx

echo "=== Testing nginx config ==="
$COMPOSE exec nginx nginx -t

echo "=== SSL init complete ==="
echo "  https://$DOMAIN/"
echo "  https://$DOMAIN/wp-admin/install.php"
