#!/bin/sh
set -eu
url=${1:-http://127.0.0.1:8080}
for attempt in $(seq 1 60); do
  if curl -fsSL --max-time 5 "$url/admin" > /dev/null 2>&1; then
    printf '%s\n' 'OK: /admin responds through the reverse proxy'
    exit 0
  fi
  sleep 2
done
echo 'FAIL: /admin unavailable' >&2
exit 1
