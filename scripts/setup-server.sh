#!/bin/bash
# Установка Docker, Docker Compose plugin и Certbot на чистый Ubuntu/Debian-сервер.
set -euo pipefail

wait_for_apt() {
    local max_wait=600
    local waited=0
    while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 \
       || fuser /var/lib/dpkg/lock >/dev/null 2>&1 \
       || fuser /var/lib/apt/lists/lock >/dev/null 2>&1; do
        if [ "$waited" -ge "$max_wait" ]; then
            echo "ERROR: apt lock not released after ${max_wait}s (unattended-upgr?)"
            echo "Try: systemctl stop unattended-upgrades; wait; apt-get install -y certbot"
            exit 1
        fi
        echo "Waiting for apt lock (${waited}s, often unattended-upgrades)..."
        sleep 10
        waited=$((waited + 10))
    done
}

apt_install() {
    wait_for_apt
    apt-get update -qq
    wait_for_apt
    DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}

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
    apt_install docker-compose-plugin
else
    echo "Docker Compose already installed: $(docker compose version)"
fi

echo "=== Installing Certbot ==="
if ! command -v certbot >/dev/null 2>&1; then
    apt_install certbot
else
    echo "Certbot already installed: $(certbot --version)"
fi

echo "=== Creating project directory ==="
mkdir -p /opt/economicdb/backups /opt/economicdb/nginx/ssl

echo "=== Server setup complete ==="
docker --version
docker compose version
certbot --version
