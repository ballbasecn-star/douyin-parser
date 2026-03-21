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
- `deploy/nginx/compose.yaml`

它们体现了当前生产部署的基本方向：

- `douyin-parser` 接入 `shared-proxy`
- `nginx` 作为共享反向代理

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

### dev

推荐镜像 tag：

- `dev`
- `sha-<commit>`

### prod

推荐镜像 tag：

- `vX.Y.Z`

不建议长期使用：

- `latest` 作为唯一发布依据

## 发布步骤

### 从 dev 到 prod 的建议流程

1. 本地开发与自测
2. 本地镜像构建
3. 本地容器验证
4. 生成固定版本镜像 tag
5. 将镜像导出或推送到镜像仓库
6. 在生产环境更新镜像
7. 重启 `douyin-parser`
8. 验证：
   - 容器健康检查
   - `/api/health`
   - 域名 HTTPS 路由
   - 关键页面与关键 API

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
- nginx 路由变化
- 配置文件组织方式变化
- 数据库接入方式变化
- 发布流程变化
