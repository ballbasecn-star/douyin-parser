from __future__ import annotations

"""
抖音 Web 请求基础设施
"""

import logging
import random
import re
import string
from typing import Dict, Optional
from urllib.parse import quote, urlencode

import requests

from app.infra.douyin_signature import ABogus

logger = logging.getLogger(__name__)

POST_DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.212 Safari/537.36"
)

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Referer": "https://www.douyin.com/",
    "User-Agent": USER_AGENT,
}

BASE_PARAMS = {
    "device_platform": "webapp",
    "aid": "6383",
    "channel": "channel_pc_web",
    "pc_client_type": "1",
    "version_code": "290100",
    "version_name": "29.1.0",
    "cookie_enabled": "true",
    "screen_width": "1920",
    "screen_height": "1080",
    "browser_language": "zh-CN",
    "browser_platform": "Win32",
    "browser_name": "Chrome",
    "browser_version": "90.0.4430.212",
    "browser_online": "true",
    "engine_name": "Blink",
    "engine_version": "90.0.4430.212",
    "os_name": "Windows",
    "os_version": "10",
    "cpu_core_num": "12",
    "device_memory": "8",
    "platform": "PC",
    "downlink": "10",
    "effective_type": "4g",
    "round_trip_time": "0",
}

MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
}


def extract_aweme_id(url: str) -> Optional[str]:
    """从 URL 中提取 aweme_id。"""
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/note/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"aweme_id=(\d+)", url)
    if match:
        return match.group(1)
    return None


def resolve_short_url(short_url: str) -> Optional[str]:
    """
    解析短链接重定向，获取 aweme_id。
    """
    try:
        response = requests.get(
            short_url,
            headers=MOBILE_HEADERS,
            allow_redirects=True,
            timeout=10,
        )
        if response.status_code == 200:
            final_url = response.url
            logger.debug("重定向 → %s", final_url)

            if final_url.rstrip("/") in ("https://www.douyin.com", "https://m.douyin.com"):
                logger.warning("链接被重定向到首页，可能已失效")
                return None

            aweme_id = extract_aweme_id(final_url)
            if aweme_id:
                logger.info("获取到 aweme_id: %s", aweme_id)
                return aweme_id

    except Exception as exc:
        logger.error("解析短链接失败: %s", exc)

    return None


def gen_mstoken() -> str:
    """生成随机 msToken。"""
    chars = string.ascii_letters + string.digits + "_-"
    return "".join(random.choice(chars) for _ in range(128))


def build_post_detail_params(aweme_id: str) -> dict:
    """构造作品详情 API 的请求参数。"""
    params = dict(BASE_PARAMS)
    params["aweme_id"] = aweme_id
    params["msToken"] = ""
    return params


def sign_params(params: dict) -> str:
    """使用 a_bogus 签名参数，返回完整 URL。"""
    bogus = ABogus()
    a_bogus = bogus.get_value(params, method="GET")
    return f"{POST_DETAIL_API}?{urlencode(params)}&a_bogus={quote(a_bogus, safe='')}"


def fetch_video_detail(aweme_id: str, cookie: str | None = None) -> Optional[Dict]:
    """请求抖音 API 获取视频详情。"""
    params = build_post_detail_params(aweme_id)
    signed_url = sign_params(params)

    headers = dict(DEFAULT_HEADERS)
    if cookie:
        headers["Cookie"] = cookie

    logger.info("请求抖音 API: aweme_id=%s", aweme_id)
    logger.debug("URL: %s...", signed_url[:100])

    try:
        response = requests.get(signed_url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if data.get("status_code") == 0:
                aweme_detail = data.get("aweme_detail")
                if aweme_detail:
                    logger.info("✅ 抖音 API 返回成功")
                    return aweme_detail
                logger.warning("API 返回无 aweme_detail: %s", list(data.keys()))
            else:
                logger.warning(
                    "API 状态码异常: %s, %s",
                    data.get("status_code"),
                    data.get("status_msg", ""),
                )
        else:
            logger.warning("HTTP 错误: %s", response.status_code)

    except Exception as exc:
        logger.error("请求抖音 API 失败: %s", exc)

    return None
