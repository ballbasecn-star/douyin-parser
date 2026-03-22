#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

IMAGE_REPO="${IMAGE_REPO:-ballbasecn/douyin-parser}"
BASE_IMAGE_REPO="${BASE_IMAGE_REPO:-ballbasecn/douyin-parser-base}"
PLATFORM="${PLATFORM:-linux/amd64}"
ARCH_SUFFIX="${ARCH_SUFFIX:-amd64}"
BASE_IMAGE_VERSION="${BASE_IMAGE_VERSION:-python3.11-bookworm-${ARCH_SUFFIX}}"
BASE_IMAGE="${BASE_IMAGE_REPO}:${BASE_IMAGE_VERSION}"

DEPLOY_HOST="${DEPLOY_HOST:-117.72.207.52}"
DEPLOY_USER="${DEPLOY_USER:-root}"
DEPLOY_APP_DIR="${DEPLOY_APP_DIR:-/root/apps/douyin-parser}"
PUBLIC_HEALTH_URL="${PUBLIC_HEALTH_URL:-https://parser.ballbase.cloud/api/health}"
LOCAL_HEALTH_PORT="${LOCAL_HEALTH_PORT:-28080}"
COMPOSE_TEMPLATE_PATH="${COMPOSE_TEMPLATE_PATH:-$ROOT_DIR/deploy/douyin-parser/compose.yaml}"
REMOTE_COMPOSE_PATH="${DEPLOY_APP_DIR}/compose.yaml"

ALLOW_DIRTY=0
DRY_RUN=0
REBUILD_BASE=0
SKIP_UPLOAD=0
RELEASE_VERSION=""

usage() {
  cat <<'EOF'
用法：
  ./scripts/deploy_prod.sh [选项]

选项：
  --release-version <value>  指定发布版本号；默认自动生成
  --rebuild-base             强制重建基础镜像
  --allow-dirty              允许在工作区未提交时发布
  --skip-upload              只构建与导出，不上传服务器
  --dry-run                  仅打印将执行的关键步骤
  -h, --help                 查看帮助

环境变量：
  IMAGE_REPO                 应用镜像仓库，默认 ballbasecn/douyin-parser
  BASE_IMAGE_REPO            基础镜像仓库，默认 ballbasecn/douyin-parser-base
  DEPLOY_HOST                生产服务器地址
  DEPLOY_USER                生产服务器用户
  DEPLOY_PASSWORD            可选；若设置则使用 sshpass
  DEPLOY_APP_DIR             生产应用目录
  PUBLIC_HEALTH_URL          部署后公网健康检查地址
  COMPOSE_TEMPLATE_PATH      本地 compose 模板路径
EOF
}

log() {
  printf '[deploy] %s\n' "$*"
}

die() {
  printf '[deploy] 错误: %s\n' "$*" >&2
  exit 1
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

run_shell() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  /bin/zsh -lc "$*"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --release-version)
      [[ $# -ge 2 ]] || die "--release-version 需要一个值"
      RELEASE_VERSION="$2"
      shift 2
      ;;
    --rebuild-base)
      REBUILD_BASE=1
      shift
      ;;
    --allow-dirty)
      ALLOW_DIRTY=1
      shift
      ;;
    --skip-upload)
      SKIP_UPLOAD=1
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
      die "未知参数: $1"
      ;;
  esac
done

require_tool() {
  command -v "$1" >/dev/null 2>&1 || die "缺少命令: $1"
}

require_tool git
require_tool docker
require_tool curl

if [[ -n "${DEPLOY_PASSWORD:-}" ]]; then
  require_tool sshpass
fi

APP_VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT_DIR/app/version.py" | head -n 1)"
[[ -n "$APP_VERSION" ]] || die "无法从 app/version.py 读取应用版本"

GIT_SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

if [[ -z "$RELEASE_VERSION" ]]; then
  RELEASE_VERSION="v${APP_VERSION}-${TIMESTAMP}-${GIT_SHA}"
fi

APP_IMAGE="${IMAGE_REPO}:${RELEASE_VERSION}-${ARCH_SUFFIX}"
TAR_PATH="/tmp/douyin-parser-${RELEASE_VERSION}-${ARCH_SUFFIX}.tar"
REMOTE_TAR_PATH="${DEPLOY_APP_DIR}/$(basename "$TAR_PATH")"
RELEASE_ENV_PATH="${DEPLOY_APP_DIR}/release.env"

[[ -f "$COMPOSE_TEMPLATE_PATH" ]] || die "找不到 compose 模板: ${COMPOSE_TEMPLATE_PATH}"

if [[ "$ALLOW_DIRTY" -ne 1 ]]; then
  STATUS_OUTPUT="$(git -C "$ROOT_DIR" status --porcelain)"
  if [[ -n "$STATUS_OUTPUT" ]]; then
    die "当前工作区存在未提交改动。请先提交，或使用 --allow-dirty 明确允许发布。"
  fi
fi

