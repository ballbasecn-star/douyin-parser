"""
兼容层：Cookie 基础设施已迁移到 app.infra。
"""

from app.infra.cookie_store import CookieManager, get_cookie_manager
from app.infra.cookie_webhook import start_webhook_background, start_webhook_server

__all__ = [
    "CookieManager",
    "get_cookie_manager",
    "start_webhook_background",
    "start_webhook_server",
]
