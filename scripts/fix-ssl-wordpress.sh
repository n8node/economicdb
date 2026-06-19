#!/bin/bash
# Диагностика и исправление HTTPS для WordPress + nginx
set -euo pipefail

cd /opt/economicdb
set -a
# shellcheck disable=SC1091
source .env
set +a

DOMAIN="${DOMAIN:-economicdb.com}"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "=== 1. nginx conf.d ==="
ls -la nginx/conf.d/
rm -f nginx/conf.d/https.conf.sample nginx/conf.d/default.http-bootstrap.conf nginx/conf.d/default.http-redirect.conf

echo "=== 2. Apply HTTPS nginx configs ==="
cp nginx/templates/default.http-redirect.conf nginx/conf.d/default.conf
cp nginx/templates/https.conf.template nginx/conf.d/https.conf
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx/conf.d/https.conf

echo "=== 3. Test nginx ==="
$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo "=== 4. Local HTTPS checks ==="
curl -sf "https://$DOMAIN/health" && echo " health OK"
curl -sI "http://$DOMAIN/" | head -1
curl -sI "https://$DOMAIN/wp-includes/css/install.min.css" | head -3

echo "=== 5. Rebuild WordPress (proxy URL fix) ==="
$COMPOSE up -d --build wordpress

echo "=== 6. Patch wp-config (remove hardcoded http/https defines) ==="
$COMPOSE exec wordpress bash -c '
WP_CONFIG=/var/www/html/wp-config.php
if [ -f "$WP_CONFIG" ]; then
  sed -i "/define('\''WP_HOME'\''/d" "$WP_CONFIG" 2>/dev/null || true
  sed -i "/define('\''WP_SITEURL'\''/d" "$WP_CONFIG" 2>/dev/null || true
  grep -q "economicdb-extra-config" "$WP_CONFIG" || sed -i "/That'\''s all, stop editing/i\\
/* economicdb-extra-config */\\
if (file_exists('\''/usr/local/share/economicdb/extra.php'\'')) { require_once '\''/usr/local/share/economicdb/extra.php'\''; }\\
" "$WP_CONFIG"
  echo "--- wp-config tail ---"
  tail -8 "$WP_CONFIG"
fi
'

echo "=== 7. Fix WP options in DB (if installed) ==="
$COMPOSE exec -T mysql mysql -u"${WP_DB_USER}" -p"${WP_DB_PASSWORD}" "${WP_DB_NAME}" -e "
UPDATE wp_options SET option_value='https://${DOMAIN}' WHERE option_name IN ('home','siteurl');
SELECT option_name, option_value FROM wp_options WHERE option_name IN ('home','siteurl');
" 2>/dev/null || echo "(WP not installed yet — skip DB update)"

echo "=== 8. CSS URLs in install page ==="
curl -s "https://$DOMAIN/wp-admin/install.php" | grep -oE 'href="[^"]+\.css[^"]*"' | head -5 || true

echo ""
echo "=== Done ==="
echo "Open: https://$DOMAIN/wp-admin/install.php (Ctrl+F5)"
echo "If still fails from browser — check firewall: ufw status | ss -tlnp | grep 443"
