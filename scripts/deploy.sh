#!/bin/bash
set -euo pipefail

SERVER="${DEPLOY_SERVER:-deploy@YOUR_SERVER_IP}"
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
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker image prune -f
sleep 5
curl -sf http://127.0.0.1/health || echo "WARNING: Health check failed!"
echo "=== Deploy done ==="
EOF
