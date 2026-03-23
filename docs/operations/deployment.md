# 部署说明

## 目的

本文档描述当前项目在 `dev` 与 `prod` 两套环境中的推荐部署方式、目录布局、配置组织与发布步骤。

## 环境概览

当前项目维护两套主要环境：

- `dev`：本地开发与验证
- `prod`：正式生产环境

## dev 部署

### 适用场景

- 本地开发
- 接口调试
- UI 联调
- 数据结构验证
- Docker 镜像验证

### 推荐运行方式

#### 方式 A：直接运行 Python 服务

适合快速调试。

常见流程：

1. 安装依赖
2. 准备本地环境变量
3. 设置本地 Cookie
4. 启动 `web.app`

说明：

- 这种方式启动快
- 适合调试单视频解析内核与前端交互
- 不适合模拟完整生产部署

#### 方式 B：本地 Docker 运行

适合验证镜像、依赖和容器行为。

推荐：

- 使用本地构建镜像
- 单独传入本地开发环境变量
- 不复用生产环境的 `.env`
- 本地优先构建本机架构镜像，不默认构建 `linux/amd64`

### dev 配置建议

建议本地使用独立配置文件，例如：

- `.env.dev`

建议包含：

- `SILICONFLOW_API_KEY`
- `GROQ_API_KEY`
- `COOKIE_DIR`
- `PORT`
- `WEBHOOK_PORT`
- `DATABASE_URL`

### dev 数据目录建议

建议本地开发目录与生产隔离，例如：

```text
./.local/
  cookie_data/
  logs/
  exports/
```

dev 环境数据库建议：

- 使用独立 PostgreSQL 开发数据库
- 数据库名建议：`douyin_parser_dev`
- 示例连接串：
  `DATABASE_URL=postgresql+psycopg://douyin_parser:your_password@127.0.0.1:5432/douyin_parser_dev`

补充说明：

- 当前代码仍保留 SQLite 回退能力，便于测试或临时启动
- 但这不应再作为正式 `dev` 环境标准

## prod 部署

### 适用场景

- 正式对外服务
- 承载真实业务数据
- 作为正式访问入口

### 当前推荐拓扑

当前生产环境推荐采用：

- `douyin-parser` 独立容器
- 共享 `nginx` 作为全局入口
- `nginx` 负责 TLS 终止与域名转发
- 数据与配置通过宿主机挂载持久化

### 当前生产目录建议

推荐目录结构：

```text
/root/apps/
  nginx/
    compose.yaml
    conf.d/
    ssl/
    www/
  douyin-parser/
    compose.yaml
    .env
    data/
      cookie_data/
```

说明：

- `nginx/ssl/` 保存证书
- `douyin-parser/.env` 保存生产环境变量
- `douyin-parser/data/cookie_data/` 保存生产 Cookie 数据

### 当前生产 compose

当前仓库中已有：

- `deploy/douyin-parser/compose.yaml`
- `deploy/douyin-parser/release.env.example`
- `deploy/nginx/compose.yaml`

它们体现了当前生产部署的基本方向：

- `douyin-parser` 接入 `content-shared`
- `nginx` 作为共享反向代理
- 业务容器镜像由 `release.env` 注入，而不是手改 compose

### 生产环境变量建议

生产环境 `.env` 至少应包含：

- `SILICONFLOW_API_KEY`
- `GROQ_API_KEY`
- `COOKIE_DIR=/app/cookie_data`
- `PORT=8080`
- `WEBHOOK_PORT=5555`

- `DATABASE_URL`

### 生产数据库建议

- `prod` 应使用正式 PostgreSQL 数据库
- 建议数据库名示例：`douyin_parser_prod`

禁止：

- 生产环境直接依赖 SQLite 作为主业务存储
- 生产环境与开发环境共用数据库

## nginx 与域名

当前生产环境采用共享 `nginx`，统一处理：

- `80/443`
- 证书挂载
- 域名路由

当前模式下：

- 业务服务不直接暴露公网业务端口
- `nginx` 通过 Docker 网络反向代理到内部容器

## 版本与镜像

### 基础镜像策略

当前推荐将 Docker 镜像拆为两层：

- 基础镜像：预装 `ffmpeg`
- 业务镜像：默认只安装云端转录依赖

这样做的目的：

