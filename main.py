#!/usr/bin/env python3
"""
抖音视频解析工具 - 命令行入口

用法:
    python main.py "分享文本"                       # 基本信息 + 语音转录
    python main.py --no-transcript "分享文本"        # 仅基本信息
    python main.py --cloud "分享文本"                # 云端转录 (Groq)
    python main.py --cloud --cloud-provider siliconflow "分享文本"  # SiliconFlow 转录
    python main.py --json "分享文本"                 # JSON 输出

Cookie 管理:
    python main.py cookie set "你的Cookie字符串"     # 手动设置 Cookie
    python main.py cookie show                       # 查看当前 Cookie 状态
    python main.py cookie webhook [--port 5555]      # 启动 Webhook 接收服务
"""
from app.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
