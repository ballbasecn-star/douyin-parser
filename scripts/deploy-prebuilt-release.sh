#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d)-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
DEPLOY_HOST="${DEPLOY_HOST:?DEPLOY_HOST is required}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_BASE_DIR="${DEPLOY_BASE_DIR:-/root/apps/parsers/douyin-parser}"
DEPLOY_ENV_FILE="${DEPLOY_ENV_FILE:-${ROOT_DIR}/deploy/douyin-parser/.env.prod}"
BUNDLE_DIR="${ROOT_DIR}/.tmp/release/${IMAGE_TAG}"
IMAGE_NAME="${DOUYIN_PARSER_IMAGE:-ballbasecn/douyin-parser}"

if [[ ! -f "${DEPLOY_ENV_FILE}" ]]; then
  echo "缺少部署环境文件: ${DEPLOY_ENV_FILE}" >&2
  exit 1
fi

if [[ ! -f "${BUNDLE_DIR}/images/douyin-parser.tar" ]]; then
  echo "未找到导出的镜像包，请先执行 scripts/export-release-bundle.sh" >&2
  exit 1
fi

SSH_CMD=(ssh -p "${DEPLOY_PORT}" -o StrictHostKeyChecking=no "${DEPLOY_USER}@${DEPLOY_HOST}")
SCP_CMD=(scp -P "${DEPLOY_PORT}" -O -o StrictHostKeyChecking=no)

if [[ -n "${DEPLOY_PASSWORD:-}" ]]; then
  export SSHPASS="${DEPLOY_PASSWORD}"
  SSH_CMD=(sshpass -e "${SSH_CMD[@]}")
  SCP_CMD=(sshpass -e "${SCP_CMD[@]}")
fi

echo "==> 准备服务器目录"
"${SSH_CMD[@]}" "mkdir -p '${DEPLOY_BASE_DIR}/deploy' '${DEPLOY_BASE_DIR}/images'"

echo "==> 上传部署文件"
"${SCP_CMD[@]}" "${ROOT_DIR}/deploy/douyin-parser/compose.prod.yaml" "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_BASE_DIR}/deploy/compose.prod.yaml"
"${SCP_CMD[@]}" "${DEPLOY_ENV_FILE}" "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_BASE_DIR}/deploy/.env"
"${SCP_CMD[@]}" "${BUNDLE_DIR}/images/douyin-parser.tar" "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_BASE_DIR}/images/douyin-parser.tar"

echo "==> 在服务器加载镜像并启动服务"
"${SSH_CMD[@]}" "docker load -i '${DEPLOY_BASE_DIR}/images/douyin-parser.tar' && \
cd '${DEPLOY_BASE_DIR}/deploy' && \
DOUYIN_PARSER_IMAGE='${IMAGE_NAME}' \
APP_RELEASE_VERSION='${IMAGE_TAG}' \
docker compose --env-file .env -f compose.prod.yaml up -d"

echo "==> 部署完成"
