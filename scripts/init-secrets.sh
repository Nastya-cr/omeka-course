#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p .secrets
for name in omeka_db_password omeka_root_password; do
  path=".secrets/$name"
  if [ ! -s "$path" ]; then
    openssl rand -hex 24 > "$path.tmp"
    mv "$path.tmp" "$path"
  fi
done
printf '%s\n' 'Секреты готовы в .secrets/'
