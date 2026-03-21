# 模块：单视频解析内核

## 目的

这一组模块负责处理“单条视频”。它是当前产品价值的基础能力，后续更高层的监控能力也应建立在它之上。

## 相关文件

- `app/infra/douyin_signature.py`
- `app/infra/douyin_web_client.py`
- `app/services/video_fetch_service.py`
- `douyin/parser.py`
- `douyin/transcriber.py`
- `douyin/analyzer.py`
- `app/domain/video_info.py`
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

### `video_fetch_service.py`

- 提取抖音短链或完整视频链接
- 将原始接口数据转换成 `VideoInfo`
- 组织单视频抓取流程

### `parser.py`

- 协调整条单视频处理流程
- 为 SSE API 输出进度事件
- 将转录和分析结果附加到 `VideoInfo`

### `transcriber.py`

- 通过 `ffmpeg` 从直链提取音频
- 必要时降级为先下载完整视频
- 执行本地转录或云端转录

### `analyzer.py`

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
