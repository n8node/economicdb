#!/bin/bash
# Полный post-deploy после git pull
set -euo pipefail

cd "$(dirname "$0")/.."

chmod +x scripts/*.sh
bash scripts/server-deploy.sh

bash scripts/diagnose-site.sh
