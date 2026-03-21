ARG TARGETPLATFORM
ARG BASE_IMAGE=ballbasecn/douyin-parser-base:python3.11-bookworm
FROM --platform=$TARGETPLATFORM ${BASE_IMAGE}

ARG TARGETOS
ARG TARGETARCH
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST
ARG REQUIREMENTS_FILE=requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    WEBHOOK_PORT=5555

WORKDIR /app

COPY requirements.txt requirements.local-whisper.txt ./

RUN python -m pip install --upgrade pip \
    && if [ -n "$PIP_INDEX_URL" ]; then pip config set global.index-url "$PIP_INDEX_URL"; fi \
    && if [ -n "$PIP_EXTRA_INDEX_URL" ]; then pip config set global.extra-index-url "$PIP_EXTRA_INDEX_URL"; fi \
    && if [ -n "$PIP_TRUSTED_HOST" ]; then pip config set global.trusted-host "$PIP_TRUSTED_HOST"; fi \
    && pip install -r "$REQUIREMENTS_FILE"

COPY main.py .
COPY app ./app
COPY web ./web
COPY scripts ./scripts

EXPOSE 8080 5555

CMD ["sh", "-c", "python -m web.app --port ${PORT} --webhook-port ${WEBHOOK_PORT}"]
