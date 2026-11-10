FROM php:8.4-apache-bookworm
ARG OMEKA_VERSION=4.2.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip libicu-dev libonig-dev libzip-dev libpng-dev libjpeg62-turbo-dev libfreetype6-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" gd intl mbstring pdo_mysql zip \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*
RUN curl --fail --show-error --silent --location --retry 3 \
      "https://github.com/omeka/omeka-s/releases/download/v${OMEKA_VERSION}/omeka-s-${OMEKA_VERSION}.zip" -o /tmp/omeka.zip \
    && unzip -q /tmp/omeka.zip -d /tmp/omeka-release \
    && app="$(find /tmp/omeka-release -maxdepth 2 -name index.php -type f -print -quit)" \
    && test -n "$app" \
    && cp -a "$(dirname "$app")"/. /var/www/html/ \
    && test -f /var/www/html/.htaccess \
    && test -d /var/www/html/vendor \
    && mkdir -p /var/www/html/files \
    && chown -R www-data:www-data /var/www/html/files \
    && rm -rf /tmp/omeka.zip /tmp/omeka-release
COPY apache.conf /etc/apache2/conf-enabled/omeka.conf
COPY uploads.ini /usr/local/etc/php/conf.d/omeka-uploads.ini
COPY --chmod=755 start.sh /usr/local/bin/start-omeka
CMD ["start-omeka"]

RUN sed -i '/Thumbnailer.*=>/s/Thumbnailer\\ImageMagick/Thumbnailer\\Gd/' /var/www/html/config/local.config.php \
    && grep -Fq "'Omeka\File\Thumbnailer' => 'Omeka\File\Thumbnailer\Gd'" /var/www/html/config/local.config.php
