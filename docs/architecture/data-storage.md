# 数据存储设计规范

## 目的

本文档定义项目的持久化策略、数据库选型原则、PostgreSQL 使用要求，以及面向“博主监控 V1”的建议数据边界。

## 当前结论

从“博主监控 V1”开始，项目的正式持久化存储应采用 PostgreSQL，而不是继续依赖文件或浏览器本地存储承载核心业务数据。

现有文件型存储仍可保留，但它们不再承担主业务数据职责：

- `cookie_data/`：继续保存 Cookie
- 浏览器 `localStorage`：仅用于前端轻量历史和临时状态

## 为什么需要数据库

单视频解析工具阶段，可以主要依赖：

- 运行时内存
- 本地文件
- 浏览器本地存储

但在“博主监控”阶段会新增以下需求：

- 持久保存博主列表
- 持久保存博主视频列表
- 保存视频历史同步时间
- 保存转录与 AI 分析结果
- 做去重、筛选、排序和后续扩展

这些需求决定了必须引入真正的数据库。

## 选型结论

### 正式数据库

- PostgreSQL 16+ 作为首选

### 不建议作为主存储的方案

- SQLite：适合本地原型，不适合长期线上演进
- MySQL：并非不能用，但当前没有明显收益，且不如 PostgreSQL 适配后续复杂查询和 JSON 数据场景
- 纯文件存储：无法支撑实体关系、去重和查询

## PostgreSQL 使用要求

### 1. 核心业务数据必须落库

至少以下数据必须持久化到 PostgreSQL：

- creators
- creator_videos
- video_analyses

### 2. 关键字段必须有唯一约束

建议至少保证：

- `creators.stable_user_id` 唯一
- `creator_videos.video_id` 唯一

如果一个视频可能归属于不同业务视图，也至少需要：

- `creator_id + video_id` 复合唯一

### 3. 原始返回可保留，但不能替代结构化字段

允许保存 `raw_payload` 或原始 JSON 字段做调试和兼容，但查询、排序和业务逻辑必须依赖结构化字段，而不是每次从 JSON 临时解析。

### 4. 所有时间字段统一保存为 UTC

展示时再转本地时区，避免后续定时任务、统计和服务迁移出现时间混乱。

### 5. 通过迁移工具维护 schema

数据库结构变更必须通过迁移工具管理，禁止线上手改表结构作为常规流程。

推荐：

- ORM / SQL toolkit：SQLAlchemy 2.x
- 迁移工具：Alembic
- 驱动：psycopg 3

## 建议的数据边界

### Creator

表示一个被关注的博主。

建议核心字段：

- `id`
- `stable_user_id`
- `source_url`
- `resolved_url`
- `nickname`
- `display_handle`
- `avatar_url`
- `domain_tag`
- `remark`
- `status`
- `created_at`
- `updated_at`

### CreatorVideo

表示某个博主的一条视频记录。

建议核心字段：

- `id`
- `creator_id`
- `video_id`
- `title`
- `description`
- `share_url`
- `cover_url`
- `publish_time`
- `duration_ms`
- `play_count`
- `like_count`
- `comment_count`
- `share_count`
- `collect_count`
- `first_seen_at`
- `last_synced_at`
- `raw_payload`

### VideoAnalysis

表示一条视频的转录与 AI 分析结果。

建议核心字段：

- `id`
- `video_id`
- `transcript`
- `analysis_json`
- `transcript_provider`
- `analysis_model`
- `status`
- `error_message`
- `created_at`
- `updated_at`

## 索引建议

第一版建议至少建立：

- `creators(stable_user_id)`
- `creator_videos(creator_id, publish_time desc)`
- `creator_videos(video_id)`
- `creator_videos(last_synced_at)`
- `video_analyses(video_id)`
- `video_analyses(status)`

如果后续要做按互动表现筛选，再考虑增加：

- `creator_videos(creator_id, like_count desc)`
- `creator_videos(creator_id, comment_count desc)`

## 数据写入策略

### Creator

- 以 `stable_user_id` 为主键候选做幂等写入
- 已存在时更新昵称、头像、主页链接等可变字段

### CreatorVideo

- 首次同步时写入基础数据
- 后续同步时更新互动指标和 `last_synced_at`
- 不重复插入同一视频

### VideoAnalysis

建议第一版采用“一条视频一份当前分析结果”的简单模式。  
如果未来需要多次重新分析，再扩展为分析历史表。

## 事务原则

建议：

- 同步博主视频列表时，以单次同步批次作为事务边界
- 分析单条视频时，以“分析结果落库”为事务边界
- 不把远程 API 请求长时间包在数据库事务里

## 与现有存储方式的关系

### Cookie

Cookie 目前仍保存在文件中，可以继续保持，但不应纳入 PostgreSQL 第一版核心表。

### 前端历史记录

前端 `localStorage` 中的历史记录属于 UI 辅助信息，不作为主业务数据来源。

### API Key

API Key 仍通过环境变量注入，不进入业务表。

## 后续扩展方向

如果未来加入定时同步或趋势分析，可以继续新增：

- `video_metric_snapshots`
- `sync_jobs`
- `task_runs`

但这些不是 V1 必需项。

## 何时更新本文档

当以下内容变化时必须更新：

- 数据库选型变化
- ORM / 迁移方案变化
- 核心表结构变化
- 持久化边界变化
- 新增快照或任务表
