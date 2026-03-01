"""
Cookie 管理模块

提供以下功能：
1. 本地 Cookie 文件存储和加载
2. Webhook 接收器 - 接收来自 Chrome Cookie Sniffer 扩展的 Cookie 推送
3. CLI 手动设置 Cookie
"""
import json
import logging
import os
import threading
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# 默认 Cookie 存储路径
COOKIE_DIR = os.environ.get("COOKIE_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookie_data"))
COOKIE_FILE = os.path.join(COOKIE_DIR, "douyin_cookie.json")


class CookieManager:
    """Cookie 管理器"""

    def __init__(self, cookie_dir: str = None):
        self.cookie_dir = cookie_dir or COOKIE_DIR
        self.cookie_file = os.path.join(self.cookie_dir, "douyin_cookie.json")
        Path(self.cookie_dir).mkdir(parents=True, exist_ok=True)

    def get_cookie(self) -> Optional[str]:
        """
        获取当前保存的 Cookie

        Returns:
            Cookie 字符串，不存在则返回 None
        """
        if not os.path.exists(self.cookie_file):
            return None

        try:
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            cookie = data.get("cookie", "")
            if cookie:
                timestamp = data.get("timestamp", "")
                logger.debug(f"加载 Cookie (更新于: {timestamp})")
                return cookie
        except Exception as e:
            logger.warning(f"读取 Cookie 失败: {e}")

        return None

    def save_cookie(self, cookie: str, source: str = "manual"):
        """
        保存 Cookie

        Args:
            cookie: Cookie 字符串
            source: 来源 (manual / webhook / browser)
        """
        try:
            data = {
                "cookie": cookie,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "service": "douyin",
            }

            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Cookie 已保存 (来源: {source}, 长度: {len(cookie)})")
        except Exception as e:
            logger.error(f"保存 Cookie 失败: {e}")

    def has_cookie(self) -> bool:
        """检查是否有保存的 Cookie"""
        return self.get_cookie() is not None

    def get_cookie_info(self) -> dict:
        """获取 Cookie 的元信息"""
        if not os.path.exists(self.cookie_file):
            return {"exists": False}

        try:
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "exists": True,
                "source": data.get("source", "unknown"),
                "timestamp": data.get("timestamp", ""),
                "cookie_length": len(data.get("cookie", "")),
            }
        except Exception:
            return {"exists": False}


def start_webhook_server(port: int = 5555, cookie_manager: CookieManager = None):
    """
    启动 Webhook 接收服务器

    Chrome Cookie Sniffer 扩展会将捕获到的 Cookie 通过 POST 请求发送到此服务器。
    设置扩展的 Webhook URL 为: http://<你的IP>:<port>/webhook

    Args:
        port: 服务监听端口 (默认 5555)
        cookie_manager: Cookie 管理器实例
    """
    from http.server import HTTPServer, BaseHTTPRequestHandler

    if cookie_manager is None:
        cookie_manager = CookieManager()

    class WebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                service = data.get("service", "")
                cookie = data.get("cookie", "")

                if service == "douyin" and cookie:
                    cookie_manager.save_cookie(cookie, source="webhook")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "message": f"Cookie 已更新 ({len(cookie)} chars)"
                    }).encode())
                    logger.info(f"✅ 收到 Webhook Cookie 更新 ({len(cookie)} chars)")
                else:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "无效的请求数据"
                    }).encode())

            except Exception as e:
                logger.error(f"Webhook 处理错误: {e}")
                self.send_response(500)
                self.end_headers()

        def do_GET(self):
            """健康检查"""
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            info = cookie_manager.get_cookie_info()
            self.wfile.write(json.dumps({
                "status": "running",
                "service": "douyin-parser cookie webhook",
                "cookie": info,
            }).encode())

        def log_message(self, format, *args):
            """使用 Python logging 而非 stderr"""
            logger.debug(f"Webhook: {args[0]}")

    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logger.info(f"🔗 Webhook 服务启动: http://0.0.0.0:{port}")
    logger.info(f"   请在 Chrome Cookie Sniffer 扩展中设置 Webhook URL 为:")
    logger.info(f"   http://<你的电脑IP>:{port}")
    server.serve_forever()


def start_webhook_background(port: int = 5555, cookie_manager: CookieManager = None):
    """后台启动 Webhook 服务器"""
    t = threading.Thread(
        target=start_webhook_server,
        args=(port, cookie_manager),
        daemon=True,
    )
    t.start()
    return t


# 全局单例
_cookie_manager = None


def get_cookie_manager() -> CookieManager:
    """获取全局 Cookie 管理器"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager()
    return _cookie_manager
