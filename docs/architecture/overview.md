# 架构总览

## 系统目标

系统围绕“单视频处理内核”组织。后续新增能力应尽量复用这套内核，而不是复制一套新的解析逻辑。

## 当前运行入口

- CLI 入口：`app/cli/main.py`
- CLI 兼容包装层：`main.py`
- Web UI 与 API：`web/app.py`
- App 分层实现：`app/`
- Agent 客户端：`scripts/douyin_parser_client.py`
- 容器运行：`Dockerfile` 与 `deploy/`

## 当前核心流程

1. 输入抖音分享文本或视频链接
2. 解析短链并提取 `aweme_id`
3. 使用签名参数和 Cookie 请求抖音详情接口
4. 将返回结果转换为 `VideoInfo`
5. 可选执行音频提取与转录
6. 可选执行 AI 文案分析
7. 通过 CLI、Web UI 或同步 API 返回结构化结果

## 主要模块

- `app/infra/douyin_signature.py`
  负责 `a_bogus` 签名算法
- `app/infra/douyin_web_client.py`
  负责抖音 Web 请求参数、签名和详情接口调用
- `app/infra/media_tools.py`
  负责音频提取、视频下载等媒体处理基础设施
- `app/infra/siliconflow_client.py`
  负责 SiliconFlow 聊天接口调用
- `app/services/video_fetch_service.py`
  负责分享链接提取、视频数据解析和单视频抓取流程
- `app/services/transcript_service.py`
  负责本地与云端转录流程
- `app/services/analysis_service.py`
  负责对转录文本做 AI 分析
- `app/services/video_parse_service.py`
  负责协调整条单视频处理流程
- `app/repositories/`
  负责博主、视频和分析结果的持久化读写
- `app/infra/cookie_store.py`
  负责 Cookie 存储、读取与全局管理器
- `app/infra/cookie_webhook.py`
  负责 Cookie Webhook 接收服务
- `app/api/`
  负责 Flask 路由、请求适配与响应组装
- `app/cli/`
  负责 CLI 命令入口、解析命令与 Cookie 子命令
- `app/services/`
  负责视频抓取、转录、分析、主解析编排、系统配置和图片代理等业务服务
- `app/domain/`
  负责领域模型与核心实体，当前已承接 `VideoInfo`
- `app/schemas/`
  负责 HTTP 请求结构定义与参数标准化
- `app/infra/`
  负责应用级配置、路径与基础设施常量，并承接 Cookie、签名和抖音 Web 客户端
- `web/app.py`
  作为 Web 服务启动入口，负责装配 app 并启动运行
- `main.py`
  作为 CLI 兼容包装层，转发到 `app/cli/main.py`

当前仓库内部实现已经统一收口到 `app/`，不再保留旧的 `douyin/` 兼容导出层。

## 当前部署形态

- `douyin-parser` 作为独立容器运行
- 共享 `nginx` 负责 TLS 终止与反向代理
- Cookie 数据通过宿主机目录挂载保存
- API Key 通过 `.env` 注入

## 计划中的监控扩展

下一层架构应新增：

1. 基于主页分享链接解析稳定博主标识
2. 同步博主视频列表
3. 对博主、视频、分析结果做持久化存储
4. 后续再考虑调度层

建议将其实现为单视频内核之上的新层：

- 博主管理模块
- 博主视频同步模块
- 持久化层
- 后续可选的定时调度层

## 设计规则

- 单视频解析内核仍应是唯一理解“单条视频深度处理”的地方
- 博主视频列表同步应与转录/分析执行解耦
- 持久化标识与结果，不依赖聊天上下文作为记忆
- 新增 API 时保持 `success` / `data` / `error` 的统一格式
- 优先渐进式交付，不要过早自动化

## 已知风险

- 抖音详情接口与博主视频列表接口都存在脆弱性
- Cookie 处理仍然有安全敏感性
- 如果把批量工作放进同步 API，响应时间会很差
- 一旦扩展到博主级规模，转录与分析成本会快速增长

## 延伸文档

与当前架构直接相关的专题文档：

- `docs/architecture/project-structure.md`
- `docs/architecture/data-storage.md`
- `docs/architecture/environment-strategy.md`
- `docs/architecture/decisions/0001-monitoring-scope.md`
- `docs/architecture/decisions/0002-use-postgresql.md`
