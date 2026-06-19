#!/usr/bin/env bash
set -euo pipefail

WP_CONFIG="/var/www/html/wp-config.php"
EXTRA="/usr/local/share/economicdb/extra.php"
MARKER="economicdb-extra-config"

if [ -f "$WP_CONFIG" ]; then
    sed -i "/define('WP_HOME'/d" "$WP_CONFIG" 2>/dev/null || true
    sed -i '/define("WP_HOME"/d' "$WP_CONFIG" 2>/dev/null || true
    sed -i "/define('WP_SITEURL'/d" "$WP_CONFIG" 2>/dev/null || true
    sed -i '/define("WP_SITEURL"/d' "$WP_CONFIG" 2>/dev/null || true

    if ! grep -q "$MARKER" "$WP_CONFIG"; then
        sed -i "/That's all, stop editing/i\\
/* $MARKER */\\
if (file_exists('$EXTRA')) { require_once '$EXTRA'; }\\
" "$WP_CONFIG"
    fi
fi

exec docker-entrypoint.sh "$@"
