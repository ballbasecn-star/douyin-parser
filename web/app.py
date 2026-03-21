"""
Douyin Parser - Web 服务

启动方式:
    python -m web.app [--port 8080] [--debug]
"""

import logging

from app import create_app
from douyin.cookie_manager import start_webhook_background

app = create_app()
logger = logging.getLogger(__name__)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Douyin Parser Web 服务")
    parser.add_argument("--port", type=int, default=8080, help="端口 (默认: 8080)")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--webhook-port", type=int, default=5555, help="Cookie Webhook 端口")
    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 后台启动 Cookie Webhook
    start_webhook_background(port=args.webhook_port)
    logger.info(f"🍪 Cookie Webhook 已在后台启动 (端口: {args.webhook_port})")

    # 启动 Web 服务
    print(f"\n🚀 Douyin Parser Web 服务启动")
    print(f"   🌐 http://localhost:{args.port}")
    print(f"   🍪 Cookie Webhook: http://0.0.0.0:{args.webhook_port}")
    print(f"   按 Ctrl+C 停止\n")

    app.run(host="0.0.0.0", port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
