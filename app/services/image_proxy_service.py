"""图片代理相关服务。"""

from typing import Optional, Tuple

import requests


def fetch_proxy_image(image_url: str) -> Optional[Tuple[bytes, str, dict]]:
    """代理下载图片，返回内容、类型和缓存头。"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.douyin.com/",
    }

    try:
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
    except Exception:
        return None

    if response.status_code != 200:
        return None

    return (
        response.content,
        response.headers.get("Content-Type", "image/jpeg"),
        {"Cache-Control": "public, max-age=86400"},
    )
