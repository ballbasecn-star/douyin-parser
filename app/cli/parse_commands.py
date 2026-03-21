"""视频解析 CLI 子命令。"""

import argparse
import json
import os

from app.cli.common import setup_logging
from app.services.video_parse_service import parse_video


def build_parse_parser() -> argparse.ArgumentParser:
    """构建解析命令参数。"""
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
    parser.add_argument(
        "--cloud-provider",
        default="groq",
        choices=["groq", "siliconflow"],
        help="云端服务商 (默认: groq)",
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="本地转录模型大小 (默认: large-v3)",
    )
    parser.add_argument("--api-url", help="自定义远程 API 地址")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志输出")
    return parser


def handle_parse_command(args: list[str]) -> int:
    """处理视频解析命令。"""
    parser = build_parse_parser()
    parsed = parser.parse_args(args)
    setup_logging(parsed.verbose)

    share_text = parsed.text
    if not share_text:
        print("📋 请粘贴抖音分享文本（输入后按回车）:")
        print("-" * 40)
        try:
            share_text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n取消。")
            return 0

    if not share_text:
        print("❌ 未输入任何内容")
        return 1

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

    if parsed.cloud:
        if parsed.cloud_provider == "siliconflow":
            cloud_api_key = os.environ.get("SILICONFLOW_API_KEY")
        else:
            cloud_api_key = os.environ.get("GROQ_API_KEY")
    else:
        cloud_api_key = None

    result = parse_video(
        share_text=share_text,
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
        return 1

    if parsed.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.format_output())
    return 0
