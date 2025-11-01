#!/bin/sh
set -e

TARGET="${TARGET:-/target}"
mkdir -p "$TARGET"

cp -a /opt/monitoring/. "$TARGET" || true
chown -R 1000:1000 "$TARGET" || true


if [ "$1" = "--copy-only" ] || [ -z "$1" ]; then
  exit 0
fi

tail -f /dev/null