FROM php:8.2-apache AS base

RUN apt-get update \
    && apt-get install -y --no-install-recommends kcat \
    && a2enmod rewrite \
    && printf "FallbackResource /index.php\n" > /etc/apache2/conf-available/fallback.conf \
    && a2enconf fallback \
    && sed -i 's/80/8080/g' /etc/apache2/ports.conf /etc/apache2/sites-available/000-default.conf \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

WORKDIR /src
COPY docker/laravel/public/ ./

FROM base AS production

COPY --from=builder /src/ /var/www/html/

RUN chown -R www-data:www-data /var/www/html /var/run/apache2 /var/lock/apache2 /var/log/apache2

USER www-data

EXPOSE 8080
