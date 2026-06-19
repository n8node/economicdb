#!/bin/sh
set -eu

mkdir -p /app/.next/static

if [ ! -d /opt/static-staging ]; then
  echo "ERROR: /opt/static-staging is missing" >&2
  exit 1
fi

staging_count=$(find /opt/static-staging -type f 2>/dev/null | wc -l | tr -d " ")
if [ "$staging_count" -eq 0 ]; then
  echo "ERROR: /opt/static-staging is empty" >&2
  exit 1
fi

cp -a /opt/static-staging/. /app/.next/static/

volume_count=$(find /app/.next/static -type f 2>/dev/null | wc -l | tr -d " ")
if [ "$volume_count" -eq 0 ]; then
  echo "ERROR: static volume is empty after copy" >&2
  exit 1
fi

echo "static ready: staging=${staging_count} volume=${volume_count}"
exec "$@"
