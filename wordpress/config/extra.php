<?php
/**
 * Proxy + dynamic scheme for WordPress behind Nginx.
 * Loaded from wp-config.php on every request.
 */
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
    $_SERVER['HTTPS'] = 'on';
}

$domain = getenv('DOMAIN') ?: 'economicdb.com';
$host = $_SERVER['HTTP_HOST'] ?? $domain;
$host = preg_replace('/:\d+$/', '', $host);
$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';

if (!defined('WP_HOME')) {
    define('WP_HOME', $scheme . '://' . $host);
}
if (!defined('WP_SITEURL')) {
    define('WP_SITEURL', $scheme . '://' . $host);
}
