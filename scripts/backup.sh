#!/bin/sh
set -eu
umask 077
backup_dir=${BACKUP_DIR:-/backups}
files_dir=${FILES_DIR:-/omeka-files}
secret_file=${DB_SECRET_FILE:-/run/secrets/omeka_db_password}
password=$(cat "$secret_file")
case "$password" in
  ''|*[!0-9a-f]*) echo 'Expected a hexadecimal database password' >&2; exit 1 ;;
esac
tmp=$(mktemp -d "$backup_dir/.partial.XXXXXX")
config=$(mktemp)
trap 'rm -rf "$tmp"; rm -f "$config"' EXIT
trap 'exit 1' HUP INT TERM
printf '[client]\nhost=db\nuser=omeka\npassword=%s\n' "$password" > "$config"
mariadb-dump --defaults-extra-file="$config" --single-transaction --quick omeka > "$tmp/database.sql"
test -s "$tmp/database.sql"
tar -C "$files_dir" -czf "$tmp/files.tar.gz" .
(
  cd "$tmp"
  sha256sum database.sql files.tar.gz > SHA256SUMS
)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
suffix=${tmp##*.}
mv "$tmp" "$backup_dir/$stamp-$suffix"
printf 'Backup created: %s\n' "$stamp-$suffix"
