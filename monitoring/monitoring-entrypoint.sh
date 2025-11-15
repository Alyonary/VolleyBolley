#!/bin/sh
set -e

TARGET="${TARGET:-/target}"      # корень целевого тома
UID="${COPY_UID:-472}"
GID="${COPY_GID:-472}"

[ -d /opt/monitoring ] || { echo "/opt/monitoring not found" >&2; exit 1; }

mkdir -p "$TARGET"

# копируем содержимое образа В КОРЕНЬ тома (без дополнительной поддиректории)
cp -a /opt/monitoring/. "$TARGET" || true

# если есть готовая grafana/provisioning — переместим/гарантируем структуру
if [ -d /opt/monitoring/grafana/provisioning ]; then
  mkdir -p "$TARGET/provisioning"
  cp -a /opt/monitoring/grafana/provisioning/. "$TARGET/provisioning/" || true
fi

# создаём пустые папки, которые ожидает Grafana
mkdir -p "$TARGET/provisioning/datasources" "$TARGET/provisioning/dashboards"

chmod -R a+rX "$TARGET" || true
chown -R "${UID}:${GID}" "$TARGET" 2>/dev/null || true

echo "Monitoring files copied to $TARGET (owner=${UID}:${GID})"

if [ "$1" = "--copy-only" ] || [ -z "$1" ]; then
  exit 0
fi

tail -f /dev/null