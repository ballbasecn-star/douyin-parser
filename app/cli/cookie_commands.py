"""Cookie 相关 CLI 子命令。"""

from app.cli.common import setup_logging
from app.infra.cookie_store import get_cookie_manager
from app.infra.cookie_webhook import start_webhook_server


def handle_cookie_command(args: list[str]) -> int:
    """处理 cookie 子命令。"""
    cookie_manager = get_cookie_manager()
    action = args[0] if args else "show"

    if action == "set":
        if len(args) < 2:
            print("❌ 请提供 Cookie 值")
            print('用法: python main.py cookie set "你的Cookie字符串"')
            return 1
        cookie_manager.save_cookie(args[1], source="manual")
        print("✅ Cookie 已保存")
        return 0

    if action == "show":
        info = cookie_manager.get_cookie_info()
        if info.get("exists"):
            print("🍪 Cookie 状态:")
            print(f"   来源: {info['source']}")
            print(f"   更新时间: {info['timestamp']}")
            print(f"   长度: {info['cookie_length']} 字符")
            cookie = cookie_manager.get_cookie()
            if cookie:
                print(f"   预览: {cookie[:100]}...")
        else:
            print("⚠️  未设置 Cookie")
            print("💡 设置方式:")
            print('   1. 手动: python main.py cookie set "Cookie内容"')
            print("   2. 自动: python main.py cookie webhook")
        return 0

    if action == "webhook":
        port = 5555
        for index, arg in enumerate(args):
            if arg == "--port" and index + 1 < len(args):
                port = int(args[index + 1])
        setup_logging(True)
        print("🔗 启动 Cookie Webhook 接收服务...")
        print(f"   监听地址: http://0.0.0.0:{port}")
        print("   请在 Chrome Cookie Sniffer 扩展中设置 Webhook URL")
        print("   按 Ctrl+C 停止")
        print()
        try:
            start_webhook_server(port=port, cookie_manager=cookie_manager)
        except KeyboardInterrupt:
            print("\n已停止。")
        return 0

    print(f"未知的 cookie 命令: {action}")
    print("可用: set / show / webhook")
    return 1
