# 模块：博主监控

## 状态

规划中，尚未实现。

## 目的

在现有单视频解析内核之上，新增以“博主”为中心的工作流。

它应允许用户：

1. 通过主页分享链接添加对标博主
2. 保存稳定的博主标识
3. 同步该博主的视频列表
4. 手动选择某些视频执行转录和分析

## 计划职责

### 博主管理

- 接收主页分享短链
- 解析短链并跟随跳转
- 提取稳定博主标识
- 持久化保存博主信息与状态

### 博主视频同步

- 拉取博主视频列表
- 处理分页
- 保存或更新视频记录，避免重复
- 记录最近同步时间

### 手动深度分析

- 允许用户主动挑选某条视频做深度处理
- 复用现有单视频解析内核
- 保存转录与分析结果

## 建议数据对象

### Creator

- `id`
- `source_url`
- `resolved_url`
- `stable_user_id`
- `nickname`
- `domain_tag`
- `remark`
- `status`
- `created_at`
- `updated_at`

### CreatorVideo

- `id`
- `creator_id`
- `video_id`
- `title`
- `share_url`
- `cover_url`
- `publish_time`
- `play_count`
- `like_count`
- `comment_count`
- `share_count`
- `collect_count`
- `first_seen_at`
- `last_synced_at`

### VideoAnalysis

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

## V1 边界

V1 先做到：

- 博主接入
- 博主视频列表同步
- 手动选择视频做深度分析

V1 不做：

- 自动分析所有同步到的视频
- 重型任务队列基础设施
- 定时报表

## 仍待确认的问题

这些问题在正式实现前需要明确：

1. 哪个字段作为博主的最终主键
2. V1 是否接受 SQLite 作为持久化存储
3. 首次同步时要回溯多少历史视频
4. 列表页最重要的筛选与排序字段是什么
