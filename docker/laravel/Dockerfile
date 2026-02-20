FROM php:8.2-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends kcat \
    && a2enmod rewrite \
    && printf "FallbackResource /index.php\n" > /etc/apache2/conf-available/fallback.conf \
    && a2enconf fallback \
    && rm -rf /var/lib/apt/lists/*

COPY docker/laravel/public/ /var/www/html/
