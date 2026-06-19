#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

mkdir -p backups nginx/ssl

chmod +x scripts/*.sh

echo "Setup complete. Local dev: make dev | First server deploy: sudo scripts/setup-server.sh && scripts/first-deploy.sh"
