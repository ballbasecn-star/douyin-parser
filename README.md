<p align="center">
  <h1 align="center">🎬 Douyin Parser</h1>
  <p align="center">
    <strong>完全本地化的抖音视频解析与文案提取工具</strong>
  </p>
  <p align="center">
    从抖音分享链接中提取视频信息、完整描述和视频内语音文案
  </p>
  <p align="center">
    <a href="#功能特性">功能特性</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="#使用指南">使用指南</a> •
    <a href="#项目架构">项目架构</a> •
    <a href="#cookie-管理">Cookie 管理</a> •
    <a href="#常见问题">FAQ</a>
  </p>
</p>

---

## ✨ 功能特性

- 🔗 **智能链接解析** — 支持抖音分享文本、短链接、完整链接，自动提取视频 ID
- 📊 **完整视频数据** — 标题、作者、时长、播放量、点赞、评论、收藏、封面等
- 🎙️ **视频语音转录** — 基于 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 将视频内语音转为文字
- ☁️ **云端转录** — 可选 [Groq API](https://groq.com/) 或 SiliconFlow 云端快速转录
- 🧠 **AI 爆款文案拆解** — 一键提炼黄金前三秒、文案框架、情绪留存点，支持 DeepSeek 等多模型
- 🖥️ **高颜值 Web UI** — 赛博朋克深色主题，支持 SSE 服务端推送渐进式渲染与实时系统日志
- 🍪 **Cookie 自动管理** — 内置 Webhook 服务器 + Chrome 扩展，自动无感更新 Cookie
- 🔒 **完全本地化** — 零远程中间服务依赖，直接与抖音 API 通信
- 📦 **命令行工具** — 简洁的 CLI 界面，支持 JSON 输出，易于集成到其他系统

## 📸 示例输出

```
============================================================
📹 抖音视频信息
============================================================

📌 标题: 这个时代简直是为了我们而生的
👤 作者: 西门聪明蛋XD (@65371323007)
🔗 视频ID: 7602296040360228075
⏱️  时长: 02:45
📅 发布时间: 2026-02-02 23:51:34

📊 数据: ❤️ 20,390 | 💬 464 | 🔄 3,613 | ⭐ 14,828

🏷️  标签: #ai编程 #vibe氛围 #学习 #进步 #网站

📝 视频描述:
----------------------------------------
这个时代简直是为了我们而生的
#ai编程 #vibe氛围 #学习 #进步 #网站
----------------------------------------

🎙️  视频内完整文案 (语音转录):
========================================
你有没有发觉这个时代简直就是为了我们而生的...
========================================

🧠  AI 爆款文案拆解:
========================================
【Hook片段】: "你有没有发觉这个时代简直就是为了我们而生的"
【Hook类型】: 情感共鸣类
【内容框架】: 痛点/共鸣引入 -> 具体案例/场景展示 -> 价值观输出/行动号召
【留存点】: 
  - 提到“这个时代”，引发大环境的共鸣
  - ...
========================================
```

## 🚀 快速开始

### 环境要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.9 | 运行环境 |
| [ffmpeg](https://ffmpeg.org/) | 任意 | 音频提取（转录时需要） |

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/your-username/douyin-parser.git
cd douyin-parser

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置抖音 Cookie（必须，详见"Cookie 管理"章节）
python main.py cookie set "你的抖音Cookie字符串"

# 4. 验证安装
python main.py --no-transcript "抖音分享链接"
```

### 安装 ffmpeg（转录时需要）

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# 下载: https://ffmpeg.org/download.html
```

## 📖 使用指南

### 🖥️ 启动网页版 (推荐)

如果你更喜欢可视化操作，可以启动内置的高颜值 Web 界面：

```bash
python -m web.app --port 8081
```

> 浏览器访问 `http://localhost:8081` 即可体验！
> **Web 端特性**：暗黑科技风 UI、SSE 流式渐进渲染（解析、转录、拆解分步展示）、实时后端执行日志跟踪。

### 📦 命令行基本用法

```bash
# 从分享文本解析并附加 AI 爆款拆解预存（自动提取链接 + 转录语音文案 + 深度拆解）
python main.py --analyze "2.30 复制打开抖音，看看【某某的作品】... https://v.douyin.com/xxxxx/"

# 仅转录不拆解
python main.py "https://v.douyin.com/xxxxx/"

# 仅获取视频信息（不转录，速度快）
python main.py --no-transcript "https://v.douyin.com/xxxxx/"

# JSON 格式输出（便于程序化处理）
python main.py --json "https://v.douyin.com/xxxxx/"

# 交互式输入
python main.py
```

### 语音转录选项

```bash
# 本地转录 — 默认使用 large-v3 模型（最佳中文效果，首次需下载 3GB）
python main.py "分享文本"

# 选择更小的模型（下载快，精度略低）
python main.py --model small "分享文本"     # 500MB
python main.py --model tiny "分享文本"      # 75MB

# 云端转录 — 使用 Groq API（极快，需 API Key）
export GROQ_API_KEY="gsk_xxxxxxxx"
python main.py --cloud "分享文本"
```

### 模型大小对比

| 模型 | 大小 | 中文效果 | 速度 | 推荐场景 |
|------|------|---------|------|---------|
| `tiny` | 75 MB | ★★☆☆☆ | 极快 | 测试验证 |
| `base` | 145 MB | ★★★☆☆ | 快 | 日常使用 |
| `small` | 488 MB | ★★★★☆ | 中 | 性价比首选 |
| `medium` | 1.5 GB | ★★★★☆ | 较慢 | 高精度 |
| `large-v3` | 3 GB | ★★★★★ | 慢 | 最佳效果 |
| Groq 云端 | — | ★★★★★ | 极快 | 有网络时首选 |

### 完整命令参考

```
python main.py [选项] [文本]

位置参数:
  text                       抖音分享文本或链接

选项:
  --no-transcript            不转录视频内语音（仅获取基本信息）
  --cloud                    使用云端 API (Groq 或 SiliconFlow) 转录
  --model {tiny,base,small,medium,large-v3}
                             本地转录模型大小 (默认: large-v3)
  --analyze                  使用大模型对视频转录文案进行爆款深度拆解 (默认需要配置环境变量)
  --ai-model MODEL_NAME      指定用于拆解的模型 (默认: Pro/deepseek-ai/DeepSeek-V3.2)
  --json                     以 JSON 格式输出
  --api-url URL              自定义 API 地址
  -v, --verbose              详细日志输出

Cookie 管理:
  python main.py cookie set "Cookie值"     手动设置 Cookie
  python main.py cookie show               查看 Cookie 状态
  python main.py cookie webhook            启动 Webhook 接收服务
```

## 🏗️ 项目架构

### 目录结构

```
douyin-parser/
├── main.py                          # CLI 兼容入口（实际实现已迁移到 app/cli）
├── douyin/                          # 核心模块
│   ├── __init__.py                  # 包初始化，版本号
│   ├── crawler.py                   # 兼容导出层（抓取逻辑已迁移到 app/services + app/infra）
│   ├── abogus.py                    # 兼容导出层（签名算法已迁移到 app/infra）
│   ├── parser.py                    # 兼容导出层（主解析流程已迁移到 app/services）
│   ├── models.py                    # 兼容导出层（VideoInfo 已迁移到 app/domain）
│   ├── transcriber.py               # 兼容导出层（转录能力已迁移到 app/services + app/infra）
│   ├── analyzer.py                  # 兼容导出层（文案分析已迁移到 app/services）
│   └── cookie_manager.py            # 兼容导出层（Cookie 基础设施已迁移到 app/infra）
├── app/                             # 新后端主包
│   ├── api/                         # Web/API 路由与请求适配
│   ├── cli/                         # CLI 命令入口与子命令实现
│   ├── services/                    # 业务流程编排（含抓取、转录、分析与主解析）
│   ├── domain/                      # 领域模型（含 VideoInfo）
│   ├── schemas/                     # 请求结构定义
│   └── infra/                       # 应用配置、Cookie、签名、媒体与抖音请求基础设施
├── chrome-cookie-sniffer/           # Chrome 浏览器扩展
│   ├── manifest.json                # 扩展配置
│   ├── background.js                # 请求拦截 + Cookie 捕获
│   ├── popup.html                   # 扩展弹窗界面
│   ├── popup.js                     # 弹窗交互逻辑
│   └── README.md                    # 扩展使用说明
├── cookie_data/                     # Cookie 存储目录（自动创建）
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
└── .gitignore
```

### 数据流

```
                          ┌──────────────────────────────────────┐
                          │          douyin-parser (本地)         │
                          │                                      │
  分享文本 ───────────▶   │  1. 提取链接                          │
                          │  2. 重定向 → 获取 aweme_id            │
                          │  3. 构造参数 + a_bogus 签名            │
  cookie_data/ ────────▶  │  4. 携带 Cookie 请求抖音 API  ────────│───▶  抖音 API
                          │  5. 解析视频数据 → VideoInfo           │
                          │  6. 下载视频 → ffmpeg → Whisper 转录   │
                          │                                      │
                          └──────────────────────────────────────┘
                                         │
                                         ▼
                                    结构化输出
                               (文本 / JSON / dict)
```

### 核心模块说明

| 模块 | 职责 | 依赖 |
|------|------|------|
| `app/services/video_fetch_service.py` | 链接提取、视频数据解析、单视频抓取流程编排 | `app/infra/douyin_web_client.py`, `app/domain` |
| `app/services/transcript_service.py` | 组织本地/云端转录流程与临时文件清理 | `app/infra/media_tools.py`, `faster-whisper` |
| `app/services/analysis_service.py` | 组织 SiliconFlow 文案分析并解析结构化结果 | `app/infra/siliconflow_client.py` |
| `app/services/video_parse_service.py` | 顶层单视频解析入口，协调抓取、转录和分析 | `video_fetch_service.py`, `transcript_service.py`, `analysis_service.py` |
| `app/infra/douyin_web_client.py` | 构造请求参数、a_bogus 签名、调用抖音 Web API | `app/infra/douyin_signature.py`, `requests` |
| `app/infra/douyin_signature.py` | 实现 a_bogus 签名算法（基于 SM3 哈希），生成请求防伪参数 | `gmssl` |
| `app/infra/media_tools.py` | 音频提取、视频下载等媒体处理基础设施 | `ffmpeg`, `requests` |
| `models.py` | `VideoInfo` 的兼容导出层，内部已迁移到 `app/domain` | — |
| `transcriber.py` | 兼容导出层，内部已迁移到 `app/services` / `app/infra` | — |
| `analyzer.py` | 兼容导出层，内部已迁移到 `app/services` | — |
| `parser.py` | 兼容导出层，内部已迁移到 `app/services` | — |
| `cookie_manager.py` | 兼容导出层，Cookie 基础设施已迁移到 `app/infra` | — |

## 🍪 Cookie 管理

> **为什么需要 Cookie？**
> 抖音 API 需要有效的登录态 Cookie 才能返回完整数据。没有 Cookie 时，API 会返回空数据。

### 方式一：手动设置（推荐新手）

1. 在浏览器中打开 [抖音网页版](https://www.douyin.com) 并登录
2. 按 `F12` 打开开发者工具 → 切换到 **Network（网络）** 标签
3. 刷新页面，点击任意请求，在 **Headers** 中找到 `Cookie` 字段
4. 复制完整 Cookie 值，运行：

```bash
python main.py cookie set "你复制的Cookie值"
```

### 方式二：Chrome 扩展自动更新（推荐长期使用）

1. 在 Chrome 中加载 `chrome-cookie-sniffer/` 扩展（开发者模式）：
   - 打开 `chrome://extensions/`
   - 开启「开发者模式」
   - 点击「加载已解压的扩展程序」→ 选择 `chrome-cookie-sniffer/` 目录

2. 启动 Webhook 接收服务：
```bash
python main.py cookie webhook --port 5555
```

3. 在扩展中设置 Webhook URL 为 `http://localhost:5555`

4. 浏览抖音网页时，Cookie 将自动捕获并更新

### 查看 Cookie 状态

```bash
python main.py cookie show
```

```
🍪 Cookie 状态:
   来源: webhook
   更新时间: 2026-03-01T12:15:44
   长度: 6137 字符
   预览: xg_device_score=7.003...
```

## 🔧 配置

### 环境变量

在项目根目录创建 `.env` 文件（参照 `.env.example`）：

```env
# Groq API Key（使用 --cloud 云端转录时需要）
# 免费获取: https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

## 📦 依赖说明

```
requests          HTTP 请求
python-dotenv     环境变量加载
gmssl             SM3 哈希算法（a_bogus 签名）
faster-whisper    语音转文字（本地转录）
ffmpeg            音频提取（系统依赖）
```

## ❓ 常见问题

### Q: 解析失败，返回空数据？

**A:** Cookie 过期或无效。运行 `python main.py cookie show` 检查 Cookie 状态，如果过期请重新设置。

### Q: 首次转录很慢？

**A:** 首次运行需要下载 Whisper 模型。`large-v3` 约 3GB，如网络较慢，可先用 `--model tiny`（75MB）测试，或使用 `--cloud` 云端转录。

### Q: 如何在代码中调用？

```python
from douyin.parser import parse

# 基本解析
result = parse("https://v.douyin.com/xxxxx/", enable_transcript=False)
print(result.title)
print(result.author)
print(result.to_dict())  # JSON 序列化

# 含转录
result = parse("https://v.douyin.com/xxxxx/", model_size="small")
print(result.transcript)
```

### Q: a_bogus 签名失败？

**A:** `abogus.py` 中的 `ua_code` 基于 `Chrome/90.0.4430.212` 生成。如果抖音更新了反爬策略，可能需要更新签名算法。

### Q: 支持哪些链接格式？

| 格式 | 示例 | 支持 |
|------|------|:---:|
| 分享文本 | `2.30 复制打开抖音... https://v.douyin.com/xxx/` | ✅ |
| 短链接 | `https://v.douyin.com/xxxxx/` | ✅ |
| 完整链接 | `https://www.douyin.com/video/1234567890` | ✅ |
| 图文/笔记 | `https://www.douyin.com/note/1234567890` | ✅ |

## ⚠️ 免责声明

- 本项目仅供**学习交流**使用，请勿用于商业或非法用途
- 使用本工具时请遵守抖音的 [服务条款](https://www.douyin.com/agreements/)
- Cookie 属于个人隐私数据，请妥善保管，不要泄露
- 签名算法来源于开源项目 [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)，遵循 GPL-3.0 协议
- 本项目不提供任何形式的担保，因使用本工具产生的一切后果由使用者自行承担

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。

> **注意**：`douyin/abogus.py` 文件源自 [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)，原始协议为 GPL-3.0。如需商用，请注意该文件的许可约束。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 🙏 致谢

- [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader) — a_bogus 签名算法
- [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — 项目灵感和 Cookie Sniffer
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — 高性能语音转文字
- [Groq](https://groq.com/) — 超快云端推理 API
