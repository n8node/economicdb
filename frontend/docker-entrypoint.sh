#!/bin/sh
set -eu

STATIC_ROOT=/data/next-static

mkdir -p "$STATIC_ROOT"

if [ ! -d /opt/static-staging ]; then
  echo "ERROR: /opt/static-staging is missing" >&2
  exit 1
fi

staging_count=$(find /opt/static-staging -type f 2>/dev/null | wc -l | tr -d " ")
if [ "$staging_count" -eq 0 ]; then
  echo "ERROR: /opt/static-staging is empty" >&2
  exit 1
fi

cp -a /opt/static-staging/. "$STATIC_ROOT/"

mkdir -p /app/.next
if [ -e /app/.next/static ] && [ ! -L /app/.next/static ]; then
  rm -rf /app/.next/static
fi
ln -sfn "$STATIC_ROOT" /app/.next/static

volume_count=$(find "$STATIC_ROOT" -type f 2>/dev/null | wc -l | tr -d " ")
if [ "$volume_count" -eq 0 ]; then
  echo "ERROR: ${STATIC_ROOT} is empty after copy" >&2
  exit 1
fi

echo "static ready: staging=${staging_count} volume=${volume_count}"
exec "$@"
