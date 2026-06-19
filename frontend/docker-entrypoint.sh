#!/bin/sh
set -e

# Накапливаем static-чанки между деплоями — старый HTML не ломается на 404
mkdir -p /app/.next/static
if [ -d /opt/static-staging ]; then
  cp -rn /opt/static-staging/. /app/.next/static/ 2>/dev/null || true
fi

exec "$@"
