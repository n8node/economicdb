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

$COMPOSE exec nginx nginx -t
$COMPOSE exec nginx nginx -s reload

echo "=== 3. HTTPS checks ==="
curl -sf "https://$DOMAIN/health" && echo " health OK"
curl -sI "http://$DOMAIN/" | head -1
curl -sI "https://$DOMAIN/wp-admin/load-styles.php?load%5B%5D=install" | head -5

echo "=== 4. Rebuild & restart WordPress ==="
$COMPOSE up -d --build wordpress
sleep 3

echo "=== 5. wp-config (must contain extra.php) ==="
$COMPOSE exec wordpress grep -n "extra.php\|WP_HOME\|WP_SITEURL\|economicdb-extra" /var/www/html/wp-config.php || echo "WARNING: extra.php not in wp-config!"

echo "=== 6. Manual patch if missing ==="
$COMPOSE exec wordpress bash -c '
WP_CONFIG=/var/www/html/wp-config.php
EXTRA=/usr/local/share/economicdb/extra.php
if [ -f "$WP_CONFIG" ] && ! grep -q "economicdb-extra-config" "$WP_CONFIG"; then
  sed -i "/require_once ABSPATH . '\''wp-settings.php'\'';/i\\
/* economicdb-extra-config */\\
if (file_exists('\''/usr/local/share/economicdb/extra.php'\'')) { require_once '\''/usr/local/share/economicdb/extra.php'\''; }\\
" "$WP_CONFIG"
  echo "Patched wp-config"
fi
grep -n "extra.php" "$WP_CONFIG" || true
'

echo "=== 7. WP DB options (if installed) ==="
$COMPOSE exec -T mysql mysql -u"${WP_DB_USER}" -p"${WP_DB_PASSWORD}" "${WP_DB_NAME}" -e "
UPDATE wp_options SET option_value='https://${DOMAIN}' WHERE option_name IN ('home','siteurl');
SELECT option_name, option_value FROM wp_options WHERE option_name IN ('home','siteurl');
" 2>/dev/null || echo "(WP not installed yet)"

echo "=== 8. Install page style URLs ==="
curl -s "https://$DOMAIN/wp-admin/install.php" | grep -oE "href='[^']+'" | head -8 || true

echo ""
echo "=== Done ==="
echo "Open: https://$DOMAIN/wp-admin/install.php (Ctrl+Shift+R)"
