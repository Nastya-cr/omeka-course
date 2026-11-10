#!/bin/sh
set -eu
while true; do
  if wget -q -T 5 -O /dev/null http://proxy/admin; then
    state=OK
  else
    state=FAIL
  fi
  printf '%s proxy/admin %s\n' "$(date -u +%FT%TZ)" "$state"
  sleep 30
done
