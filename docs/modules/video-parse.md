# 模块：单视频解析内核

## 目的

这一组模块负责处理“单条视频”。它是当前产品价值的基础能力，后续更高层的监控能力也应建立在它之上。

## 相关文件

- `app/infra/douyin_signature.py`
- `app/infra/douyin_web_client.py`
- `app/infra/media_tools.py`
- `app/infra/siliconflow_client.py`
- `app/services/video_parse_service.py`
- `app/services/video_fetch_service.py`
- `app/services/transcript_service.py`
- `app/services/analysis_service.py`
- `app/domain/video_info.py`
- `douyin/parser.py`（兼容导出层）
- `douyin/transcriber.py`（兼容导出层）
- `douyin/analyzer.py`（兼容导出层）
- `douyin/crawler.py`（兼容导出层）
- `douyin/abogus.py`（兼容导出层）
- `douyin/models.py`（兼容导出层）

## 职责

### `douyin_signature.py`

- 生成 `a_bogus` 签名
- 作为抖音 Web 请求的底层签名算法实现

### `douyin_web_client.py`

- 构造详情接口参数
- 携带签名与请求头调用抖音 Web API
- 解析短链重定向并提取 `aweme_id`

### `media_tools.py`

- 通过 `ffmpeg` 进行音频提取
- 在必要时下载完整视频作为降级方案
- 作为转录流程的媒体处理基础设施

### `video_fetch_service.py`

- 提取抖音短链或完整视频链接
- 将原始接口数据转换成 `VideoInfo`
- 组织单视频抓取流程

### `video_parse_service.py`

- 协调整条单视频处理流程
- 为 SSE API 输出进度事件
- 将转录和分析结果附加到 `VideoInfo`

### `transcript_service.py`

- 执行本地转录或云端转录
- 负责转录流程编排与临时文件清理

### `siliconflow_client.py`

- 调用 SiliconFlow chat completions 接口
- 为文案分析提供基础 API 客户端

### `analysis_service.py`

- 将转录文本发送给 SiliconFlow 聊天接口
- 解析并标准化返回的 JSON 分析结果

## 输入

- 分享文本或直接视频链接
- 来自 Cookie 管理器的 Cookie
- 可选的转录提供方与模型配置
- 可选的 AI 分析请求

## 输出

输出 `VideoInfo`，包含：

- 视频元数据
- 视频统计数据
- 封面与分享链接
- 转录文本
- AI 分析结果

## 运行说明

- 想要稳定行为，实际上基本需要 Cookie
- 即使是云端转录，当前流程也仍然依赖 `ffmpeg`
- 当前 AI 分析默认基于 SiliconFlow

## 变更提醒

如果修改了以下内容，需要同步更新文档：

- 返回结构
- 默认服务商行为
- 转录流程
- 必需环境变量
- `/api/parse-sync` 的错误契约
