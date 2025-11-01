FROM alpine:3.18

RUN apk add --no-cache bash ca-certificates

WORKDIR /opt/monitoring
COPY . /opt/monitoring

# нормализуем окончания строк и сделаем entrypoint исполняемым
RUN if [ -f /opt/monitoring/monitoring-entrypoint.sh ]; then \
      sed -i 's/\r$//' /opt/monitoring/monitoring-entrypoint.sh && \
      chmod +x /opt/monitoring/monitoring-entrypoint.sh ; \
    else echo "monitoring-entrypoint.sh not found" >&2; exit 1; fi

ENTRYPOINT ["/opt/monitoring/monitoring-entrypoint.sh"]
CMD ["--copy-only"]