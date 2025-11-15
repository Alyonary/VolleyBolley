#!/bin/sh
set -e

TARGET="${TARGET:-/target}"      # Root directory for the target volume
UID="${COPY_UID:-472}"          # Default UID for ownership
GID="${COPY_GID:-472}"          # Default GID for ownership

# Check if the source directory exists
[ -d /opt/monitoring ] || { echo "/opt/monitoring not found" >&2; exit 1; }

# Create the target directory if it does not exist
mkdir -p "$TARGET"

# Copy the contents of the image to the root of the target volume (without subdirectories)
cp -a /opt/monitoring/. "$TARGET" || true

# If the Grafana provisioning structure exists, move it to the target
if [ -d /opt/monitoring/grafana/provisioning ]; then
  mkdir -p "$TARGET/provisioning"
  cp -a /opt/monitoring/grafana/provisioning/. "$TARGET/provisioning/" || true
fi

# Create empty directories expected by Grafana
mkdir -p "$TARGET/provisioning/datasources" "$TARGET/provisioning/dashboards"

# Copy Promtail configuration if it exists
if [ -f /opt/monitoring/promtail-config.yml ]; then
  cp /opt/monitoring/promtail-config.yml "$TARGET/promtail-config.yml" || true
fi

# Copy Loki configuration if it exists
if [ -f /opt/monitoring/loki-config.yml ]; then
  cp /opt/monitoring/loki-config.yml "$TARGET/loki-config.yml" || true
fi

# Copy Prometheus configuration if it exists
if [ -f /opt/monitoring/prometheus.yml ]; then
  cp /opt/monitoring/prometheus.yml "$TARGET/prometheus.yml" || true
fi

# Set permissions for all files
chmod -R a+rX "$TARGET" || true
chown -R "${UID}:${GID}" "$TARGET" 2>/dev/null || true

echo "Monitoring files copied to $TARGET (owner=${UID}:${GID})"

# Exit if the "--copy-only" argument is passed or no arguments are provided
if [ "$1" = "--copy-only" ] || [ -z "$1" ]; then
  exit 0
fi

# Keep the container running
tail -f /dev/null