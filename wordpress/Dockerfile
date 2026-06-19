FROM wordpress:6.8-php8.3-apache

RUN a2enmod rewrite headers

COPY config/extra.php /usr/local/share/economicdb/extra.php
COPY docker-entrypoint.sh /usr/local/bin/economicdb-entrypoint.sh
RUN chmod +x /usr/local/bin/economicdb-entrypoint.sh

ENTRYPOINT ["economicdb-entrypoint.sh"]
CMD ["apache2-foreground"]
