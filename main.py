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
import json
import logging
import sys
import os

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def handle_cookie(args):
    """处理 cookie 子命令"""
    from app.infra.cookie_store import get_cookie_manager
    from app.infra.cookie_webhook import start_webhook_server

    cm = get_cookie_manager()
    action = args[0] if args else "show"

    if action == "set":
        if len(args) < 2:
            print("❌ 请提供 Cookie 值")
            print('用法: python main.py cookie set "你的Cookie字符串"')
            sys.exit(1)
        cm.save_cookie(args[1], source="manual")
        print("✅ Cookie 已保存")

    elif action == "show":
        info = cm.get_cookie_info()
        if info.get("exists"):
            print("🍪 Cookie 状态:")
            print(f"   来源: {info['source']}")
            print(f"   更新时间: {info['timestamp']}")
            print(f"   长度: {info['cookie_length']} 字符")
            cookie = cm.get_cookie()
            if cookie:
                print(f"   预览: {cookie[:100]}...")
        else:
            print("⚠️  未设置 Cookie")
            print("💡 设置方式:")
            print('   1. 手动: python main.py cookie set "Cookie内容"')
            print("   2. 自动: python main.py cookie webhook")

    elif action == "webhook":
        port = 5555
        # 检查 --port 参数
        for i, a in enumerate(args):
            if a == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
        setup_logging(True)
        print(f"🔗 启动 Cookie Webhook 接收服务...")
        print(f"   监听地址: http://0.0.0.0:{port}")
        print(f"   请在 Chrome Cookie Sniffer 扩展中设置 Webhook URL")
        print(f"   按 Ctrl+C 停止")
        print()
        try:
            start_webhook_server(port=port, cookie_manager=cm)
        except KeyboardInterrupt:
            print("\n已停止。")

    else:
        print(f"未知的 cookie 命令: {action}")
        print("可用: set / show / webhook")


def handle_parse(args):
    """处理视频解析"""
    import argparse
    from douyin.parser import parse

    parser = argparse.ArgumentParser(
        description="抖音视频解析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py "分享文本"                       # 获取信息 + 转录
  python main.py --no-transcript "分享文本"        # 仅基本信息
  python main.py --cloud "分享文本"                # Groq 云端转录
  python main.py cookie set "Cookie值"            # 设置 Cookie
  python main.py cookie show                      # 查看 Cookie
  python main.py cookie webhook                   # Cookie 接收服务
        """,
    )
    parser.add_argument("text", nargs="?", help="抖音分享文本或链接")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--no-transcript", action="store_true", help="不转录视频内语音")
    parser.add_argument("--analyze", action="store_true", help="使用大模型进行爆款文案拆解分析")
    parser.add_argument("--cloud", action="store_true", help="使用云端 API 转录")
    parser.add_argument("--cloud-provider", default="groq",
                        choices=["groq", "siliconflow"],
                        help="云端服务商 (默认: groq)")
    parser.add_argument("--model", default="large-v3",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="本地转录模型大小 (默认: large-v3)")
    parser.add_argument("--api-url", help="自定义远程 API 地址")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志输出")

    parsed = parser.parse_args(args)
    setup_logging(parsed.verbose)

    # 获取输入文本
    share_text = parsed.text
    if not share_text:
        print("📋 请粘贴抖音分享文本（输入后按回车）:")
        print("-" * 40)
        try:
            share_text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n取消。")
            sys.exit(0)

    if not share_text:
        print("❌ 未输入任何内容")
        sys.exit(1)

    # 提示转录模式
    enable_transcript = not parsed.no_transcript
    enable_analysis = parsed.analyze
    
    if enable_transcript:
        if parsed.cloud:
            provider_name = "Groq" if parsed.cloud_provider == "groq" else "SiliconFlow"
            mode = f"☁️ {provider_name} 云端"
        else:
            mode = f"💻 本地 ({parsed.model})"
            
        if enable_analysis:
            mode += " + 🧠 AI爆款拆解"
            
        print(f"\n🔍 正在解析... [转录模式: {mode}]\n")
    else:
        if enable_analysis:
            print("⚠️ 警告: 已省略转录 (--no-transcript)，文案拆解 (--analyze) 将无效。")
        print("\n🔍 正在解析... [仅基本信息]\n")

    # 确定 API Key
    if parsed.cloud:
        if parsed.cloud_provider == "siliconflow":
            cloud_api_key = os.environ.get("SILICONFLOW_API_KEY")
        else:
            cloud_api_key = os.environ.get("GROQ_API_KEY")
    else:
        cloud_api_key = None

    # 解析
    result = parse(
        share_text,
        service_url=parsed.api_url,
        enable_transcript=enable_transcript,
        use_cloud=parsed.cloud,
        cloud_provider=parsed.cloud_provider,
        model_size=parsed.model,
        cloud_api_key=cloud_api_key,
        enable_analysis=enable_analysis,
    )

    if not result:
        print("❌ 解析失败，请检查链接是否有效。")
        sys.exit(1)

    # 输出结果
    if parsed.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.format_output())


def main():
    args = sys.argv[1:]

    if not args:
        # 无参数 → 交互式输入
        handle_parse(args)
    elif args[0] == "cookie":
        handle_cookie(args[1:])
    else:
        handle_parse(args)


if __name__ == "__main__":
    main()
