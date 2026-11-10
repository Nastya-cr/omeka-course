#!/bin/sh
set -eu
cd /var/www/html
password=$(cat /run/secrets/omeka_db_password)
case "$password" in
  ''|*[!0-9a-f]*) echo 'Expected a hexadecimal database password' >&2; exit 1 ;;
esac
umask 027
cat > config/database.ini <<CONFIG
user = "omeka"
password = "$password"
dbname = "omeka"
host = "db"
port = "3306"
CONFIG
chown root:www-data config/database.ini
chmod 640 config/database.ini
chown www-data:www-data files
umask 022
exec apache2-foreground
