# 模块：单视频解析内核

## 目的

这一组模块负责处理“单条视频”。它是当前产品价值的基础能力，后续更高层的监控能力也应建立在它之上。

## 相关文件

- `douyin/crawler.py`
- `douyin/parser.py`
- `douyin/transcriber.py`
- `douyin/analyzer.py`
- `douyin/models.py`

## 职责

### `crawler.py`

- 提取抖音短链或完整视频链接
- 解析短链跳转
- 提取 `aweme_id`
- 对详情接口参数做签名
- 携带 Cookie 请求抖音详情接口
- 将原始接口数据转换成 `VideoInfo`

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