log "应用版本: ${APP_VERSION}"
log "发布版本: ${RELEASE_VERSION}"
log "应用镜像: ${APP_IMAGE}"
log "基础镜像: ${BASE_IMAGE}"

if [[ "$REBUILD_BASE" -eq 1 ]] || ! docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
  log "构建基础镜像"
  run_cmd docker buildx build \
    --platform "$PLATFORM" \
    -f "$ROOT_DIR/Dockerfile.base" \
    -t "$BASE_IMAGE" \
    --load \
    "$ROOT_DIR"
else
  log "复用已有基础镜像 ${BASE_IMAGE}"
fi

log "构建应用镜像"
run_cmd docker buildx build \
  --platform "$PLATFORM" \
  -f "$ROOT_DIR/Dockerfile" \
  --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
  -t "$APP_IMAGE" \
  --load \
  "$ROOT_DIR"

SMOKE_CONTAINER="douyin-parser-smoke-${GIT_SHA}"

log "本地容器烟测"
if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '[dry-run] docker run --rm -d --platform %s --name %s -p %s:8080 %s\n' "$PLATFORM" "$SMOKE_CONTAINER" "$LOCAL_HEALTH_PORT" "$APP_IMAGE"
else
  docker stop "$SMOKE_CONTAINER" >/dev/null 2>&1 || true
  CONTAINER_ID="$(docker run --rm -d --platform "$PLATFORM" --name "$SMOKE_CONTAINER" -p "${LOCAL_HEALTH_PORT}:8080" "$APP_IMAGE")"
  trap 'docker stop "$SMOKE_CONTAINER" >/dev/null 2>&1 || true' EXIT
  for _ in {1..20}; do
    if curl -fsS "http://127.0.0.1:${LOCAL_HEALTH_PORT}/api/health" >/dev/null; then
      break
    fi
    sleep 2
  done
  curl -fsS "http://127.0.0.1:${LOCAL_HEALTH_PORT}/api/health"
  echo
  docker stop "$CONTAINER_ID" >/dev/null 2>&1 || true
  trap - EXIT
fi

log "导出应用镜像"
run_cmd docker save -o "$TAR_PATH" "$APP_IMAGE"

if [[ "$SKIP_UPLOAD" -eq 1 ]]; then
  log "已跳过上传。镜像 tar 在 ${TAR_PATH}"
  exit 0
fi

SSH_TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"
SSH_BASE=(ssh -o StrictHostKeyChecking=no "$SSH_TARGET")
SCP_BASE=(scp -o StrictHostKeyChecking=no)

if [[ -n "${DEPLOY_PASSWORD:-}" ]]; then
  SSH_BASE=(sshpass -p "$DEPLOY_PASSWORD" ssh -o StrictHostKeyChecking=no "$SSH_TARGET")
  SCP_BASE=(sshpass -p "$DEPLOY_PASSWORD" scp -o StrictHostKeyChecking=no)
fi

log "上传镜像到服务器"
run_cmd "${SSH_BASE[@]}" "mkdir -p '${DEPLOY_APP_DIR}'"
run_cmd "${SCP_BASE[@]}" "$TAR_PATH" "${SSH_TARGET}:${REMOTE_TAR_PATH}"
run_cmd "${SCP_BASE[@]}" "$COMPOSE_TEMPLATE_PATH" "${SSH_TARGET}:${REMOTE_COMPOSE_PATH}.new"

RELEASE_ENV_CONTENT=$(cat <<EOF
DOUYIN_PARSER_IMAGE=${APP_IMAGE}
APP_RELEASE_VERSION=${RELEASE_VERSION}
EOF
)

REMOTE_SCRIPT=$(cat <<EOF
set -euo pipefail
cd '${DEPLOY_APP_DIR}'
if [ -f compose.yaml ]; then
  cp compose.yaml "compose.yaml.bak-\$(date +%Y%m%d-%H%M%S)"
fi
mv '${REMOTE_COMPOSE_PATH}.new' '${REMOTE_COMPOSE_PATH}'
if [ -f release.env ]; then
  cp release.env "release.env.bak-\$(date +%Y%m%d-%H%M%S)"
fi
cat > '${RELEASE_ENV_PATH}' <<'RELEASE_ENV'
${RELEASE_ENV_CONTENT}
RELEASE_ENV
docker load -i '${REMOTE_TAR_PATH}'
docker compose --env-file release.env up -d
sleep 8
docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' douyin-parser
echo '--- compose image ---'
sed -n '1,40p' '${REMOTE_COMPOSE_PATH}'
echo '--- release env ---'
sed -n '1,20p' '${RELEASE_ENV_PATH}'
EOF
)

log "在服务器上加载镜像并更新 compose"
run_cmd "${SSH_BASE[@]}" "$REMOTE_SCRIPT"

log "公网健康检查"
run_cmd curl -fsS "$PUBLIC_HEALTH_URL"
echo

log "发布完成"
log "release_version=${RELEASE_VERSION}"
log "image=${APP_IMAGE}"
log "tar=${TAR_PATH}"