- 避免每次业务构建都重新安装 `ffmpeg`
- 缩短默认镜像构建时间
- 将本地 Whisper 作为可选能力，而不是默认能力

当前约定：

- 基础镜像示例 tag：`ballbasecn/douyin-parser-base:python3.11-bookworm`
- 业务镜像默认依赖文件：`requirements.txt`
- 本地 Whisper 业务镜像可通过 `requirements.local-whisper.txt` 构建

### dev

推荐镜像 tag：

- `dev`
- `sha-<commit>`

### prod

推荐镜像 tag：

- `v<应用版本>-<时间戳>-<git短提交>-amd64`

不建议长期使用：

- `latest` 作为唯一发布依据

推荐将“应用版本”和“发布版本”区分开：

- 应用版本：代码中的语义版本，例如 `1.0.0`
- 发布版本：一次真实上线对应的版本号，例如 `v1.0.0-20260321-230501-abc1234`

好处：

- 能区分“当前产品版本”和“某次生产发布”
- 健康检查可以直接回显当前 release
- 回滚时更容易定位具体镜像

## 发布步骤

### 从 dev 到 prod 的建议流程

1. 本地开发与自测
2. 运行统一发布脚本 `scripts/deploy_prod.sh`
3. 脚本自动完成：
   - 读取应用语义版本
   - 读取当前 git 短提交
   - 生成发布版本号
   - 按需构建基础镜像
   - 构建 `linux/amd64` 应用镜像
   - 本地运行容器烟测
   - 导出镜像 tar
   - 上传到生产服务器
   - 同步最新的 `compose.yaml` 到生产目录
   - 更新服务器上的 `release.env`
   - 执行 `docker compose --env-file release.env up -d`
   - 做容器健康检查和公网健康检查

### 统一发布脚本

推荐使用：

```bash
./scripts/deploy_prod.sh
```

该脚本默认会：

- 使用 `app/version.py` 里的应用版本
- 使用当前 git 短提交
- 生成发布版本号：
  `v<应用版本>-<时间戳>-<git短提交>`
- 生成应用镜像 tag：
  `ballbasecn/douyin-parser:<发布版本>-amd64`

常用参数：

```bash
# 强制重建基础镜像
./scripts/deploy_prod.sh --rebuild-base

# 在工作区有未提交改动时允许继续发布
./scripts/deploy_prod.sh --allow-dirty

# 指定发布版本号
./scripts/deploy_prod.sh --release-version v1.0.0-20260321-abc1234

# 只构建与导出，不上传服务器
./scripts/deploy_prod.sh --skip-upload

# 仅查看将执行的步骤
./scripts/deploy_prod.sh --dry-run
```

### 发布脚本依赖的环境变量

脚本支持以下变量：

- `IMAGE_REPO`
- `BASE_IMAGE_REPO`
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PASSWORD`
- `DEPLOY_APP_DIR`
- `PUBLIC_HEALTH_URL`

其中：

- 若配置了 `DEPLOY_PASSWORD`，脚本会使用 `sshpass`
- 若未配置，则默认使用本机 SSH key 连接服务器

### 服务器侧文件约定

生产目录下建议至少有：

- `.env`
  - 应用运行配置，例如 `SILICONFLOW_API_KEY`、`DATABASE_URL`
- `release.env`
  - 发布元信息，例如当前镜像 tag、当前发布版本号
- `compose.yaml`
  - 容器编排模板

说明：

- `.env` 面向应用运行配置
- `release.env` 面向部署元信息
- 这两类信息应分开维护，避免将业务密钥和部署版本混在一起
- `compose.yaml` 由发布脚本从仓库中的模板同步到服务器，不建议在线上手改

## 回滚原则

生产环境必须可以回滚到上一个稳定镜像版本。

建议：

- 每次正式发布使用固定版本号
- 保留最近几个稳定镜像 tag
- 不在生产环境直接覆盖为不可追踪的临时版本

## 后续扩展

当项目复杂度继续上升时，可以再扩展本文档：

- 增加 `staging` 环境章节
- 增加 PostgreSQL 部署章节
- 增加备份与恢复章节
- 增加日志与监控章节

## 何时更新本文档

当以下内容变化时必须更新：

- 环境目录布局变化
- compose 结构变化
- 发布脚本行为变化
- 版本号策略变化
- nginx 路由变化
- 配置文件组织方式变化
- 数据库接入方式变化
- 发布流程变化
