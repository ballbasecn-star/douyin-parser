#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d)-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
IMAGE_NAME="${DOUYIN_PARSER_IMAGE:-ballbasecn/douyin-parser}"
BUNDLE_DIR="${ROOT_DIR}/.tmp/release/${IMAGE_TAG}"

mkdir -p "${BUNDLE_DIR}/images" "${BUNDLE_DIR}/deploy"

echo "==> 导出 douyin-parser 镜像"
docker save -o "${BUNDLE_DIR}/images/douyin-parser.tar" "${IMAGE_NAME}:${IMAGE_TAG}"

cp "${ROOT_DIR}/deploy/douyin-parser/compose.prod.yaml" "${BUNDLE_DIR}/deploy/compose.prod.yaml"
cp "${ROOT_DIR}/deploy/douyin-parser/.env.prod.example" "${BUNDLE_DIR}/deploy/.env.prod.example"

cat > "${BUNDLE_DIR}/deploy/release.env" <<EOF
DOUYIN_PARSER_IMAGE=${IMAGE_NAME}
APP_RELEASE_VERSION=${IMAGE_TAG}
EOF

echo "==> 导出完成: ${BUNDLE_DIR}"
