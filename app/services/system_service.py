"""系统级服务。"""

import os
from typing import Dict, List

from douyin.cookie_manager import get_cookie_manager

from app.infra.settings import APP_VERSION


def get_health_payload() -> Dict:
    """返回健康检查载荷。"""
    return {
        "status": "running",
        "version": APP_VERSION,
        "cookie": get_cookie_manager().get_cookie_info(),
    }


def get_cookie_status_payload() -> Dict:
    """返回 Cookie 状态。"""
    return get_cookie_manager().get_cookie_info()


def save_cookie_value(cookie: str) -> None:
    """保存 Cookie。"""
    get_cookie_manager().save_cookie(cookie, source="web")


def save_runtime_keys(data: Dict) -> List[str]:
    """将 API Key 保存到当前进程环境变量。"""
    saved = []
    for key in ("GROQ_API_KEY", "SILICONFLOW_API_KEY"):
        if key in data and data[key]:
            os.environ[key] = data[key]
            saved.append(key)
    return saved
