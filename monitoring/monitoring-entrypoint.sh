#!/bin/sh
set -e

TARGET="${TARGET:-/target}"      # Корень целевого тома
UID="${COPY_UID:-472}"
GID="${COPY_GID:-472}"

# Проверяем наличие исходной директории
[ -d /opt/monitoring ] || { echo "/opt/monitoring not found" >&2; exit 1; }

# Создаём целевую директорию, если она не существует
mkdir -p "$TARGET"

# Копируем содержимое образа в корень тома (без дополнительной поддиректории)
cp -a /opt/monitoring/. "$TARGET" || true

# Если есть готовая структура grafana/provisioning, перемещаем её
if [ -d /opt/monitoring/grafana/provisioning ]; then
  mkdir -p "$TARGET/provisioning"
  cp -a /opt/monitoring/grafana/provisioning/. "$TARGET/provisioning/" || true
fi

# Создаём пустые папки, которые ожидает Grafana
mkdir -p "$TARGET/provisioning/datasources" "$TARGET/provisioning/dashboards"

# Копируем конфигурацию Promtail, если она существует
if [ -f /opt/monitoring/promtail-config.yml ]; then
  cp /opt/monitoring/promtail-config.yml "$TARGET/promtail-config.yml" || true
fi

# Копируем конфигурацию Loki, если она существует
if [ -f /opt/monitoring/loki-config.yml ]; then
  cp /opt/monitoring/loki-config.yml "$TARGET/loki-config.yml" || true
fi

# Копируем конфигурацию Prometheus, если она существует
if [ -f /opt/monitoring/prometheus.yml ]; then
  cp /opt/monitoring/prometheus.yml "$TARGET/prometheus.yml" || true
fi

# Устанавливаем права доступа для всех файлов
chmod -R a+rX "$TARGET" || true
chown -R "${UID}:${GID}" "$TARGET" 2>/dev/null || true

echo "Monitoring files copied to $TARGET (owner=${UID}:${GID})"

# Если передан аргумент "--copy-only" или аргумент отсутствует, завершаем выполнение
if [ "$1" = "--copy-only" ] || [ -z "$1" ]; then
  exit 0
fi

# Оставляем контейнер активным
tail -f /dev/null