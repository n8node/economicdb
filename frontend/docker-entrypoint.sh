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

echo "static ready: files=${static_count}"
exec "$@"
