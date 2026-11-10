#!/bin/sh
set -eu
while sleep "${BACKUP_INTERVAL:-86400}"; do
  if ! /usr/local/bin/backup.sh; then
    echo 'Backup failed. See the preceding error.' >&2
  fi
done
