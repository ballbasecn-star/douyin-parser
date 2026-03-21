# 项目结构与分层规范

## 目的

本文档定义 `douyin-parser` 在向“企业级、可持续迭代”的 Python 项目演进时，推荐采用的代码分层和目录结构。

当前仓库已经有一套可运行的单视频解析结构。本文档不是要求立刻推翻重写，而是用于约束后续新增功能，尤其是“博主监控”相关能力，避免代码继续向单文件和跨层耦合方向扩散。

## 设计原则

### 1. 单一职责

每一层只做一类事情：

- API 层负责接收请求和返回响应
- Service 层负责业务编排
- Repository 层负责数据库访问
- Domain / Model 层负责实体与核心规则
- Infra 层负责第三方系统、配置、日志、存储等基础设施

### 2. 依赖方向单向

依赖应尽量按以下方向流动：

`api -> services -> repositories -> database`

以及：

`services -> domain`

基础设施依赖可以被上层调用，但业务规则不能写进基础设施层。

### 3. 保留稳定内核

当前单视频处理能力是项目最稳定的内核。后续博主监控、调度、持久化等能力应尽量“包裹并复用”这套内核，而不是复制一份新的解析流程。

### 4. 渐进式重构

当前仓库可以先保持现状运行；新增模块按新结构编写。只有在边界清晰、收益明确时，才逐步将旧逻辑迁入新结构。

## 推荐的目标目录结构

推荐的中长期结构如下：

```text
douyin-parser/
├── app/                           # 新后端主包
│   ├── api/                       # HTTP 路由与请求/响应适配
│   ├── services/                  # 业务流程编排
│   ├── repositories/              # 数据访问层
│   ├── domain/                    # 领域实体与核心规则
│   ├── schemas/                   # API DTO / 序列化结构
│   ├── tasks/                     # 定时任务与后台任务
│   ├── infra/                     # 配置、数据库、日志、外部服务客户端
│   └── utils/                     # 通用工具函数
├── douyin/                        # 现有单视频解析核心（短期保留）
├── web/                           # 现有 Web UI 与 Flask 入口
├── scripts/                       # 面向运维或 agent 的脚本
├── deploy/                        # 部署配置
├── docs/                          # 项目文档
├── tests/                         # 自动化测试
└── main.py                        # 现有 CLI 入口
```

## 分层职责说明

### API 层

建议目录：

- `app/api/`

职责：

- 接收 HTTP 请求
- 做最小输入校验
- 调用 service
- 将结果转换为统一响应结构

禁止事项：

- 直接拼装复杂业务逻辑
- 直接操作数据库
- 直接写 SQL
- 在路由函数内调用外部第三方接口完成完整业务流程

### Service 层

建议目录：

- `app/services/`

职责：

- 组织业务流程
- 编排多个 repository 和外部能力
- 负责事务边界
- 负责业务级错误处理

适合放在这里的示例：

- `creator_service.py`
- `creator_sync_service.py`
- `video_analysis_service.py`

### Repository 层

建议目录：

- `app/repositories/`

职责：

- 按实体或聚合封装数据库访问
- 屏蔽 SQL 或 ORM 细节
- 提供清晰的数据读写接口

适合放在这里的示例：

- `creator_repository.py`
- `video_repository.py`
- `analysis_repository.py`

### Domain 层

建议目录：

- `app/domain/`

职责：

- 领域实体
- 领域规则
- 核心值对象

说明：

如果项目仍然较轻，也可以先把领域实体与 ORM 模型分开得不那么彻底，但业务规则依然不应写进 API 或 Repository。

### Schemas 层

建议目录：

- `app/schemas/`

职责：

- 定义 API 请求和响应结构
- 统一字段命名
- 约束对外契约

### Tasks 层

建议目录：

- `app/tasks/`

职责：

- 定时任务
- 批处理任务
- 后台同步任务

当前阶段说明：

第一版博主监控不强依赖复杂任务队列，但这个目录要预留。后续如果引入 APScheduler、cron 触发器或消息队列，统一在这一层收口。

### Infra 层

建议目录：

- `app/infra/`

职责：

- 数据库连接与会话管理
- 配置加载
- 第三方 API 客户端
- 日志与监控
- 缓存、对象存储等基础设施封装

适合放在这里的示例：

- `config.py`
- `db.py`
- `siliconflow_client.py`
- `douyin_web_client.py`

## 针对当前仓库的演进建议

### 当前稳定保留区

以下内容暂时可以保留原位置，不必马上迁移：

- `douyin/crawler.py`
- `douyin/parser.py`
- `douyin/transcriber.py`
- `douyin/analyzer.py`
- `web/app.py`（当前已收敛为 Web 启动包装层）

原因：

- 已有功能可用
- 迁移成本高
- 当前最重要的是把新能力的边界建对

### 新功能的推荐落点

与“博主监控 V1”相关的新代码，建议优先按新结构编写，例如：

```text
app/
  api/
    creators.py
    videos.py
  services/
    creator_service.py
    creator_sync_service.py
    video_analysis_service.py
  repositories/
    creator_repository.py
    video_repository.py
    video_analysis_repository.py
  infra/
    db.py
    settings.py
```

### 兼容策略

新服务层可以先直接调用现有 `douyin/parser.py` 中的单视频处理能力，而不是立刻重写整条链路。

### 当前已完成的第一步重构

当前仓库已经完成了第一轮结构化收敛：

- `app/api/` 已承接 Web/API 路由
- `app/services/` 已承接视频解析与系统服务编排
- `app/domain/` 已承接单视频核心领域模型 `VideoInfo`
- `app/schemas/` 已承接解析请求结构
- `app/infra/` 已承接应用基础配置与 Cookie 基础设施
- `web/app.py` 现在只负责启动 Flask 服务和 Cookie Webhook

这意味着后续新增能力应继续落在 `app/` 下，而不是再回到 `web/app.py` 堆逻辑。

## 测试结构建议

推荐至少建立：

```text
tests/
├── unit/
├── integration/
└── e2e/
```

建议覆盖：

- `unit/`：纯业务逻辑、解析函数、数据映射
- `integration/`：数据库、第三方 API 适配层、同步流程
- `e2e/`：关键 HTTP API 流程

## 命名规范

- `*_service.py`：业务服务
- `*_repository.py`：数据访问
- `*_client.py`：外部服务客户端
- `*_schema.py` 或 `schemas/*.py`：请求响应结构
- `*_task.py`：任务执行器

## 当前阶段的强约束

从现在开始，新增与监控能力相关的代码应遵守以下规则：

1. 不把新的复杂业务流程继续堆进 `web/app.py`
2. 不把数据库访问直接写进路由层
3. 不把博主视频同步逻辑直接塞进现有 `douyin/crawler.py`
4. 单视频解析内核继续复用，但监控流程要建立独立 service

## 何时更新本文档

当以下内容变化时需要更新：

- 新的目录结构正式落地
- 分层边界发生变化
- 引入新的后端框架
- 从单体结构演进到多服务结构
