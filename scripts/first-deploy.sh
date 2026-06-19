#!/bin/bash
# Первый деплой на чистый сервер:
#   1. Docker + Certbot (setup-server.sh)
#   2. .env с bootstrap-секретами
#   3. docker compose up
#   4. Let's Encrypt
#   5. Seed super_admin (через backend при старте)
#
# Использование на сервере:
#   curl -fsSL .../first-deploy.sh | bash
#   или после git clone:
#   ADMIN_INITIAL_PASSWORD='your-password' ./scripts/first-deploy.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

REPO_URL="${REPO_URL:-https://github.com/n8node/economicdb.git}"
DOMAIN="${DOMAIN:-economicdb.com}"

echo "=== Step 1: Docker & Certbot ==="
if [ "$(id -u)" -eq 0 ]; then
    bash "$SCRIPT_DIR/setup-server.sh"
else
    echo "Запустите setup-server.sh от root, затем повторите first-deploy от deploy-пользователя:"
    echo "  sudo bash scripts/setup-server.sh"
    if ! command -v docker >/dev/null 2>&1; then
        exit 1
    fi
fi

echo "=== Step 2: .env ==="
if [ ! -f .env ]; then
    cp .env.example .env

    POSTGRES_PASS="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    WP_PASS="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    WP_ROOT="$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    JWT="$(openssl rand -base64 48)"
    ENC="$(openssl rand -base64 32)"

    sed -i "s|CHANGE_ME_strong_password|$POSTGRES_PASS|g" .env
    sed -i "s|CHANGE_ME_wp_password|$WP_PASS|g" .env
    sed -i "s|CHANGE_ME_root_password|$WP_ROOT|g" .env
    sed -i "s|CHANGE_ME_min_64_chars_random_secret|$JWT|g" .env
    sed -i "s|CHANGE_ME_min_32_bytes_for_aes256|$ENC|g" .env
    sed -i "s|postgres://macro:CHANGE_ME@|postgres://macro:${POSTGRES_PASS}@|g" .env

    if [ -n "${ADMIN_INITIAL_PASSWORD:-}" ]; then
        sed -i "s|CHANGE_ME_admin_password_on_server|$ADMIN_INITIAL_PASSWORD|g" .env
    fi

    echo "Created .env with generated secrets."
    if grep -q "CHANGE_ME_admin_password" .env; then
        echo ""
        echo "WARNING: Set ADMIN_INITIAL_PASSWORD before backend starts:"
        echo "  export ADMIN_INITIAL_PASSWORD='your-password'"
        echo "  sed -i \"s|CHANGE_ME_admin_password_on_server|\$ADMIN_INITIAL_PASSWORD|g\" .env"
        echo ""
        read -r -p "Press Enter after setting admin password in .env, or Ctrl+C to abort..."
    fi
else
    echo ".env already exists — skipping generation."
fi

# shellcheck disable=SC1091
source .env

echo "=== Step 3: Docker Compose up ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "=== Waiting for backend health ==="
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1/health >/dev/null 2>&1; then
        echo "Backend is healthy."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "WARNING: Health check not ready yet. Check logs:"
        echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend --tail=50"
    fi
    sleep 5
done

echo "=== Step 4: SSL certificate ==="
bash "$SCRIPT_DIR/ssl-init.sh"

echo "=== Step 5: Verify ==="
curl -sf "http://127.0.0.1/health" && echo " HTTP OK"
curl -sfk "https://127.0.0.1/health" -H "Host: $DOMAIN" && echo " HTTPS OK" || true

echo ""
echo "=== First deploy complete ==="
echo "  Site:    https://$DOMAIN/"
echo "  App:     https://$DOMAIN/app/"
echo "  Admin:   https://$DOMAIN/adminus/"
echo "  Admin login: ${ADMIN_INITIAL_EMAIL:-see .env}"
echo ""
echo "Configure OpenRouter, Robokassa, SMTP and data providers in admin panel."
