"""
Cookie Webhook 服务
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.infra.cookie_store import CookieManager, get_cookie_manager

logger = logging.getLogger(__name__)


def start_webhook_server(port: int = 5555, cookie_manager: CookieManager | None = None):
    """
    启动 Cookie Webhook 接收服务器。

    Chrome Cookie Sniffer 扩展会将捕获到的 Cookie 通过 POST 请求发送到此服务器。
    """
    cookie_manager = cookie_manager or get_cookie_manager()

    class WebhookHandler(BaseHTTPRequestHandler):
        def _send_cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "86400")

        def do_OPTIONS(self):
            self.send_response(200)
            self._send_cors_headers()
            self.end_headers()
            logger.debug("✅ CORS 预检请求已通过")

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
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "status": "ok",
                                "message": f"Cookie 已更新 ({len(cookie)} chars)",
                            }
                        ).encode()
                    )
                    logger.info("✅ 收到 Webhook Cookie 更新 (%s chars)", len(cookie))
                    return

                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "status": "error",
                            "message": "无效的请求数据",
                        }
                    ).encode()
                )

            except Exception as exc:
                logger.error("Webhook 处理错误: %s", exc)
                self.send_response(500)
                self._send_cors_headers()
                self.end_headers()

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            info = cookie_manager.get_cookie_info()
            self.wfile.write(
                json.dumps(
                    {
                        "status": "running",
                        "service": "douyin-parser cookie webhook",
                        "cookie": info,
                    }
                ).encode()
            )

        def log_message(self, format, *args):
            logger.debug("Webhook: %s", args[0])

    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logger.info("🔗 Webhook 服务启动: http://0.0.0.0:%s", port)
    logger.info("   请在 Chrome Cookie Sniffer 扩展中设置 Webhook URL 为:")
    logger.info("   http://<你的电脑IP>:%s", port)
    server.serve_forever()


def start_webhook_background(port: int = 5555, cookie_manager: CookieManager | None = None):
    """后台启动 Webhook 服务器。"""
    thread = threading.Thread(
        target=start_webhook_server,
        args=(port, cookie_manager),
        daemon=True,
    )
    thread.start()
    return thread
