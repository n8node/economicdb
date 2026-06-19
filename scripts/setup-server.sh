#!/bin/bash
# Установка Docker, Docker Compose plugin и Certbot на чистый Ubuntu/Debian-сервер.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Запустите от root: sudo ./scripts/setup-server.sh"
    exit 1
fi

echo "=== Installing Docker ==="
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed: $(docker --version)"
fi

echo "=== Installing Docker Compose plugin ==="
if ! docker compose version >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y docker-compose-plugin
fi

echo "=== Installing Certbot ==="
if ! command -v certbot >/dev/null 2>&1; then
    apt-get update -qq
    apt-get install -y certbot
fi

echo "=== Creating project directory ==="
    mkdir -p /opt/economicdb/backups /opt/economicdb/nginx/ssl

echo "=== Server setup complete ==="
docker --version
docker compose version
certbot --version
