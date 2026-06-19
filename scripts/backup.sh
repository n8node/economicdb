#!/bin/bash
set -euo pipefail

PROJECT_DIR="/opt/economicdb"
BACKUP_DIR="$PROJECT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# shellcheck disable=SC1091
source "$PROJECT_DIR/.env"

mkdir -p "$BACKUP_DIR"

COMPOSE="docker compose -f $PROJECT_DIR/docker-compose.yml -f $PROJECT_DIR/docker-compose.prod.yml"

$COMPOSE exec -T postgres pg_dump -U "${POSTGRES_USER:-macro}" "${POSTGRES_DB:-macro}" \
    | gzip > "$BACKUP_DIR/pg_$DATE.sql.gz"

$COMPOSE exec -T mysql mysqldump -u "${WP_DB_USER:-wordpress}" -p"${WP_DB_PASSWORD}" "${WP_DB_NAME:-wordpress}" \
    | gzip > "$BACKUP_DIR/wp_$DATE.sql.gz"

find "$BACKUP_DIR" -type f -mtime +"$RETENTION_DAYS" -delete

echo "Backup completed: $DATE"
