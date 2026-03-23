#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_CONFIG="${RELEASE_CONFIG:-${ROOT_DIR}/deploy/douyin-parser/.release.local.env}"

if [[ -f "${RELEASE_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${RELEASE_CONFIG}"
fi

if [[ -z "${DEPLOY_ENV_FILE:-}" ]]; then
  DEPLOY_ENV_FILE="${ROOT_DIR}/deploy/douyin-parser/.env.prod"
fi

if [[ -f "${DEPLOY_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${DEPLOY_ENV_FILE}"
fi

IMAGE_TAG="${IMAGE_TAG:-$(date +%Y%m%d)-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
TARGET_PLATFORM="${TARGET_PLATFORM:-linux/amd64}"
DOUYIN_PARSER_IMAGE="${DOUYIN_PARSER_IMAGE:-ballbasecn/douyin-parser}"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_PASSWORD="${DEPLOY_PASSWORD:-}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
DEPLOY_BASE_DIR="${DEPLOY_BASE_DIR:-/root/apps/parsers/douyin-parser}"
PORT="${PORT:-8080}"
SERVER_HEALTHCHECK_URL="${SERVER_HEALTHCHECK_URL:-http://127.0.0.1:${PORT}/api/v1/health}"
SERVER_CAPABILITIES_URL="${SERVER_CAPABILITIES_URL:-http://127.0.0.1:${PORT}/api/v1/capabilities}"

SKIP_BUILD=0
SKIP_EXPORT=0
SKIP_DEPLOY=0
DRY_RUN=0

usage() {
  cat <<'USAGE'
用法：
  ./scripts/release-prod.sh [选项]

选项：
  --image-tag <value>    指定发布版本号
  --skip-build           跳过镜像构建
  --skip-export          跳过 bundle 导出
  --skip-deploy          跳过上传和部署
  --dry-run              只打印将执行的命令
  -h, --help             查看帮助
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-tag)
      [[ $# -ge 2 ]] || { echo "--image-tag 需要一个值" >&2; exit 1; }
      IMAGE_TAG="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    --skip-export)
      SKIP_EXPORT=1
      shift
      ;;
    --skip-deploy)
      SKIP_DEPLOY=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage
      exit 1
      ;;
  esac
done

run_step() {
  local description="$1"
  shift
  echo "==> ${description}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run] %q' "$1"
    shift
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "缺少命令: $1" >&2
    exit 1
  }
}

require_tool docker
require_tool git
require_tool curl

if [[ "${SKIP_DEPLOY}" -eq 0 ]]; then
  [[ -n "${DEPLOY_HOST}" ]] || {
    echo "缺少 DEPLOY_HOST。请在 ${RELEASE_CONFIG} 中配置，或执行前导出。" >&2
    exit 1
  }
fi

SSH_CHECK_CMD=(ssh -p "${DEPLOY_PORT}" -o StrictHostKeyChecking=no "${DEPLOY_USER}@${DEPLOY_HOST}")
if [[ -n "${DEPLOY_PASSWORD}" ]]; then
  require_tool sshpass
  export SSHPASS="${DEPLOY_PASSWORD}"
  SSH_CHECK_CMD=(sshpass -e "${SSH_CHECK_CMD[@]}")
fi

if [[ "${SKIP_BUILD}" -eq 0 ]]; then
  run_step \
    "构建发布镜像" \
    env \
    IMAGE_TAG="${IMAGE_TAG}" \
    TARGET_PLATFORM="${TARGET_PLATFORM}" \
    DOUYIN_PARSER_IMAGE="${DOUYIN_PARSER_IMAGE}" \
    "${ROOT_DIR}/scripts/build-release-image.sh"
fi

if [[ "${SKIP_EXPORT}" -eq 0 ]]; then
  run_step \
    "导出发布 bundle" \
    env \
    IMAGE_TAG="${IMAGE_TAG}" \
    DOUYIN_PARSER_IMAGE="${DOUYIN_PARSER_IMAGE}" \
    "${ROOT_DIR}/scripts/export-release-bundle.sh"
fi

if [[ "${SKIP_DEPLOY}" -eq 0 ]]; then
  run_step \
    "上传服务器并更新服务" \
    env \
    IMAGE_TAG="${IMAGE_TAG}" \
    DEPLOY_HOST="${DEPLOY_HOST}" \
    DEPLOY_USER="${DEPLOY_USER}" \
    DEPLOY_PASSWORD="${DEPLOY_PASSWORD}" \
    DEPLOY_PORT="${DEPLOY_PORT}" \
    DEPLOY_BASE_DIR="${DEPLOY_BASE_DIR}" \
    DEPLOY_ENV_FILE="${DEPLOY_ENV_FILE}" \
    DOUYIN_PARSER_IMAGE="${DOUYIN_PARSER_IMAGE}" \
    "${ROOT_DIR}/scripts/deploy-prebuilt-release.sh"
fi

if [[ "${DRY_RUN}" -eq 0 && "${SKIP_DEPLOY}" -eq 0 ]]; then
  run_step "检查服务健康状态" "${SSH_CHECK_CMD[@]}" "curl -fsS '${SERVER_HEALTHCHECK_URL}'"
  echo
  run_step "检查服务能力声明" "${SSH_CHECK_CMD[@]}" "curl -fsS '${SERVER_CAPABILITIES_URL}'"
  echo
fi

echo "==> 发布完成"
echo "IMAGE_TAG=${IMAGE_TAG}"
echo "RELEASE_CONFIG=${RELEASE_CONFIG}"
