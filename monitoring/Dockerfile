FROM alpine:3.18

RUN apk add --no-cache bash ca-certificates

WORKDIR /opt/monitoring
COPY . /opt/monitoring

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["--copy-only"]