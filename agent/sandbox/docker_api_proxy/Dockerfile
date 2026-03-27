FROM python:3.12-alpine

RUN apk add --no-cache curl

WORKDIR /app
COPY proxy.py .

RUN addgroup -g 1000 proxy && \
    adduser -u 1000 -G proxy -s /bin/sh -D proxy

USER proxy

EXPOSE 2376

HEALTHCHECK --interval=10s --timeout=5s --start-period=2s --retries=3 \
    CMD curl --fail http://localhost:2376/_ping || exit 1

CMD ["python", "/app/proxy.py", "2376", "host.docker.internal", "2375"]
