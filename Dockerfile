FROM --platform=$TARGETPLATFORM python:3.11-slim-bookworm

ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_TRUSTED_HOST

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    WEBHOOK_PORT=5555

WORKDIR /app

# ffmpeg 用于音频提取，libgomp1 为 faster-whisper / ctranslate2 CPU 运行时常见依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && if [ -n "$PIP_INDEX_URL" ]; then pip config set global.index-url "$PIP_INDEX_URL"; fi \
    && if [ -n "$PIP_EXTRA_INDEX_URL" ]; then pip config set global.extra-index-url "$PIP_EXTRA_INDEX_URL"; fi \
    && if [ -n "$PIP_TRUSTED_HOST" ]; then pip config set global.trusted-host "$PIP_TRUSTED_HOST"; fi \
    && pip install -r requirements.txt

COPY main.py .
COPY app ./app
COPY web ./web
COPY scripts ./scripts
COPY cookie_data ./cookie_data

EXPOSE 8080 5555

CMD ["sh", "-c", "python -m web.app --port ${PORT} --webhook-port ${WEBHOOK_PORT}"]
