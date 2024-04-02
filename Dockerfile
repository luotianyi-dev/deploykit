FROM    python:3.11-slim AS builder
ARG     IMAGE_VERSION=latest
LABEL   org.opencontainers.image.title=deploykit \
        org.opencontainers.image.url=https://github.com/luotianyi-dev/deploykit \
        org.opencontainers.image.source=https://github.com/luotianyi-dev/deploykit \
        org.opencontainers.image.documentation=https://github.com/luotianyi-dev/deploykit/blob/main/README.md \
        org.opencontainers.image.licenses=MPL-2.0 \
        org.opencontainers.image.version=${IMAGE_VERSION}
COPY    . /app
WORKDIR   /app
RUN     pip install -U pdm && pdm install --check --prod --no-editable

FROM        python:3.11-slim
COPY        --from=builder /app/.venv /app/.venv
COPY        src            /app/src
RUN         apt-get update && apt-get install -y curl
ENV         PATH="/app/.venv/bin:$PATH" \
            WEB_CONCURRENCY=4
EXPOSE      8000
MAINTAINER  Tianyi Network <support@luotianyi.dev>
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=3 CMD \
            curl -sfvo /dev/null http://localhost:8000/health
ENTRYPOINT  ["uvicorn", "deploykit_server.app:app", "--host", "0.0.0.0"]
