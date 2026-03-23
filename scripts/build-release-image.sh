#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d)-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
TARGET_PLATFORM="${TARGET_PLATFORM:-linux/amd64}"
IMAGE_NAME="${DOUYIN_PARSER_IMAGE:-ballbasecn/douyin-parser}"

echo "==> 构建 douyin-parser 镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
docker buildx build \
  --platform "${TARGET_PLATFORM}" \
  -f "${ROOT_DIR}/Dockerfile" \
  --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
  --load \
  "${ROOT_DIR}"

echo "==> 镜像构建完成"
echo "DOUYIN_PARSER_IMAGE=${IMAGE_NAME}:${IMAGE_TAG}"
