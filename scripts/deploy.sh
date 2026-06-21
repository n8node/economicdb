#!/bin/bash
set -euo pipefail

SERVER="${DEPLOY_SERVER:-root@194.67.120.118}"
PROJECT_DIR="/opt/economicdb"
BRANCH="${1:-main}"

echo "=== Deploying branch: $BRANCH ==="

git push origin "$BRANCH"

ssh "$SERVER" bash -s << EOF
set -euo pipefail
cd $PROJECT_DIR
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH
if [ -f nginx/templates/https.conf.template ]; then
  bash scripts/generate-nginx-https-conf.sh
fi
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T nginx nginx -t
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T nginx nginx -s reload
docker image prune -f
sleep 5
curl -sf http://127.0.0.1/health || echo "WARNING: Health check failed!"
echo "=== Deploy done ==="
EOF
