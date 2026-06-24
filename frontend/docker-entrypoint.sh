#!/bin/sh
set -eu

STATIC_ROOT=/app/.next/static

if [ ! -d "$STATIC_ROOT" ]; then
  echo "ERROR: ${STATIC_ROOT} is missing" >&2
  exit 1
fi

static_count=$(find "$STATIC_ROOT" -type f 2>/dev/null | wc -l | tr -d " ")
if [ "$static_count" -eq 0 ]; then
  echo "ERROR: ${STATIC_ROOT} is empty" >&2
  exit 1
fi

if [ ! -d /app/public ]; then
  echo "ERROR: /app/public is missing" >&2
  exit 1
fi

if [ -f /app/BUILD_ID ]; then
  image_build_id=$(cat /app/BUILD_ID | tr -d "\r\n")
  if [ -n "$image_build_id" ]; then
    if [ "${BUILD_ID:-}" = "" ] || [ "${BUILD_ID:-}" = "dev" ]; then
      export BUILD_ID="$image_build_id"
    fi
    if [ "${NEXT_PUBLIC_BUILD_ID:-}" = "" ] || [ "${NEXT_PUBLIC_BUILD_ID:-}" = "dev" ]; then
      export NEXT_PUBLIC_BUILD_ID="$image_build_id"
    fi
  fi
fi

echo "static ready: files=${static_count}"
echo "frontend build id: ${NEXT_PUBLIC_BUILD_ID:-unknown}"
exec "$@"
