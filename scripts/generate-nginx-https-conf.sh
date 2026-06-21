#!/bin/bash
# Копирует HTTPS шаблоны в nginx/conf.d (без reload контейнера).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f nginx/templates/https.conf.template ]; then
  echo "ERROR: nginx/templates/https.conf.template not found"
  exit 1
fi

DOMAIN="${DOMAIN:-economicdb.com}"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
  DOMAIN="${DOMAIN:-economicdb.com}"
fi

cp nginx/templates/https.conf.template nginx/conf.d/https.conf
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/https.conf

cp nginx/templates/default.http-redirect.conf nginx/conf.d/default.conf
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/default.conf

echo "=== nginx conf.d written for ${DOMAIN} ==="
