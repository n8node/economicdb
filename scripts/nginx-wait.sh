#!/bin/bash
# Wait until nginx container accepts exec, then run nginx -t [reload].
set -euo pipefail

RELOAD="${NGINX_RELOAD:-1}"
COMPOSE="${COMPOSE:-docker compose -f docker-compose.yml -f docker-compose.prod.yml}"

for i in $(seq 1 45); do
  state=$($COMPOSE ps nginx --format '{{.State}}' 2>/dev/null | head -1 || true)
  if [ "$state" = "running" ]; then
    if $COMPOSE exec -T nginx nginx -t 2>/dev/null; then
      if [ "$RELOAD" = "1" ]; then
        $COMPOSE exec -T nginx nginx -s reload
        echo "nginx reloaded"
      else
        echo "nginx config OK"
      fi
      exit 0
    fi
  fi
  sleep 2
done

echo "ERROR: nginx not ready for exec (409/restarting?)"
$COMPOSE ps nginx 2>/dev/null || true
$COMPOSE logs nginx --tail=30 2>/dev/null || true
exit 1
